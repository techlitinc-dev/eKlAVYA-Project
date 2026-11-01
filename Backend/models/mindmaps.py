"""
Mind-Map Domain Models

Maps with exactly one root node, child nodes, edges, and saved revisions.

Author: eKlAVYA Backend
Version: 1.0.0
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from models.common import Entity


class MindMap(Entity):
    __collection__ = "mindmaps"

    owner_id: str
    title: str
    root_node_id: Optional[str] = None

    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None

    version: int = 1
    source: str = "manual"  # manual | generated | scan | ai_action
    source_id: Optional[str] = None


class MapNode(Entity):
    __collection__ = "mindmap_nodes"

    map_id: str
    label: str
    parent_id: Optional[str] = None
    manually_locked: bool = False
    note_id: Optional[str] = None
    position: Dict[str, float] = Field(default_factory=dict)


class MapEdge(Entity):
    __collection__ = "mindmap_edges"

    map_id: str
    source_node_id: str
    target_node_id: str
    label: Optional[str] = None


class MapRevision(Entity):
    __collection__ = "mindmap_revisions"

    map_id: str
    version: int
    nodes: List[Dict] = Field(default_factory=list)
    edges: List[Dict] = Field(default_factory=list)
    created_by: str
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# API schemas
# ---------------------------------------------------------------------------


class NodeOut(BaseModel):
    id: str
    map_id: str
    label: str
    parent_id: Optional[str] = None
    manually_locked: bool = False
    note_id: Optional[str] = None
    position: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class EdgeOut(BaseModel):
    id: str
    map_id: str
    source_node_id: str
    target_node_id: str
    label: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MapOut(BaseModel):
    id: str
    owner_id: str
    title: str
    root_node_id: Optional[str] = None
    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None
    version: int
    source: str
    source_id: Optional[str] = None
    node_count: int = 0
    edge_count: int = 0
    nodes: List[NodeOut] = Field(default_factory=list)
    edges: List[EdgeOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MapCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    root_label: Optional[str] = Field(None, max_length=200)
    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None
    source: str = "manual"


class MapUpdate(BaseModel):
    """PATCH /mindmaps/{mapId} request body (optimistic concurrency)."""

    version: int = Field(..., ge=1)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None


class NodeCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=200)
    parent_id: Optional[str] = None
    note_id: Optional[str] = None
    position: Dict[str, float] = Field(default_factory=dict)


class NodeUpdate(BaseModel):
    label: Optional[str] = Field(None, min_length=1, max_length=200)
    note_id: Optional[str] = None
    manually_locked: Optional[bool] = None
    position: Optional[Dict[str, float]] = None


class EdgeCreate(BaseModel):
    source_node_id: str
    target_node_id: str
    label: Optional[str] = Field(None, max_length=200)


class GenerateOut(BaseModel):
    map: MapOut
    revision_id: str


class BranchRegenerateIn(BaseModel):
    node_id: str


class RevisionOut(BaseModel):
    id: str
    map_id: str
    version: int
    reason: Optional[str] = None
    created_by: str
    node_count: int = 0
    edge_count: int = 0
    created_at: datetime


class ExportIn(BaseModel):
    format: str = "json"


class ExportOut(BaseModel):
    format: str
    title: str
    version: int
    root_node_id: Optional[str] = None
    nodes: List[NodeOut] = Field(default_factory=list)
    edges: List[EdgeOut] = Field(default_factory=list)
    exported_at: datetime
    storage_name: str
