"""
Identifier Generation Module

Server-side UUID-based identifiers with human-readable prefixes.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import uuid


def new_id(prefix: str) -> str:
    """
    Generate a new prefixed UUID identifier.

    Args:
        prefix: Short semantic prefix (e.g. "note", "task", "req")

    Returns:
        str: Identifier like "note_9f2c1ab3d4e54a6b8c0d1e2f3a4b5c6d"
    """
    return f"{prefix}_{uuid.uuid4().hex}"


def new_request_id() -> str:
    """Generate an opaque request identifier for error responses."""
    return new_id("req")
