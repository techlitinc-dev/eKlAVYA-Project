"""
Mind-Map API Tests

Covers map CRUD with optimistic concurrency, root/child node invariants, edge
cycle rejection, deterministic generation with revision snapshots, branch
regeneration preserving locked nodes, JSON export, authorization hiding, and
idempotent creation.
"""

import json
from pathlib import Path

from core.config import get_settings
from tests.conftest import (
    ADMIN_LOCAL,
    STUDENT_AARAV,
    STUDENT_MEERA,
    SYLLABUS_ID,
    auth_headers,
)

AARAV = auth_headers(STUDENT_AARAV, "student", "Aarav Sharma")
MEERA = auth_headers(STUDENT_MEERA, "student", "Meera Iyer")
ADMIN = auth_headers(ADMIN_LOCAL, "admin", "Local Admin")

SEEDED_ROTATIONAL = "map_seed_rotational"
SEEDED_BONDING = "map_seed_bonding"
ROOT_ROT = "node_rot_root"
CHILD_ROT_TORQUE = "node_rot_torque"
CHILD_ROT_INERTIA = "node_rot_inertia"
EDGE_ROT_1 = "edge_rot_1"
NOTE_AARAV = "note_seed_1"
NOTE_MEERA = "note_seed_meera"

ROTATIONAL_TOPICS = {
    "Moment of Inertia",
    "Torque and Angular Momentum",
    "Rolling Motion",
}

TEMPLATE_CHILDREN = ["Definition", "Key Formulas", "Common Mistakes", "Practice Problems"]


def _children_of(map_body, parent_id):
    return [n for n in map_body["nodes"] if n["parent_id"] == parent_id]


def _get_map(client, map_id, headers=AARAV):
    response = client.get(f"/api/v1/mindmaps/{map_id}", headers=headers)
    assert response.status_code == 200
    return response.json()


# ---------------------------------------------------------------------------
# OpenAPI and authentication
# ---------------------------------------------------------------------------


def test_openapi_includes_mindmap_routes(client):
    spec = client.get("/api/openapi.json")
    assert spec.status_code == 200
    paths = spec.json()["paths"]
    for path in (
        "/api/v1/mindmaps",
        "/api/v1/mindmaps/{map_id}",
        "/api/v1/mindmaps/{map_id}/nodes",
        "/api/v1/mindmaps/{map_id}/nodes/{node_id}",
        "/api/v1/mindmaps/{map_id}/edges",
        "/api/v1/mindmaps/{map_id}/edges/{edge_id}",
        "/api/v1/mindmaps/{map_id}/generate",
        "/api/v1/mindmaps/{map_id}/regenerate-branch",
        "/api/v1/mindmaps/{map_id}/revisions",
        "/api/v1/mindmaps/{map_id}/export",
    ):
        assert path in paths


def test_missing_authentication_rejected(client):
    response = client.get("/api/v1/mindmaps")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


# ---------------------------------------------------------------------------
# Listing and authorization
# ---------------------------------------------------------------------------


def test_list_maps_includes_seeded_map(client):
    response = client.get("/api/v1/mindmaps", headers=AARAV)
    assert response.status_code == 200
    body = response.json()
    assert body["next_cursor"] is None
    maps = {item["id"]: item for item in body["items"]}
    assert SEEDED_ROTATIONAL in maps
    assert SEEDED_BONDING in maps
    # Counts are included without embedding full node/edge lists.
    assert maps[SEEDED_ROTATIONAL]["node_count"] == 3
    assert maps[SEEDED_ROTATIONAL]["edge_count"] == 2
    assert maps[SEEDED_ROTATIONAL]["nodes"] == []


def test_admin_sees_all_maps(client):
    response = client.get("/api/v1/mindmaps", headers=ADMIN)
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert {SEEDED_ROTATIONAL, SEEDED_BONDING} <= ids


def test_cross_student_access_hidden(client):
    response = client.get(f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}", headers=MEERA)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"

    patch = client.patch(
        f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}",
        json={"version": 1, "title": "Hijack"},
        headers=MEERA,
    )
    assert patch.status_code == 404

    delete = client.delete(f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}", headers=MEERA)
    assert delete.status_code == 404


def test_get_map_embeds_nodes_and_edges(client):
    body = _get_map(client, SEEDED_ROTATIONAL)
    assert body["title"] == "Rotational Motion"
    assert body["root_node_id"] == ROOT_ROT
    assert body["syllabus_id"] == SYLLABUS_ID
    assert body["chapter_id"] == "ch_rotational_motion"
    assert body["node_count"] == 3
    assert body["edge_count"] == 2
    assert len(body["nodes"]) == 3
    edge_pairs = {(e["source_node_id"], e["target_node_id"]) for e in body["edges"]}
    assert (ROOT_ROT, CHILD_ROT_TORQUE) in edge_pairs
    assert (ROOT_ROT, CHILD_ROT_INERTIA) in edge_pairs


# ---------------------------------------------------------------------------
# Map create / update / delete
# ---------------------------------------------------------------------------


def test_create_map_creates_exactly_one_root(client):
    response = client.post(
        "/api/v1/mindmaps",
        json={"title": "Thermodynamics", "chapter_id": "ch_chem_thermodynamics"},
        headers=AARAV,
    )
    assert response.status_code == 201
    created = response.json()
    assert created["root_node_id"] is not None
    assert created["version"] == 1

    fetched = _get_map(client, created["id"])
    assert len(fetched["nodes"]) == 1
    root = fetched["nodes"][0]
    assert root["id"] == fetched["root_node_id"]
    assert root["label"] == "Thermodynamics"  # label defaults to title
    assert root["parent_id"] is None
    assert fetched["edges"] == []


def test_create_map_with_root_label_and_invalid_context(client):
    created = client.post(
        "/api/v1/mindmaps",
        json={"title": "Work Energy", "root_label": "WEP Root"},
        headers=AARAV,
    )
    assert created.status_code == 201
    fetched = _get_map(client, created.json()["id"])
    assert fetched["nodes"][0]["label"] == "WEP Root"

    bad = client.post(
        "/api/v1/mindmaps",
        json={"title": "Bad", "topic_id": "top_missing_topic"},
        headers=AARAV,
    )
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "SYLLABUS_CONTEXT_INVALID"


def test_create_map_idempotency_key(client):
    body = {"title": "Idempotent Map"}
    key = "mindmap-idem-1"
    first = client.post("/api/v1/mindmaps", json=body, headers={**AARAV, "Idempotency-Key": key})
    assert first.status_code == 201
    second = client.post("/api/v1/mindmaps", json=body, headers={**AARAV, "Idempotency-Key": key})
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]

    listing = client.get("/api/v1/mindmaps", headers=AARAV).json()["items"]
    assert sum(1 for m in listing if m["title"] == "Idempotent Map") == 1

    conflict = client.post(
        "/api/v1/mindmaps",
        json={"title": "Different"},
        headers={**AARAV, "Idempotency-Key": key},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_update_map_title_and_stale_version_conflict(client):
    created = client.post("/api/v1/mindmaps", json={"title": "Old Title"}, headers=AARAV)
    map_id = created.json()["id"]

    ok = client.patch(
        f"/api/v1/mindmaps/{map_id}",
        json={"version": 1, "title": "New Title"},
        headers=AARAV,
    )
    assert ok.status_code == 200
    assert ok.json()["title"] == "New Title"
    assert ok.json()["version"] == 2

    stale = client.patch(
        f"/api/v1/mindmaps/{map_id}",
        json={"version": 1, "title": "Stale"},
        headers=AARAV,
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "RESOURCE_CONFLICT"


def test_update_map_validates_syllabus_context(client):
    created = client.post("/api/v1/mindmaps", json={"title": "Context Map"}, headers=AARAV)
    map_id = created.json()["id"]
    bad = client.patch(
        f"/api/v1/mindmaps/{map_id}",
        json={"version": 1, "chapter_id": "ch_missing"},
        headers=AARAV,
    )
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "SYLLABUS_CONTEXT_INVALID"


def test_delete_map_cascades(client):
    created = client.post("/api/v1/mindmaps", json={"title": "Doomed"}, headers=AARAV)
    map_id = created.json()["id"]
    client.post(f"/api/v1/mindmaps/{map_id}/nodes", json={"label": "Kid", "parent_id": created.json()["root_node_id"]}, headers=AARAV)
    client.post(f"/api/v1/mindmaps/{map_id}/generate", headers=AARAV)

    deleted = client.delete(f"/api/v1/mindmaps/{map_id}", headers=AARAV)
    assert deleted.status_code == 204
    assert deleted.content == b""

    gone = client.get(f"/api/v1/mindmaps/{map_id}", headers=AARAV)
    assert gone.status_code == 404


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def test_add_child_node_auto_creates_edge(client):
    created = client.post("/api/v1/mindmaps", json={"title": "Parenting"}, headers=AARAV)
    map_id = created.json()["id"]
    root_id = created.json()["root_node_id"]

    child = client.post(
        f"/api/v1/mindmaps/{map_id}/nodes",
        json={"label": "Child", "parent_id": root_id, "position": {"x": 1.0, "y": 2.0}},
        headers=AARAV,
    )
    assert child.status_code == 201
    assert child.json()["parent_id"] == root_id
    assert child.json()["position"] == {"x": 1.0, "y": 2.0}

    fetched = _get_map(client, map_id)
    assert fetched["node_count"] == 2
    assert fetched["edge_count"] == 1
    edge = fetched["edges"][0]
    assert edge["source_node_id"] == root_id
    assert edge["target_node_id"] == child.json()["id"]


def test_add_node_parent_from_another_map_404(client):
    created = client.post("/api/v1/mindmaps", json={"title": "Lonely"}, headers=AARAV)
    map_id = created.json()["id"]
    response = client.post(
        f"/api/v1/mindmaps/{map_id}/nodes",
        json={"label": "Stray", "parent_id": ROOT_ROT},  # belongs to seeded map
        headers=AARAV,
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_add_node_validates_note_owner(client):
    created = client.post("/api/v1/mindmaps", json={"title": "Notes"}, headers=AARAV)
    map_id = created.json()["id"]

    foreign = client.post(
        f"/api/v1/mindmaps/{map_id}/nodes",
        json={"label": "Linked", "parent_id": created.json()["root_node_id"], "note_id": NOTE_MEERA},
        headers=AARAV,
    )
    assert foreign.status_code == 404

    valid = client.post(
        f"/api/v1/mindmaps/{map_id}/nodes",
        json={"label": "Linked", "parent_id": created.json()["root_node_id"], "note_id": NOTE_AARAV},
        headers=AARAV,
    )
    assert valid.status_code == 201
    assert valid.json()["note_id"] == NOTE_AARAV


def test_first_node_without_parent_becomes_root(client, fresh_repository):
    from models.mindmaps import MindMap

    fresh_repository.put(MindMap(id="map_orphan", owner_id=STUDENT_AARAV, title="Orphan"))

    first = client.post("/api/v1/mindmaps/map_orphan/nodes", json={"label": "Found Root"}, headers=AARAV)
    assert first.status_code == 201
    fetched = _get_map(client, "map_orphan")
    assert fetched["root_node_id"] == first.json()["id"]

    # The map now has a root, so a parentless node is rejected.
    second = client.post("/api/v1/mindmaps/map_orphan/nodes", json={"label": "No Parent"}, headers=AARAV)
    assert second.status_code == 422


def test_update_node_toggles_manual_lock(client):
    updated = client.patch(
        f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}/nodes/{CHILD_ROT_INERTIA}",
        json={"manually_locked": True},
        headers=AARAV,
    )
    assert updated.status_code == 200
    assert updated.json()["manually_locked"] is True

    cleared = client.patch(
        f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}/nodes/{CHILD_ROT_INERTIA}",
        json={"manually_locked": False},
        headers=AARAV,
    )
    assert cleared.status_code == 200
    assert cleared.json()["manually_locked"] is False


def test_update_node_from_another_map_404(client):
    created = client.post("/api/v1/mindmaps", json={"title": "Empty"}, headers=AARAV)
    map_id = created.json()["id"]
    response = client.patch(
        f"/api/v1/mindmaps/{map_id}/nodes/{CHILD_ROT_TORQUE}",
        json={"label": "Sneaky"},
        headers=AARAV,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Root protection and cascade deletion
# ---------------------------------------------------------------------------


def test_delete_root_node_rejected(client):
    response = client.delete(
        f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}/nodes/{ROOT_ROT}", headers=AARAV
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATE_TRANSITION"


def test_child_deletion_cleans_descendants_and_edges(client):
    created = client.post("/api/v1/mindmaps", json={"title": "Cascade"}, headers=AARAV)
    map_id = created.json()["id"]
    root_id = created.json()["root_node_id"]

    middle = client.post(
        f"/api/v1/mindmaps/{map_id}/nodes", json={"label": "Middle", "parent_id": root_id}, headers=AARAV
    ).json()
    leaf = client.post(
        f"/api/v1/mindmaps/{map_id}/nodes", json={"label": "Leaf", "parent_id": middle["id"]}, headers=AARAV
    ).json()
    other = client.post(
        f"/api/v1/mindmaps/{map_id}/nodes", json={"label": "Other", "parent_id": root_id}, headers=AARAV
    ).json()

    fetched = _get_map(client, map_id)
    assert fetched["node_count"] == 4
    assert fetched["edge_count"] == 3

    deleted = client.delete(
        f"/api/v1/mindmaps/{map_id}/nodes/{middle['id']}", headers=AARAV
    )
    assert deleted.status_code == 204

    fetched = _get_map(client, map_id)
    remaining = {n["id"] for n in fetched["nodes"]}
    assert middle["id"] not in remaining
    assert leaf["id"] not in remaining  # descendant removed
    assert root_id in remaining
    assert other["id"] in remaining
    assert fetched["node_count"] == 2
    # Edges touching removed nodes are gone; only root->other remains.
    assert fetched["edge_count"] == 1
    assert fetched["edges"][0]["target_node_id"] == other["id"]


# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------


def test_edge_cycle_rejected(client):
    response = client.post(
        f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}/edges",
        json={"source_node_id": CHILD_ROT_TORQUE, "target_node_id": ROOT_ROT},
        headers=AARAV,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] in (
        "INVALID_STATE_TRANSITION",
        "RESOURCE_CONFLICT",
        "VALIDATION_ERROR",
    )


def test_edge_duplicate_and_self_loop_rejected(client):
    duplicate = client.post(
        f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}/edges",
        json={"source_node_id": ROOT_ROT, "target_node_id": CHILD_ROT_TORQUE},
        headers=AARAV,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "RESOURCE_CONFLICT"

    self_loop = client.post(
        f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}/edges",
        json={"source_node_id": ROOT_ROT, "target_node_id": ROOT_ROT},
        headers=AARAV,
    )
    assert self_loop.status_code == 422
    assert self_loop.json()["error"]["code"] == "VALIDATION_ERROR"


def test_edge_cross_map_reference_404(client):
    created = client.post("/api/v1/mindmaps", json={"title": "Edges"}, headers=AARAV)
    map_id = created.json()["id"]
    root_id = created.json()["root_node_id"]
    response = client.post(
        f"/api/v1/mindmaps/{map_id}/edges",
        json={"source_node_id": root_id, "target_node_id": ROOT_ROT},
        headers=AARAV,
    )
    assert response.status_code == 404


def test_delete_edge(client):
    deleted = client.delete(f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}/edges/{EDGE_ROT_1}", headers=AARAV)
    assert deleted.status_code == 204
    fetched = _get_map(client, SEEDED_ROTATIONAL)
    assert fetched["edge_count"] == 1
    assert all(e["id"] != EDGE_ROT_1 for e in fetched["edges"])


# ---------------------------------------------------------------------------
# Deterministic generation
# ---------------------------------------------------------------------------


def test_generate_saves_revision_and_bumps_version(client):
    before = _get_map(client, SEEDED_BONDING)
    response = client.post(f"/api/v1/mindmaps/{SEEDED_BONDING}/generate", headers=AARAV)
    assert response.status_code == 200
    body = response.json()
    assert body["revision_id"]
    assert body["map"]["version"] == before["version"] + 1

    revisions = client.get(f"/api/v1/mindmaps/{SEEDED_BONDING}/revisions", headers=AARAV)
    assert revisions.status_code == 200
    items = revisions.json()["items"]
    assert len(items) == 1
    assert items[0]["version"] == before["version"]
    assert items[0]["reason"] == "generate"
    assert items[0]["node_count"] == before["node_count"]

    # A second generate grows the revision history and bumps the version again.
    again = client.post(f"/api/v1/mindmaps/{SEEDED_BONDING}/generate", headers=AARAV)
    assert again.status_code == 200
    assert again.json()["map"]["version"] == before["version"] + 2
    revisions = client.get(f"/api/v1/mindmaps/{SEEDED_BONDING}/revisions", headers=AARAV).json()["items"]
    assert len(revisions) == 2
    assert revisions[0]["version"] > revisions[1]["version"]  # version descending


def test_generate_uses_chapter_topics_for_seeded_map(client):
    response = client.post(f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}/generate", headers=AARAV)
    assert response.status_code == 200
    map_body = response.json()["map"]
    assert map_body["root_node_id"] == ROOT_ROT

    child_labels = {n["label"] for n in _children_of(map_body, ROOT_ROT)}
    assert child_labels == ROTATIONAL_TOPICS
    # Freshly generated children are attached by fresh edges under the root.
    root_edges = [e for e in map_body["edges"] if e["source_node_id"] == ROOT_ROT]
    assert len(root_edges) == 3


def test_generate_uses_template_without_chapter_context(client):
    created = client.post("/api/v1/mindmaps", json={"title": "No Context"}, headers=AARAV)
    map_id = created.json()["id"]
    response = client.post(f"/api/v1/mindmaps/{map_id}/generate", headers=AARAV)
    assert response.status_code == 200
    map_body = response.json()["map"]
    child_labels = [n["label"] for n in _children_of(map_body, map_body["root_node_id"])]
    assert child_labels == TEMPLATE_CHILDREN


def test_generate_preserves_locked_subtrees(client):
    locked = client.patch(
        f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}/nodes/{CHILD_ROT_TORQUE}",
        json={"manually_locked": True},
        headers=AARAV,
    ).json()
    response = client.post(f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}/generate", headers=AARAV)
    assert response.status_code == 200
    map_body = response.json()["map"]

    preserved = next(n for n in map_body["nodes"] if n["id"] == CHILD_ROT_TORQUE)
    assert preserved["label"] == locked["label"]
    assert preserved["manually_locked"] is True
    child_labels = {n["label"] for n in _children_of(map_body, ROOT_ROT)}
    assert "Torque" in child_labels  # locked node kept
    assert ROTATIONAL_TOPICS <= child_labels  # topic children still generated
    assert len(child_labels) == 4  # no duplicate "Torque and Angular Momentum"
    # Kept root->locked edge plus three fresh topic edges.
    root_edges = [e for e in map_body["edges"] if e["source_node_id"] == ROOT_ROT]
    assert len(root_edges) == 4


# ---------------------------------------------------------------------------
# Branch regeneration
# ---------------------------------------------------------------------------


def test_regenerate_branch_rejects_root(client):
    response = client.post(
        f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}/regenerate-branch",
        json={"node_id": ROOT_ROT},
        headers=AARAV,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_regenerate_branch_preserves_locked_nodes(client):
    # Build: root -> torque -> {locked "Angular Momentum" -> grandchild, unlocked "Extra"}
    created = client.post(
        "/api/v1/mindmaps",
        json={"title": "Branchy", "chapter_id": "ch_rotational_motion"},
        headers=AARAV,
    )
    map_id = created.json()["id"]
    root_id = created.json()["root_node_id"]
    branch_root = client.post(
        f"/api/v1/mindmaps/{map_id}/nodes", json={"label": "Torque Branch", "parent_id": root_id}, headers=AARAV
    ).json()
    locked_node = client.post(
        f"/api/v1/mindmaps/{map_id}/nodes",
        json={"label": "Angular Momentum", "parent_id": branch_root["id"]},
        headers=AARAV,
    ).json()
    client.post(
        f"/api/v1/mindmaps/{map_id}/nodes",
        json={"label": "Kept Grandchild", "parent_id": locked_node["id"]},
        headers=AARAV,
    )
    client.post(
        f"/api/v1/mindmaps/{map_id}/nodes",
        json={"label": "Extra", "parent_id": branch_root["id"]},
        headers=AARAV,
    )
    client.patch(
        f"/api/v1/mindmaps/{map_id}/nodes/{locked_node['id']}",
        json={"manually_locked": True},
        headers=AARAV,
    )

    response = client.post(
        f"/api/v1/mindmaps/{map_id}/regenerate-branch",
        json={"node_id": branch_root["id"]},
        headers=AARAV,
    )
    assert response.status_code == 200
    map_body = response.json()["map"]
    assert map_body["version"] == 2

    nodes = {n["id"]: n for n in map_body["nodes"]}
    labels = {n["label"] for n in map_body["nodes"]}
    # Locked node and its subtree survive untouched.
    assert nodes[locked_node["id"]]["manually_locked"] is True
    assert "Angular Momentum" in labels
    assert "Kept Grandchild" in labels
    # Unlocked sibling replaced by deterministic chapter topics.
    assert "Extra" not in labels
    child_labels = {n["label"] for n in _children_of(map_body, branch_root["id"])}
    assert "Angular Momentum" in child_labels
    assert ROTATIONAL_TOPICS <= child_labels

    revisions = client.get(f"/api/v1/mindmaps/{map_id}/revisions", headers=AARAV).json()["items"]
    assert len(revisions) == 1
    assert revisions[0]["reason"] == "regenerate-branch"


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def test_export_returns_valid_json_and_persists_file(client):
    response = client.post(f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}/export", headers=AARAV)
    assert response.status_code == 200
    body = response.json()  # response itself is parseable structured JSON

    assert body["format"] == "json"
    assert body["title"] == "Rotational Motion"
    assert body["version"] == 1
    assert body["root_node_id"] == ROOT_ROT
    assert len(body["nodes"]) == 3
    assert len(body["edges"]) == 2
    assert body["exported_at"]

    storage_name = body["storage_name"]
    assert storage_name == f"mindmap_{SEEDED_ROTATIONAL}_v1.json"
    assert not Path(storage_name).is_absolute()

    target = Path(get_settings().local_media_dir) / storage_name
    assert target.exists()
    on_disk = json.loads(target.read_text(encoding="utf-8"))
    assert on_disk["title"] == "Rotational Motion"
    assert {n["id"] for n in on_disk["nodes"]} == {ROOT_ROT, CHILD_ROT_TORQUE, CHILD_ROT_INERTIA}


def test_export_rejects_unknown_format(client):
    response = client.post(
        f"/api/v1/mindmaps/{SEEDED_ROTATIONAL}/export",
        json={"format": "pdf"},
        headers=AARAV,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
