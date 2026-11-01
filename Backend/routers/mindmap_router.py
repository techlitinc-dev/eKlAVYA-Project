"""
Mind-Map Router

Map CRUD with optimistic concurrency, node/edge management with tree
invariants, deterministic mock generation with revision snapshots, and local
JSON export. All paths are registered under /api/v1.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from core.config import Settings, get_settings
from core.security import Principal, get_current_principal
from dependencies import (
    IdempotencyManager,
    PaginationParams,
    get_pagination,
    get_repository,
    paginate,
)
from models.common import Page
from models.mindmaps import (
    BranchRegenerateIn,
    EdgeCreate,
    EdgeOut,
    ExportIn,
    ExportOut,
    GenerateOut,
    MapCreate,
    MapOut,
    MapUpdate,
    NodeCreate,
    NodeUpdate,
    NodeOut,
    RevisionOut,
)
from repositories.base import Repository
from services import mindmap_service as service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Mind Maps"])


@router.get(
    "/mindmaps",
    response_model=Page[MapOut],
    summary="List mind maps (owner; admin sees all)",
)
def list_maps(
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
) -> Page[MapOut]:
    items = service.list_maps(repo, principal)
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[MapOut](items=page, next_cursor=next_cursor)


@router.post(
    "/mindmaps",
    response_model=MapOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a mind map with exactly one root node",
)
def create_map(
    payload: MapCreate,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body = payload.model_dump()
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("mindmap.create", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    map_out = service.create_map(repo, principal, payload)
    if idem_key:
        manager.store(
            "mindmap.create",
            idem_key,
            body,
            status.HTTP_201_CREATED,
            jsonable_encoder(map_out),
        )
    return map_out


@router.get(
    "/mindmaps/{map_id}",
    response_model=MapOut,
    summary="Get a mind map with nodes and edges",
)
def get_map(
    map_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> MapOut:
    return service.get_map(repo, principal, map_id)


@router.patch(
    "/mindmaps/{map_id}",
    response_model=MapOut,
    summary="Update a mind map (optimistic concurrency)",
)
def update_map(
    map_id: str,
    payload: MapUpdate,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> MapOut:
    return service.update_map(repo, principal, map_id, payload)


@router.delete(
    "/mindmaps/{map_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a mind map and all its nodes, edges, and revisions",
)
def delete_map(
    map_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> Response:
    service.delete_map(repo, principal, map_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/mindmaps/{map_id}/nodes",
    response_model=NodeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a node (auto-creates an edge from its parent)",
)
def add_node(
    map_id: str,
    payload: NodeCreate,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body = payload.model_dump()
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("mindmap.node.create", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    node_out = service.add_node(repo, principal, map_id, payload)
    if idem_key:
        manager.store(
            "mindmap.node.create",
            idem_key,
            body,
            status.HTTP_201_CREATED,
            jsonable_encoder(node_out),
        )
    return node_out


@router.patch(
    "/mindmaps/{map_id}/nodes/{node_id}",
    response_model=NodeOut,
    summary="Update a node (label, note link, manual lock, position)",
)
def update_node(
    map_id: str,
    node_id: str,
    payload: NodeUpdate,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> NodeOut:
    return service.update_node(repo, principal, map_id, node_id, payload)


@router.delete(
    "/mindmaps/{map_id}/nodes/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a node, its descendants, and all touching edges (root is protected)",
)
def delete_node(
    map_id: str,
    node_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> Response:
    service.delete_node(repo, principal, map_id, node_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/mindmaps/{map_id}/edges",
    response_model=EdgeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add an edge (tree-direction only; cycles, duplicates, self-loops rejected)",
)
def add_edge(
    map_id: str,
    payload: EdgeCreate,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> EdgeOut:
    return service.add_edge(repo, principal, map_id, payload)


@router.delete(
    "/mindmaps/{map_id}/edges/{edge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an edge",
)
def delete_edge(
    map_id: str,
    edge_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> Response:
    service.delete_edge(repo, principal, map_id, edge_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/mindmaps/{map_id}/generate",
    response_model=GenerateOut,
    summary="Deterministically regenerate the map (mock provider, saves a revision)",
)
def generate_map(
    map_id: str,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body = {"map_id": map_id}
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("mindmap.generate", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    result = service.generate_map(repo, principal, map_id)
    if idem_key:
        manager.store(
            "mindmap.generate",
            idem_key,
            body,
            status.HTTP_200_OK,
            jsonable_encoder(result),
        )
    return result


@router.post(
    "/mindmaps/{map_id}/regenerate-branch",
    response_model=GenerateOut,
    summary="Deterministically regenerate a node's subtree (preserves locked nodes)",
)
def regenerate_branch(
    map_id: str,
    payload: BranchRegenerateIn,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> GenerateOut:
    return service.regenerate_branch(repo, principal, map_id, payload)


@router.get(
    "/mindmaps/{map_id}/revisions",
    response_model=Page[RevisionOut],
    summary="List saved map revisions (version descending)",
)
def list_revisions(
    map_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
) -> Page[RevisionOut]:
    items = service.list_revisions(repo, principal, map_id)
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[RevisionOut](items=page, next_cursor=next_cursor)


@router.post(
    "/mindmaps/{map_id}/export",
    response_model=ExportOut,
    summary="Export a mind map as structured JSON and persist it locally",
)
def export_map(
    map_id: str,
    payload: Optional[ExportIn] = None,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> ExportOut:
    return service.export_map(repo, principal, map_id, payload.format if payload else "json", settings)
