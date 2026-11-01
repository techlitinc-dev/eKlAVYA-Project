"""
Relationship-Based Access Helpers

Shared authorization decisions used by services across domains:

- Students can access only their own records.
- Teachers can access students assigned through a shared class.
- Parents can access only linked children, read-only.
- Admins can access everything.

Cross-student private records are hidden with 404; role-level violations use
403, per the documented authorization behavior.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from typing import Optional

from core.errors import NotFound, PermissionDenied
from core.security import Principal
from models.common import ClassRoom, ParentLink

logger = logging.getLogger(__name__)


def is_admin(principal: Principal) -> bool:
    return principal.role == "admin"


def teacher_can_access_student(repo, teacher_id: str, student_id: str) -> bool:
    """True when the teacher shares an assigned class with the student."""
    for classroom in repo.all(ClassRoom):
        if (
            teacher_id in classroom.teacher_ids
            and student_id in classroom.student_ids
        ):
            return True
    return False


def parent_can_access_student(repo, parent_id: str, student_id: str) -> bool:
    """True when the parent is linked to the child."""
    for link in repo.all(ParentLink):
        if link.parent_id == parent_id and link.student_id == student_id:
            return True
    return False


def assert_owner_access(principal: Principal, owner_id: str) -> None:
    """
    Allow only the owner (or admin) to act on a private record.

    Other users receive 404 so private records are not exposed.
    """
    if is_admin(principal):
        return
    if principal.user_id != owner_id:
        raise NotFound("The requested resource was not found.")


def get_owned_record(repo, entity_cls, record_id: str, principal: Principal):
    """
    Fetch a record that belongs to the principal (404 otherwise).

    Returns:
        The entity when the principal is the owner or an admin.
    """
    record = repo.get(entity_cls, record_id)
    if record is None:
        raise NotFound()
    assert_owner_access(principal, record.owner_id)
    return record


def resolve_student_scope(
    repo,
    principal: Principal,
    student_id: Optional[str] = None,
) -> str:
    """
    Resolve which student's records an authenticated caller may address.

    Rules:
        student: may only address themselves (explicit mismatched id -> 404)
        teacher: may address students assigned through a shared class
        parent:  may address linked children (read-only; enforcement of
                 read-only behavior stays with the calling endpoint)
        admin:   may address anyone

    Returns:
        str: The effective student_id
    """
    if is_admin(principal):
        target = student_id or principal.user_id
        return target

    if principal.role == "student":
        if student_id and student_id != principal.user_id:
            raise NotFound("The requested resource was not found.")
        return principal.user_id

    if principal.role == "teacher":
        target = student_id or principal.user_id
        if not teacher_can_access_student(repo, principal.user_id, target):
            raise PermissionDenied(
                details={"student_id": target},
                message="You are not assigned to this student.",
            )
        return target

    if principal.role == "parent":
        target = student_id or _first_linked_child(repo, principal.user_id)
        if target is None or not parent_can_access_student(
            repo, principal.user_id, target
        ):
            raise PermissionDenied(
                details={"student_id": target},
                message="You are not linked to this student.",
            )
        return target

    raise PermissionDenied()


def _first_linked_child(repo, parent_id: str) -> Optional[str]:
    for link in repo.all(ParentLink):
        if link.parent_id == parent_id:
            return link.student_id
    return None


def assert_teacher_or_admin(principal: Principal) -> None:
    if principal.role not in ("teacher", "admin"):
        raise PermissionDenied("This action requires a teacher or admin role.")


def assert_parent_read_only(principal: Principal) -> None:
    """Parents never modify student tasks, notes, or progress."""
    if principal.role == "parent":
        raise PermissionDenied("Parents have read-only access to child records.")
