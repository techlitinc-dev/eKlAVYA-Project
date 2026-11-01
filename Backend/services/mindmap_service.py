"""
Mind-Map Service

Business logic for mind maps: maps with exactly one root node, tree-structured
child nodes, edges, deterministic mock generation with revision snapshots, and
local JSON export.

Generation is deterministic (no AI calls): children are derived from the
chapter's topic names when a chapter context exists, otherwise from a fixed
template. Nodes with ``manually_locked=True`` and their subtrees are always
preserved during regeneration.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from core.access import assert_owner_access, is_admin
from core.config import Settings
from core.errors import (
    InvalidStateTransition,
    NotFound,
    ResourceConflict,
    ValidationFailed,
)
from core.security import Principal
from core.time import utcnow
from models.common import SyllabusContext
from models.mindmaps import (
    BranchRegenerateIn,
    EdgeCreate,
    EdgeOut,
    GenerateOut,
    MapCreate,
    MapEdge,
    MapNode,
    MapOut,
    MapRevision,
    MapUpdate,
    MindMap,
    NodeCreate,
    NodeUpdate,
    NodeOut,
    RevisionOut,
)
from models.notes import Note
from models.syllabus import SyllabusProfile, Topic
from repositories.base import Repository
from services import syllabus_core_service as syllabus_service
from services.audit_service import record_audit

logger = logging.getLogger(__name__)

# Deterministic fallback children for maps without a chapter context.
TEMPLATE_CHILDREN = ["Definition", "Key Formulas", "Common Mistakes", "Practice Problems"]

ALLOWED_UPDATE_FIELDS = ("title", "syllabus_id", "subject_id", "chapter_id", "topic_id")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _map_nodes(repo: Repository, map_id: str) -> List[MapNode]:
    return repo.find(MapNode, map_id=map_id)


def _map_edges(repo: Repository, map_id: str) -> List[MapEdge]:
    return repo.find(MapEdge, map_id=map_id)


def _node_out(node: MapNode) -> NodeOut:
    return NodeOut(**node.model_dump())


def _edge_out(edge: MapEdge) -> EdgeOut:
    return EdgeOut(**edge.model_dump())


def _build_map_out(repo: Repository, map_: MindMap, include_children: bool = True) -> MapOut:
    nodes = sorted(_map_nodes(repo, map_.id), key=lambda n: (n.created_at, n.id))
    edges = sorted(_map_edges(repo, map_.id), key=lambda e: (e.created_at, e.id))
    children_nodes: List[NodeOut] = []
    children_edges: List[EdgeOut] = []
    if include_children:
        children_nodes = [_node_out(n) for n in nodes]
        children_edges = [_edge_out(e) for e in edges]
    return MapOut(
        **map_.model_dump(),
        node_count=len(nodes),
        edge_count=len(edges),
        nodes=children_nodes,
        edges=children_edges,
    )


def _revision_out(revision: MapRevision) -> RevisionOut:
    return RevisionOut(
        **revision.model_dump(exclude={"nodes", "edges"}),
        node_count=len(revision.nodes),
        edge_count=len(revision.edges),
    )


def _get_owned_map(repo: Repository, principal: Principal, map_id: str) -> MindMap:
    map_ = repo.get(MindMap, map_id)
    if map_ is None:
        raise NotFound("The requested mind map was not found.")
    assert_owner_access(principal, map_.owner_id)
    return map_


def _get_map_node(repo: Repository, map_id: str, node_id: str) -> MapNode:
    node = repo.get(MapNode, node_id)
    if node is None or node.map_id != map_id:
        raise NotFound("The requested node was not found in this mind map.")
    return node


def _get_map_edge(repo: Repository, map_id: str, edge_id: str) -> MapEdge:
    edge = repo.get(MapEdge, edge_id)
    if edge is None or edge.map_id != map_id:
        raise NotFound("The requested edge was not found in this mind map.")
    return edge


def _children_index(nodes: List[MapNode]) -> Dict[Optional[str], List[MapNode]]:
    index: Dict[Optional[str], List[MapNode]] = {}
    for node in nodes:
        index.setdefault(node.parent_id, []).append(node)
    return index


def _descendants(nodes_by_id: Dict[str, MapNode], node_id: str) -> Set[str]:
    """All transitive descendant node ids (excluding ``node_id`` itself)."""
    children = _children_index(list(nodes_by_id.values()))
    found: Set[str] = set()
    stack = list(children.get(node_id, []))
    while stack:
        current = stack.pop()
        if current.id in found:
            continue
        found.add(current.id)
        stack.extend(children.get(current.id, []))
    return found


def _subtree_ids(nodes_by_id: Dict[str, MapNode], node_id: str) -> Set[str]:
    return _descendants(nodes_by_id, node_id) | {node_id}


def _validate_note_reference(repo: Repository, owner_id: str, note_id: str) -> None:
    note = repo.get(Note, note_id)
    if note is None or note.owner_id != owner_id:
        raise NotFound("The referenced note was not found.")


def _owner_profile(repo: Repository, owner_id: str) -> SyllabusProfile:
    profile = repo.first(SyllabusProfile, student_id=owner_id)
    if profile is None:
        raise NotFound("No syllabus profile found for this student.")
    return profile


def _validate_context_for_owner(
    repo: Repository, owner_id: str, context: SyllabusContext
) -> None:
    if context.is_empty():
        return
    profile = _owner_profile(repo, owner_id)
    syllabus_service.validate_syllabus_context(repo, context, profile)


def _chapter_child_labels(repo: Repository, map_: MindMap) -> List[str]:
    """Deterministic child labels: chapter topic names, else fixed template."""
    if map_.chapter_id:
        topics = repo.find(Topic, chapter_id=map_.chapter_id)
        if topics:
            topics.sort(key=lambda t: (t.name, t.id))
            return [topic.name for topic in topics]
    return list(TEMPLATE_CHILDREN)


def _save_revision(
    repo: Repository, principal: Principal, map_: MindMap, reason: str
) -> MapRevision:
    nodes = [n.model_dump(mode="json") for n in _map_nodes(repo, map_.id)]
    edges = [e.model_dump(mode="json") for e in _map_edges(repo, map_.id)]
    revision = MapRevision.new(
        "rev",
        map_id=map_.id,
        version=map_.version,
        nodes=nodes,
        edges=edges,
        created_by=principal.user_id,
        reason=reason,
    )
    repo.put(revision)
    return revision


def _create_child_nodes(
    repo: Repository,
    map_: MindMap,
    parent_id: str,
    labels: List[str],
    existing_children: List[MapNode],
) -> Tuple[List[MapNode], List[MapEdge]]:
    """Create deterministic child nodes (and parent edges), skipping labels
    that already exist among ``existing_children``."""
    existing_labels = {child.label for child in existing_children}
    created_nodes: List[MapNode] = []
    created_edges: List[MapEdge] = []
    for label in labels:
        if label in existing_labels:
            continue
        node = MapNode.new(
            "node", map_id=map_.id, label=label, parent_id=parent_id
        )
        repo.put(node)
        edge = MapEdge.new(
            "edge", map_id=map_.id, source_node_id=parent_id, target_node_id=node.id
        )
        repo.put(edge)
        created_nodes.append(node)
        created_edges.append(edge)
        existing_labels.add(label)
    return created_nodes, created_edges


def _delete_nodes_and_touching_edges(repo: Repository, map_id: str, remove_ids: Set[str]) -> None:
    for edge in _map_edges(repo, map_id):
        if edge.source_node_id in remove_ids or edge.target_node_id in remove_ids:
            repo.delete(MapEdge, edge.id)
    for node_id in remove_ids:
        repo.delete(MapNode, node_id)


def _remove_orphans_to_root(repo: Repository, map_: MindMap, keep_ids: Set[str]) -> None:
    """Re-attach kept non-root nodes whose parent was removed back to the root."""
    nodes_by_id = {n.id: n for n in _map_nodes(repo, map_.id)}
    for node in nodes_by_id.values():
        if node.id == map_.root_node_id:
            continue
        if node.parent_id is not None and node.parent_id not in nodes_by_id:
            node.parent_id = map_.root_node_id
            node.touch()
            repo.put(node)
            repo.put(
                MapEdge.new(
                    "edge",
                    map_id=map_.id,
                    source_node_id=map_.root_node_id,
                    target_node_id=node.id,
                )
            )


# ---------------------------------------------------------------------------
# Map CRUD
# ---------------------------------------------------------------------------

def list_maps(repo: Repository, principal: Principal) -> List[MapOut]:
    if is_admin(principal):
        maps = repo.all(MindMap)
    else:
        maps = repo.find(MindMap, owner_id=principal.user_id)
    maps.sort(key=lambda m: (m.title, m.id))
    return [_build_map_out(repo, map_, include_children=False) for map_ in maps]


def create_map(repo: Repository, principal: Principal, data: MapCreate) -> MapOut:
    title = data.title.strip()
    if not title:
        raise ValidationFailed(details={"field": "title"})
    context = SyllabusContext(
        syllabus_id=data.syllabus_id,
        subject_id=data.subject_id,
        chapter_id=data.chapter_id,
        topic_id=data.topic_id,
    )
    _validate_context_for_owner(repo, principal.user_id, context)

    map_ = MindMap.new(
        "map",
        owner_id=principal.user_id,
        title=title,
        syllabus_id=data.syllabus_id,
        subject_id=data.subject_id,
        chapter_id=data.chapter_id,
        topic_id=data.topic_id,
        source=data.source or "manual",
    )
    root = MapNode.new(
        "node",
        map_id=map_.id,
        label=(data.root_label or "").strip() or title,
        parent_id=None,
    )
    map_.root_node_id = root.id
    repo.put(root)
    repo.put(map_)
    record_audit(
        repo,
        principal.user_id,
        "mindmap.create",
        "mindmap",
        map_.id,
        details={"title": map_.title, "root_node_id": root.id},
    )
    return _build_map_out(repo, map_)


def get_map(repo: Repository, principal: Principal, map_id: str) -> MapOut:
    map_ = _get_owned_map(repo, principal, map_id)
    return _build_map_out(repo, map_)


def update_map(repo: Repository, principal: Principal, map_id: str, data: MapUpdate) -> MapOut:
    map_ = _get_owned_map(repo, principal, map_id)

    if data.version != map_.version:
        raise ResourceConflict(
            details={"expected_version": data.version, "current_version": map_.version},
            message="The mind map was modified by another request.",
        )

    updates = data.model_dump(exclude={"version"}, exclude_none=True)
    if "title" in updates:
        title = updates["title"].strip()
        if not title:
            raise ValidationFailed(details={"field": "title"})
        map_.title = title

    syllabus_updates = {k: v for k, v in updates.items() if k in ALLOWED_UPDATE_FIELDS[1:]}
    if syllabus_updates:
        merged = SyllabusContext(
            syllabus_id=syllabus_updates.get("syllabus_id", map_.syllabus_id),
            subject_id=syllabus_updates.get("subject_id", map_.subject_id),
            chapter_id=syllabus_updates.get("chapter_id", map_.chapter_id),
            topic_id=syllabus_updates.get("topic_id", map_.topic_id),
        )
        _validate_context_for_owner(repo, map_.owner_id, merged)
        for field_name, value in syllabus_updates.items():
            setattr(map_, field_name, value)

    map_.version += 1
    map_.touch()
    repo.put(map_)
    record_audit(
        repo,
        principal.user_id,
        "mindmap.update",
        "mindmap",
        map_.id,
        details={"version": map_.version},
    )
    return _build_map_out(repo, map_)


def delete_map(repo: Repository, principal: Principal, map_id: str) -> None:
    map_ = _get_owned_map(repo, principal, map_id)
    for node in _map_nodes(repo, map_id):
        repo.delete(MapNode, node.id)
    for edge in _map_edges(repo, map_id):
        repo.delete(MapEdge, edge.id)
    for revision in repo.find(MapRevision, map_id=map_id):
        repo.delete(MapRevision, revision.id)
    repo.delete(MindMap, map_id)
    record_audit(
        repo,
        principal.user_id,
        "mindmap.delete",
        "mindmap",
        map_.id,
        details={"title": map_.title},
    )


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def add_node(
    repo: Repository, principal: Principal, map_id: str, data: NodeCreate
) -> NodeOut:
    map_ = _get_owned_map(repo, principal, map_id)

    parent: Optional[MapNode] = None
    if map_.root_node_id is None:
        if data.parent_id is not None:
            raise ValidationFailed(
                details={"field": "parent_id"},
                message="The first node of a map must be its root (parent_id must be null).",
            )
    else:
        if data.parent_id is None:
            raise ValidationFailed(
                details={"field": "parent_id"},
                message="parent_id is required; this map already has a root node.",
            )
        parent = repo.get(MapNode, data.parent_id)
        if parent is None or parent.map_id != map_id:
            raise NotFound("The parent node was not found in this mind map.")

    if data.note_id:
        _validate_note_reference(repo, map_.owner_id, data.note_id)

    label = data.label.strip()
    if not label:
        raise ValidationFailed(details={"field": "label"})

    node = MapNode.new(
        "node",
        map_id=map_id,
        label=label,
        parent_id=parent.id if parent else None,
        note_id=data.note_id,
        position=dict(data.position or {}),
    )
    repo.put(node)

    if parent is not None:
        repo.put(
            MapEdge.new(
                "edge",
                map_id=map_id,
                source_node_id=parent.id,
                target_node_id=node.id,
            )
        )

    if map_.root_node_id is None:
        map_.root_node_id = node.id
        map_.touch()
        repo.put(map_)

    record_audit(
        repo,
        principal.user_id,
        "mindmap.node.add",
        "mindmap_node",
        node.id,
        details={"map_id": map_id, "parent_id": parent.id if parent else None},
    )
    return _node_out(node)


def update_node(
    repo: Repository,
    principal: Principal,
    map_id: str,
    node_id: str,
    data: NodeUpdate,
) -> NodeOut:
    _get_owned_map(repo, principal, map_id)
    node = _get_map_node(repo, map_id, node_id)

    updates = data.model_dump(exclude_none=True)
    if "label" in updates:
        label = updates["label"].strip()
        if not label:
            raise ValidationFailed(details={"field": "label"})
        node.label = label
    if "note_id" in updates:
        note_id = updates["note_id"]
        if note_id is not None:
            map_ = repo.get(MindMap, map_id)
            _validate_note_reference(repo, map_.owner_id, note_id)
        node.note_id = note_id
    if "manually_locked" in updates:
        node.manually_locked = bool(updates["manually_locked"])
    if "position" in updates:
        node.position = dict(updates["position"] or {})

    node.touch()
    repo.put(node)
    record_audit(
        repo,
        principal.user_id,
        "mindmap.node.update",
        "mindmap_node",
        node.id,
        details={
            "map_id": map_id,
            "manually_locked": node.manually_locked,
        },
    )
    return _node_out(node)


def delete_node(
    repo: Repository, principal: Principal, map_id: str, node_id: str
) -> int:
    map_ = _get_owned_map(repo, principal, map_id)
    node = _get_map_node(repo, map_id, node_id)

    if map_.root_node_id is not None and node.id == map_.root_node_id:
        raise InvalidStateTransition(
            message="The root node cannot be deleted; a map must keep exactly one root node."
        )

    nodes_by_id = {n.id: n for n in _map_nodes(repo, map_id)}
    remove_ids = _subtree_ids(nodes_by_id, node.id)
    _delete_nodes_and_touching_edges(repo, map_id, remove_ids)

    record_audit(
        repo,
        principal.user_id,
        "mindmap.node.delete",
        "mindmap_node",
        node.id,
        details={"map_id": map_id, "removed_count": len(remove_ids)},
    )
    return len(remove_ids)


# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------

def add_edge(
    repo: Repository, principal: Principal, map_id: str, data: EdgeCreate
) -> EdgeOut:
    map_ = _get_owned_map(repo, principal, map_id)
    source = repo.get(MapNode, data.source_node_id)
    if source is None or source.map_id != map_id:
        raise NotFound("The source node was not found in this mind map.")
    target = repo.get(MapNode, data.target_node_id)
    if target is None or target.map_id != map_id:
        raise NotFound("The target node was not found in this mind map.")

    if source.id == target.id:
        raise ValidationFailed(
            details={"field": "target_node_id"},
            message="Self-loops are not allowed in a mind map.",
        )

    for edge in _map_edges(repo, map_id):
        if edge.source_node_id == source.id and edge.target_node_id == target.id:
            raise ResourceConflict(
                details={"source_node_id": source.id, "target_node_id": target.id},
                message="An edge between these nodes already exists.",
            )

    # Cycle rejection: the target must not be an ancestor of the source.
    nodes_by_id = {n.id: n for n in _map_nodes(repo, map_id)}
    visited: Set[str] = set()
    current = source
    while current.parent_id is not None:
        if current.parent_id == target.id:
            raise InvalidStateTransition(
                details={"source_node_id": source.id, "target_node_id": target.id},
                message="This edge would create a cycle in the mind-map tree.",
            )
        if current.parent_id in visited or current.parent_id not in nodes_by_id:
            break
        visited.add(current.parent_id)
        current = nodes_by_id[current.parent_id]

    edge = MapEdge.new(
        "edge",
        map_id=map_id,
        source_node_id=source.id,
        target_node_id=target.id,
        label=data.label,
    )
    repo.put(edge)
    record_audit(
        repo,
        principal.user_id,
        "mindmap.edge.add",
        "mindmap_edge",
        edge.id,
        details={"map_id": map_id, "source_node_id": source.id, "target_node_id": target.id},
    )
    return _edge_out(edge)


def delete_edge(repo: Repository, principal: Principal, map_id: str, edge_id: str) -> None:
    _get_owned_map(repo, principal, map_id)
    edge = _get_map_edge(repo, map_id, edge_id)
    repo.delete(MapEdge, edge.id)
    record_audit(
        repo,
        principal.user_id,
        "mindmap.edge.delete",
        "mindmap_edge",
        edge.id,
        details={"map_id": map_id},
    )


# ---------------------------------------------------------------------------
# Deterministic generation (mock provider)
# ---------------------------------------------------------------------------

def generate_map(
    repo: Repository, principal: Principal, map_id: str
) -> GenerateOut:
    map_ = _get_owned_map(repo, principal, map_id)
    revision = _save_revision(repo, principal, map_, "generate")

    root_id = map_.root_node_id
    nodes_by_id = {n.id: n for n in _map_nodes(repo, map_id)}

    if root_id is not None and root_id in nodes_by_id:
        keep_ids: Set[str] = {root_id}
        # Preserve locked nodes and their entire subtrees exactly.
        for node in nodes_by_id.values():
            if node.manually_locked and node.id != root_id:
                keep_ids |= _subtree_ids(nodes_by_id, node.id)
        remove_ids = set(nodes_by_id) - keep_ids
        _delete_nodes_and_touching_edges(repo, map_id, remove_ids)
        _remove_orphans_to_root(repo, map_, set(n.id for n in _map_nodes(repo, map_id)))

        remaining_children = [
            n for n in _map_nodes(repo, map_id) if n.parent_id == root_id
        ]
        _create_child_nodes(repo, map_, root_id, _chapter_child_labels(repo, map_), remaining_children)

    map_.version += 1
    map_.touch()
    repo.put(map_)
    record_audit(
        repo,
        principal.user_id,
        "mindmap.generate",
        "mindmap",
        map_.id,
        details={"version": map_.version, "revision_id": revision.id},
    )
    return GenerateOut(map=_build_map_out(repo, map_), revision_id=revision.id)


def regenerate_branch(
    repo: Repository,
    principal: Principal,
    map_id: str,
    data: BranchRegenerateIn,
) -> GenerateOut:
    map_ = _get_owned_map(repo, principal, map_id)
    branch = _get_map_node(repo, map_id, data.node_id)
    if map_.root_node_id is not None and branch.id == map_.root_node_id:
        raise ValidationFailed(
            details={"field": "node_id"},
            message="The root node's branch cannot be regenerated; use map generation instead.",
        )

    revision = _save_revision(repo, principal, map_, "regenerate-branch")

    nodes_by_id = {n.id: n for n in _map_nodes(repo, map_id)}
    descendants = _descendants(nodes_by_id, branch.id)
    keep_ids: Set[str] = {branch.id}
    for node_id in descendants:
        if nodes_by_id[node_id].manually_locked:
            keep_ids |= _subtree_ids(nodes_by_id, node_id)
    remove_ids = descendants - keep_ids
    _delete_nodes_and_touching_edges(repo, map_id, remove_ids)

    remaining_children = [
        n for n in _map_nodes(repo, map_id) if n.parent_id == branch.id
    ]
    _create_child_nodes(
        repo, map_, branch.id, _chapter_child_labels(repo, map_), remaining_children
    )

    map_.version += 1
    map_.touch()
    repo.put(map_)
    record_audit(
        repo,
        principal.user_id,
        "mindmap.branch_regenerate",
        "mindmap",
        map_.id,
        details={"version": map_.version, "node_id": branch.id, "revision_id": revision.id},
    )
    return GenerateOut(map=_build_map_out(repo, map_), revision_id=revision.id)


# ---------------------------------------------------------------------------
# Revisions and export
# ---------------------------------------------------------------------------

def list_revisions(
    repo: Repository, principal: Principal, map_id: str
) -> List[RevisionOut]:
    _get_owned_map(repo, principal, map_id)
    revisions = repo.find(MapRevision, map_id=map_id)
    revisions.sort(key=lambda r: (r.version, r.created_at), reverse=True)
    return [_revision_out(revision) for revision in revisions]


def export_map(
    repo: Repository,
    principal: Principal,
    map_id: str,
    fmt: str,
    settings: Settings,
) -> Dict:
    map_ = _get_owned_map(repo, principal, map_id)
    if fmt != "json":
        raise ValidationFailed(
            details={"field": "format", "allowed": ["json"]},
            message=f"Unsupported export format '{fmt}'.",
        )

    nodes = sorted(_map_nodes(repo, map_id), key=lambda n: (n.created_at, n.id))
    edges = sorted(_map_edges(repo, map_id), key=lambda e: (e.created_at, e.id))
    exported_at = utcnow()
    storage_name = f"mindmap_{map_.id}_v{map_.version}.json"

    payload = {
        "format": "json",
        "title": map_.title,
        "version": map_.version,
        "root_node_id": map_.root_node_id,
        "nodes": [n.model_dump(mode="json") for n in nodes],
        "edges": [e.model_dump(mode="json") for e in edges],
        "exported_at": exported_at.isoformat(),
    }

    settings.ensure_local_dirs()
    target = Path(settings.local_media_dir) / storage_name
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    record_audit(
        repo,
        principal.user_id,
        "mindmap.export",
        "mindmap",
        map_.id,
        details={"format": "json", "storage_name": storage_name},
    )
    return {**payload, "storage_name": storage_name}
