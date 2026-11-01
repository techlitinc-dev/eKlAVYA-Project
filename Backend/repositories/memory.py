"""
In-Memory Repository

Thread-safe, process-lifetime storage for local development and tests.
Entities are deep-copied on read and write so request handling never aliases
stored state.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import threading
from typing import Any, Dict, List, Optional, Type, TypeVar

from models.common import Entity
from repositories.base import Repository

E = TypeVar("E", bound=Entity)


class InMemoryRepository(Repository):
    """Dict-backed repository. Not production persistence."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._store: Dict[str, Dict[str, Entity]] = {}

    def put(self, entity: Entity) -> Entity:
        with self._lock:
            collection = self._store.setdefault(entity.__collection__, {})
            snapshot = entity.model_copy(deep=True)
            collection[entity.id] = snapshot
            return entity

    def get(self, entity_cls: Type[E], record_id: str) -> Optional[E]:
        with self._lock:
            record = self._store.get(entity_cls.__collection__, {}).get(record_id)
            if record is None:
                return None
            return entity_cls(**record.model_dump())

    def delete(self, entity_cls: Type[E], record_id: str) -> bool:
        with self._lock:
            collection = self._store.get(entity_cls.__collection__, {})
            return collection.pop(record_id, None) is not None

    def all(self, entity_cls: Type[E]) -> List[E]:
        with self._lock:
            records = list(self._store.get(entity_cls.__collection__, {}).values())
            return [entity_cls(**record.model_dump()) for record in records]

    def find(self, entity_cls: Type[E], **fields: Any) -> List[E]:
        matches = []
        for record in self.all(entity_cls):
            if all(getattr(record, key, None) == value for key, value in fields.items()):
                matches.append(record)
        return matches

    def reset(self) -> None:
        with self._lock:
            self._store = {}
