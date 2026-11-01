"""
Authentication and Authorization Primitives

Development identity (TESTING_MODE=true) is established through headers:

    X-User-Id: student_aarav
    X-User-Role: student
    X-User-Name: Aarav Sharma

Supported roles: student, teacher, parent, admin.

When TESTING_MODE is disabled, the existing real authentication boundary is
used: a Firebase ID token supplied as ``Authorization: Bearer <token>``.
Role headers are never treated as production authentication.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from typing import Callable, Optional

from fastapi import Depends, Request
from pydantic import BaseModel

from core.config import Settings, get_settings
from core.errors import AuthenticationRequired, PermissionDenied, ValidationFailed

logger = logging.getLogger(__name__)

ROLES = ("student", "teacher", "parent", "admin")


class Principal(BaseModel):
    """Authenticated caller identity."""

    user_id: str
    role: str
    name: str

    def has_role(self, *roles: str) -> bool:
        return self.role in roles


def get_principal_from_headers(request: Request) -> Principal:
    """Build a Principal from development identity headers."""
    user_id = request.headers.get("X-User-Id")
    role = request.headers.get("X-User-Role", "student").strip().lower()
    name = request.headers.get("X-User-Name")

    if not user_id:
        raise AuthenticationRequired(
            "Missing development identity header X-User-Id."
        )
    if role not in ROLES:
        raise ValidationFailed(
            details={"field": "X-User-Role", "allowed": list(ROLES)},
            message=f"Unsupported role '{role}'.",
        )
    return Principal(user_id=user_id, role=role, name=name or user_id)


def get_principal_from_token(request: Request) -> Principal:
    """Verify a Firebase ID token and build a Principal (real auth path)."""
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise AuthenticationRequired("Missing Bearer token.")

    token = authorization[len("Bearer "):].strip()
    if not token:
        raise AuthenticationRequired("Missing Bearer token.")

    try:
        from utils.firebase_config import get_auth_client

        decoded = get_auth_client().verify_id_token(token)
    except Exception as exc:  # Firebase raises several concrete types
        logger.warning("Token verification failed: %s", type(exc).__name__)
        raise AuthenticationRequired("Invalid or expired token.") from exc

    claims_role = (decoded.get("role") or "student").lower()
    role = claims_role if claims_role in ROLES else "student"
    name = decoded.get("name") or decoded.get("uid")
    return Principal(user_id=decoded["uid"], role=role, name=name)


def get_current_principal(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Principal:
    """
    Resolve the authenticated principal for the current request.

    Testing mode uses development headers; otherwise Firebase Bearer tokens
    are verified. This boundary is explicit and never silently mixed.
    """
    if settings.testing_mode:
        return get_principal_from_headers(request)
    return get_principal_from_token(request)


def require_roles(*roles: str) -> Callable:
    """Dependency factory restricting an endpoint to the given roles."""

    def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.role not in roles:
            raise PermissionDenied(
                details={"required_roles": list(roles), "actual_role": principal.role},
                message=f"This endpoint requires one of the roles: {', '.join(roles)}.",
            )
        return principal

    return dependency


def optional_principal(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Optional[Principal]:
    """Return the principal when credentials are supplied, else None."""
    try:
        return get_current_principal(request, settings)
    except AuthenticationRequired:
        return None
