"""
Mentor AI Backend - Main Application Entry Point

This module serves as the entry point for the Mentor AI EdTech Platform backend API.
It configures FastAPI, CORS, exception handling, and routes for the application.

Features:
- FastAPI application with comprehensive CORS configuration
- Global exception handling with detailed error logging
- Health check endpoint for monitoring
- Authentication router integration
- Startup event logging

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
import traceback
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Router imports
from routers.auth_router import router as auth_router  # Parent registration endpoints (Day 1)
from routers.verification_router import router as verification_router  # Email and phone verification endpoints (Day 2)
from routers.login_router import router as login_router  # Login and session management endpoints (Day 2)
from routers.simple_register_router import router as simple_register_router  # Simple registration endpoint
from routers.preferences_router import router as preferences_router  # Parent preferences (Day 3)
from routers.child_router import router as child_router  # Child profile management (Day 3)
from routers.exam_router import router as exam_router  # Exam selection and onboarding status (Day 3)
from routers.embedding_router import router as embedding_router  # Vector search - Embedding generation
from routers.vector_search_router import router as vector_search_router  # Vector search - Semantic search
from routers.rag_router import router as rag_router  # RAG - Question generation using retrieval-augmented generation (Day 5)
from routers.diagnostic_test_router import router as diagnostic_test_router  # Diagnostic test generation and management
from routers.test_management_router import router as test_management_router  # Test lifecycle management (start, submit, results)
from routers.schedule_router import router as schedule_router  # Schedule generation and progress tracking
from routers.payment_router import router as payment_router  # Payment and subscription management
from routers.study_center_router import router as study_center_router  # Study Center Learning Journey

# New feature routers (commented out until model files are fixed)
from routers.parent_dashboard_router import router as parent_dashboard_router  # Parent dashboard and reporting
from routers.student_dashboard_router import router as student_dashboard_router  # Student dashboard and learning features
from routers.gamification_router import router as gamification_router  # Gamification features
from routers.ai_features_router import router as ai_features_router  # AI-powered features
from routers.analytics_router import router as analytics_router  # Analytics and performance insights
from routers.syllabus_coverage_router import router as syllabus_coverage_router  # Syllabus coverage tracking
from routers.analytics_router import router as analytics_router  # Analytics and performance insights
from routers.syllabus_coverage_router import router as syllabus_coverage_router  # Syllabus coverage tracking
from routers.hermes_router import router as hermes_router  # Hermes 1-to-1 AI mentor (SOUL prompt agent, micro-topic state machine, daily summaries)
from routers.marks_router import router as marks_router  # MARKS ecosystem (CPYQB, Custom Test Generator, RFC, Smart/Error Notebooks, Assignments, Heatmaps & Leagues, NEET NCERT)
from routers.sathee_ai_router import router as sathee_ai_router  # SATHEE AI Hub & Admissions (Vision OCR, SSE Socratic Stream, Similar Questions, Rank Predictor, College Cutoffs, OMR Grader)

# Vertex AI is no longer needed - using Gemini API directly

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("=" * 80)
    logger.info("Mentor AI Backend started successfully")
    logger.info("=" * 80)
    logger.info("Using Gemini API for all AI features (vector search and RAG)")
    logger.info("No Vertex AI initialization required")
    
    logger.info("Available routes:")
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            methods = ", ".join(route.methods)
            logger.info(f"  [{methods}] {route.path}")
    logger.info("=" * 80)
    
    yield
    
    # Shutdown
    logger.info("Mentor AI Backend shutting down...")
    logger.info("Cleaning up resources...")
    # Note: Vertex AI client cleanup is handled automatically
    logger.info("Shutdown complete")


# Create FastAPI application instance
app = FastAPI(
    title="Mentor AI Backend",
    version="1.0.0",
    description="Backend API for Mentor AI EdTech Platform - JEE/NEET Exam Preparation System",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend development server
        "http://127.0.0.1:3000",  # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers to the frontend
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add rate limiter middleware
from middleware.rate_limiter import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler to catch all unhandled exceptions.
    
    This handler ensures that any unexpected errors are properly logged
    and returned to the client in a consistent JSON format.
    
    Args:
        request: The incoming HTTP request
        exc: The exception that was raised
    
    Returns:
        JSONResponse with error details and 500 status code
    """
    # Get the full traceback as a string
    error_traceback = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    
    # Log the error with full traceback
    logger.error("=" * 80)
    logger.error("Unhandled Exception Occurred")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request Method: {request.method}")
    logger.error(f"Exception Type: {type(exc).__name__}")
    logger.error(f"Exception Message: {str(exc)}")
    logger.error("Traceback:")
    logger.error(error_traceback)
    logger.error("=" * 80)
    
    # Return JSON response with error details
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
                "detail": "An internal server error occurred. Please try again later."
            }
        }
    )


@app.get("/health", tags=["Health Check"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify the API is running.
    
    This endpoint is used by monitoring systems and load balancers
    to check if the service is healthy and ready to accept requests.
    
    Returns:
        Dict containing status and service name
    
    Example:
        >>> GET /health
        {
            "status": "healthy",
            "service": "mentor-ai-backend"
        }
    """
    return {
        "status": "healthy",
        "service": "mentor-ai-backend"
    }


# Include routers
# Registration router - Parent registration with email, phone, and Google OAuth
app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["Authentication"]
)

# Verification router - Email and phone verification endpoints
app.include_router(
    verification_router,
    prefix="",
    tags=["Verification"]
)

# Login router - Login, token refresh, logout, and protected endpoints
app.include_router(
    login_router,
    prefix="/api/auth",
    tags=["Login"]
)

# Preferences router - Parent preferences management (Day 3)
app.include_router(
    preferences_router,
    # Prefix and tags are already defined in the router
)

# Child profile router - Child profile management with one-child restriction (Day 3)
app.include_router(
    child_router,
    # Prefix and tags are already defined in the router
)

# Exam selection router - Exam selection and onboarding status (Day 3)
app.include_router(
    exam_router,
    # Prefix and tags are already defined in the router
)

# Embedding router - Text embedding generation using Vertex AI
app.include_router(
    embedding_router,
    # Prefix and tags are already defined in the router
)

# Vector search router - Semantic search for syllabus topics
app.include_router(
    vector_search_router,
    # Prefix and tags are already defined in the router
)

# RAG router - Question generation using retrieval-augmented generation
app.include_router(
    rag_router,
    # Prefix and tags are already defined in the router
    # Endpoints: /api/rag/generate-questions, /api/rag/generate-batch, etc.
)

# Diagnostic test router - Test generation, retrieval, and management
app.include_router(
    diagnostic_test_router,
    # Prefix and tags are already defined in the router
    # Endpoints: /api/diagnostic-test/generate, /api/diagnostic-test/{test_id}, etc.
)

# Test management router - Test lifecycle (start, submit, results)
app.include_router(
    test_management_router,
    # Prefix and tags are already defined in the router
    # Endpoints: /api/diagnostic-test/{test_id}/start, /api/diagnostic-test/{test_id}/submit, etc.
)

# Schedule router - AI-powered schedule generation and progress tracking
app.include_router(
    schedule_router,
    # Prefix and tags are already defined in the router
    # Endpoints: /api/schedule/generate, /api/schedule/{schedule_id}, /api/schedule/progress/update, etc.
)

# Payment router - Payment processing and subscription management
app.include_router(
    payment_router,
    # Prefix and tags are already defined in the router
    # Endpoints: /api/payment/plans, /api/payment/create-order, /api/payment/verify, etc.
)

# Study Center router - Learning Journey with AI-powered materials
app.include_router(
    study_center_router,
    # Prefix and tags are already defined in the router
)

# Simple Registration router - For testing without email verification
app.include_router(
    simple_register_router,
    prefix="/api/auth",
    tags=["Simple Registration"]
)

# New feature routers
# Parent dashboard router - Dashboard, reports, notifications, goals
app.include_router(
    parent_dashboard_router,
    # Prefix and tags are already defined in the router
    # Endpoints: /api/parent/dashboard, /api/parent/reports/weekly, /api/parent/goals, etc.
)

# Student dashboard router - Daily plans, practice, doubts, bookmarks
app.include_router(
    student_dashboard_router,
    # Prefix and tags are already defined in the router
    # Endpoints: /api/student/today, /api/student/practice/quick, /api/student/doubts, etc.
)

# Gamification router - Achievements, challenges, streaks, points
app.include_router(
    gamification_router,
    # Prefix and tags are already defined in the router
    # Endpoints: /api/gamification/achievements, /api/gamification/challenge/daily, etc.
)

# Analytics router - Analytics and performance insights
app.include_router(
    analytics_router,
    # Prefix and tags are already defined in the router
    # Endpoints: /api/analytics/generate, /api/analytics/student, etc.
)

# Syllabus coverage router - Syllabus coverage tracking
app.include_router(
    syllabus_coverage_router,
    # Prefix and tags are already defined in the router
    # Endpoints: /api/syllabus/coverage, etc.
)

# AI features router - AI tutor, recommendations, readiness, mistake analysis
app.include_router(
    ai_features_router,
    # Prefix and tags are already defined in the router
    # Endpoints: /api/ai/tutor/ask, /api/ai/recommend/topics, /api/ai/readiness, etc.
)

# Hermes router - 1-to-1 Socratic AI mentor (SOUL prompt, micro-topic state
# machine, Concept Wall, idempotent daily summaries in local language)
app.include_router(
    hermes_router,
    # Prefix and tags are already defined in the router
    # Endpoints: /api/hermes/chat, /api/hermes/quiz/attempt, /api/hermes/progress, etc.
)

# MARKS Competitive Ecosystem router
app.include_router(marks_router)

# SATHEE AI Hub & Admissions router
app.include_router(sathee_ai_router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint providing basic API information.
    
    Returns:
        Dict containing API information and available endpoints
    """
    return {
        "name": "Mentor AI Backend API",
        "version": "1.0.0",
        "description": "Backend API for Mentor AI EdTech Platform",
        "status": "running",
        "documentation": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc"
        },
        "endpoints": {
            "health": "/health",
            "authentication": "/api/auth",
            "onboarding": "/api/onboarding",
            "vector_search": "/api/vector-search",
            "embeddings": "/api/vector-search/embeddings",
            "diagnostic_tests": "/api/diagnostic-test",
            "test_management": "/api/diagnostic-test/{test_id}",
            "schedule": "/api/schedule",
            "progress_tracking": "/api/schedule/progress",
            "payment": "/api/payment",
            "subscriptions": "/api/payment/subscription",
            "study_center": "/api/study-center"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run the application using uvicorn
    # Note: In production, use gunicorn with uvicorn workers
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
