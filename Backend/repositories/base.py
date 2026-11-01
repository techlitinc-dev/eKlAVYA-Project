"""
Repository Interface

Abstract storage interface for eKlAVYA entities. Implementations must be
shared through FastAPI dependency injection, support reset between tests, and
protect mutations sufficiently for the local test server.

The in-memory implementation is for local development and tests only; it is
never production persistence.

Author: eKlAVYA Backend
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar

from models.common import Entity

E = TypeVar("E", bound=Entity)


class Repository(ABC):
    """Storage interface keyed by entity collection and id."""

    @abstractmethod
    def put(self, entity: Entity) -> Entity:
        """Insert or replace an entity (deep-copied)."""

    @abstractmethod
    def get(self, entity_cls: Type[E], record_id: str) -> Optional[E]:
        """Fetch an entity by id, or None."""

    @abstractmethod
    def delete(self, entity_cls: Type[E], record_id: str) -> bool:
        """Remove an entity; returns True when one existed."""

    @abstractmethod
    def all(self, entity_cls: Type[E]) -> List[E]:
        """Return every entity of the given type."""

    @abstractmethod
    def find(self, entity_cls: Type[E], **fields: Any) -> List[E]:
        """Exact-match filter on entity fields."""

    @abstractmethod
    def reset(self) -> None:
        """Remove all stored state (tests/local use only)."""

    def first(self, entity_cls: Type[E], **fields: Any) -> Optional[E]:
        matches = self.find(entity_cls, **fields)
        return matches[0] if matches else None

    def count(self, entity_cls: Type[E], **fields: Any) -> int:
        return len(self.find(entity_cls, **fields))
