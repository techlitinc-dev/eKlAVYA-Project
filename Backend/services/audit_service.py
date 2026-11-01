"""
Audit Service

Records important actions without storing private note bodies, uploaded
images, transcripts, or secrets.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from typing import Any, Dict, Optional

from models.common import AuditEntry

logger = logging.getLogger(__name__)


def record_audit(
    repo,
    actor_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditEntry:
    """
    Persist an audit entry.

    Args:
        repo: Repository instance
        actor_id: Acting user, or None for anonymous/system
        action: Stable action verb (e.g. "note.share", "call.transition")
        resource_type: Domain resource type
        resource_id: Affected record id
        details: Small structured context (no private bodies or secrets)
    """
    entry = AuditEntry.new(
        "audit",
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
    )
    repo.put(entry)
    return entry
