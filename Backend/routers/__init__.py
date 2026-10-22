"""
Routers package for Mentor AI Platform.

This package contains all FastAPI routers for the application.
"""

# Import all routers
from routers.analytics_router import router as analytics_router
from routers.auth_router import router as auth_router
from routers.child_router import router as child_router
from routers.diagnostic_test_router import router as diagnostic_test_router
from routers.embedding_router import router as embedding_router
from routers.exam_router import router as exam_router
from routers.login_router import router as login_router
from routers.payment_router import router as payment_router
from routers.preferences_router import router as preferences_router
from routers.question_router import router as question_router
from routers.rag_router import router as rag_router
from routers.schedule_router import router as schedule_router
from routers.test_management_router import router as test_management_router
from routers.vector_search_router import router as vector_search_router
from routers.verification_router import router as verification_router

__all__ = [
    "analytics_router",
    "auth_router",
    "child_router",
    "diagnostic_test_router",
    "embedding_router",
    "exam_router",
    "login_router",
    "payment_router",
    "preferences_router",
    "question_router",
    "rag_router",
    "schedule_router",
    "test_management_router",
    "vector_search_router",
    "verification_router"
]
