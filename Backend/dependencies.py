"""
Shared FastAPI Dependencies

- Repository singleton access through app.state (shared across requests)
- Request-ID middleware for the documented error envelope
- Cursor pagination helpers (limit default 20, maximum 100)
- Idempotency-Key handling for creation/generation/execution endpoints

Author: eKlAVYA Backend
Version: 1.0.0
"""

import base64
import hashlib
import json
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import Depends, Query, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from core.config import Settings, get_settings
from core.errors import IdempotencyConflict
from core.ids import new_request_id
from core.security import Principal
from core.time import utcnow
from models.common import Entity
from repositories.base import Repository

logger = logging.getLogger(__name__)


def get_repository(request: Request) -> Repository:
    """
    Return the shared repository stored on app.state.

    The instance is created once at application startup and reused for the
    lifetime of the process; tests replace it with a freshly seeded instance.
    """
    repo = getattr(request.app.state, "repository", None)
    if repo is None:
        raise RuntimeError(
            "Application state has no repository. The app lifespan did not run; "
            "use TestClient as a context manager or start uvicorn normally."
        )
    return repo


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Stamp every request with an id echoed in errors and the response header."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-Id") or new_request_id()
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def decode_cursor(cursor: Optional[str]) -> int:
    """Decode an opaque pagination cursor into a list offset."""
    if not cursor:
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
        offset = int(data.get("o", 0))
        return max(offset, 0)
    except Exception:
        from core.errors import ValidationFailed

        raise ValidationFailed(
            details={"field": "cursor"},
            message="Invalid pagination cursor.",
        )


def encode_cursor(offset: int) -> str:
    raw = json.dumps({"o": offset}).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def paginate(
    items: Sequence[Any],
    limit: int = DEFAULT_LIMIT,
    cursor: Optional[str] = None,
) -> Tuple[List[Any], Optional[str]]:
    """
    Apply cursor pagination to an in-memory list.

    Returns:
        (page_items, next_cursor or None)
    """
    offset = decode_cursor(cursor)
    page = list(items[offset:offset + limit])
    next_offset = offset + len(page)
    next_cursor = encode_cursor(next_offset) if next_offset < len(items) else None
    return page, next_cursor


class PaginationParams:
    """Parsed pagination query parameters."""

    def __init__(
        self,
        limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
        cursor: Optional[str] = Query(None),
    ) -> None:
        self.limit = limit
        self.cursor = cursor


def get_pagination(params: PaginationParams = Depends()) -> PaginationParams:
    return params


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

def canonical_body_hash(body: Optional[Dict[str, Any]]) -> str:
    """Stable hash of a request body for idempotency comparison."""
    serialized = json.dumps(body or {}, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class IdempotencyRecord(Entity):
    __collection__ = "idempotency_keys"

    user_id: str
    scope: str
    key: str
    body_hash: str
    status_code: int
    response: Dict[str, Any]


class IdempotencyManager:
    """
    Implements the Idempotency-Key contract:

    - Same user + key + body returns the original stored response.
    - Same key with a different body returns 409 IDEMPOTENCY_CONFLICT.
    - Keys expire after the configured local retention period.
    """

    def __init__(self, repo: Repository, settings: Settings, principal: Principal) -> None:
        self.repo = repo
        self.settings = settings
        self.principal = principal

    def _find(self, scope: str, key: str) -> Optional[IdempotencyRecord]:
        return self.repo.first(
            IdempotencyRecord,
            user_id=self.principal.user_id,
            scope=scope,
            key=key,
        )

    def _expired(self, record: IdempotencyRecord) -> bool:
        cutoff = record.created_at + timedelta(
            hours=self.settings.idempotency_retention_hours
        )
        return utcnow() > cutoff

    def replay(
        self, scope: str, key: str, body: Optional[Dict[str, Any]]
    ) -> Optional[IdempotencyRecord]:
        """Return the stored response for a matching request, if any."""
        record = self._find(scope, key)
        if record is None:
            return None
        if self._expired(record):
            self.repo.delete(IdempotencyRecord, record.id)
            return None
        if record.body_hash != canonical_body_hash(body):
            raise IdempotencyConflict(
                details={"key": key, "scope": scope},
                message="This Idempotency-Key was already used with a different body.",
            )
        return record

    def store(
        self,
        scope: str,
        key: str,
        body: Optional[Dict[str, Any]],
        status_code: int,
        response: Dict[str, Any],
    ) -> IdempotencyRecord:
        record = IdempotencyRecord.new(
            "idem",
            user_id=self.principal.user_id,
            scope=scope,
            key=key,
            body_hash=canonical_body_hash(body),
            status_code=status_code,
            response=response,
        )
        self.repo.put(record)
        return record
