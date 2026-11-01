"""
Application Error Contract

All eKlAVYA endpoints return errors in one documented envelope:

    {"error": {"code", "message", "details", "request_id"}}

Python tracebacks and raw provider errors are never exposed to clients.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """
    Base class for documented application errors.

    Attributes:
        status_code: HTTP status code
        code: Stable machine-readable error code
        message: Human-readable description
        details: Optional structured context
    """

    status_code: int = 400
    code: str = "VALIDATION_ERROR"
    message: str = "The request could not be processed."

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message or self.message)
        if message:
            self.message = message
        self.details = details or {}


class ValidationFailed(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"
    message = "The request failed validation."


class AuthenticationRequired(AppError):
    status_code = 401
    code = "AUTHENTICATION_REQUIRED"
    message = "Authentication is required to access this resource."


class PermissionDenied(AppError):
    status_code = 403
    code = "PERMISSION_DENIED"
    message = "You do not have permission to perform this action."


class NotFound(AppError):
    status_code = 404
    code = "NOT_FOUND"
    message = "The requested resource was not found."


class SyllabusContextInvalid(AppError):
    status_code = 422
    code = "SYLLABUS_CONTEXT_INVALID"
    message = "The selected topic does not belong to the active syllabus."


class ResourceConflict(AppError):
    status_code = 409
    code = "RESOURCE_CONFLICT"
    message = "The resource was modified by another request."


class IdempotencyConflict(AppError):
    status_code = 409
    code = "IDEMPOTENCY_CONFLICT"
    message = "The idempotency key was already used with a different request body."


class InvalidStateTransition(AppError):
    status_code = 409
    code = "INVALID_STATE_TRANSITION"
    message = "The requested state transition is not allowed."


class UploadTooLarge(AppError):
    status_code = 413
    code = "UPLOAD_TOO_LARGE"
    message = "The uploaded file exceeds the maximum allowed size."


class UploadTypeNotAllowed(AppError):
    status_code = 415
    code = "UPLOAD_TYPE_NOT_ALLOWED"
    message = "The uploaded file type is not allowed."


class OcrConfirmationRequired(AppError):
    status_code = 409
    code = "OCR_CONFIRMATION_REQUIRED"
    message = "OCR output must be confirmed before this scan can be executed."


class GroundingFailed(AppError):
    status_code = 422
    code = "GROUNDING_FAILED"
    message = "The answer could not be grounded in approved sources."


class ProviderUnavailable(AppError):
    status_code = 503
    code = "PROVIDER_UNAVAILABLE"
    message = "A required provider is temporarily unavailable."


class RateLimited(AppError):
    status_code = 429
    code = "RATE_LIMITED"
    message = "Too many requests. Please retry later."


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or "unknown"


def error_payload(err: AppError, request_id: str) -> Dict[str, Any]:
    return {
        "error": {
            "code": err.code,
            "message": err.message,
            "details": err.details,
            "request_id": request_id,
        }
    }


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc, _request_id(request)),
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    err = ValidationFailed(details={"errors": exc.errors()})
    return JSONResponse(
        status_code=err.status_code,
        content=error_payload(err, _request_id(request)),
    )


async def http_error_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code = "NOT_FOUND" if exc.status_code == 404 else "VALIDATION_ERROR"
    payload = {
        "error": {
            "code": code,
            "message": str(exc.detail) if exc.detail else "Request failed.",
            "details": {},
            "request_id": _request_id(request),
        }
    }
    return JSONResponse(status_code=exc.status_code, content=payload)


def install_exception_handlers(app: FastAPI) -> None:
    """Register the documented error envelope handlers on the app."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
