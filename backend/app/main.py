"""
main.py — FastAPI application entry point.

This module:
- Creates the FastAPI app instance
- Configures CORS middleware
- Mounts all routers
- Defines the lifespan (startup/shutdown hooks)
- Provides the /health endpoint

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


# ----------------------------------------------------------------------
# Lifespan — runs before first request and after last request
# This is where we'll initialize DB and load ML models in later sprints
# ----------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown logic.
    - Startup: runs before the app starts accepting requests
    - Shutdown: runs after the app stops accepting requests

    Currently: verifies DB connection on startup.
    Will be expanded in Sprint 5 (ML model loading).
    """
    # --- STARTUP ---
    print(f"[NovaTicket] Starting {settings.app_name} v{settings.app_version}")
    print(f"[NovaTicket] Environment: {settings.environment}")
    print(f"[NovaTicket] Debug mode: {settings.debug}")

    # Verify database connection at startup (fail fast if DB is unreachable)
    try:
        from app.database.connection import check_database_connection
        check_database_connection()
        print("[NovaTicket] Database connection: OK")
    except Exception as exc:
        # Log the error but don't crash the app — DB may not be needed for all routes
        # In production, you would raise here to prevent serving with broken DB
        print(f"[NovaTicket] WARNING: Database connection failed: {exc}")

    yield  # Application runs here

    # --- SHUTDOWN ---
    print(f"[NovaTicket] Shutting down {settings.app_name}")


# ----------------------------------------------------------------------
# FastAPI App Instance
# ----------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "NovaTicket — AI-powered event recommendation and sentiment analysis platform. "
        "Provides personalized event recommendations using Content-Based Filtering, "
        "Collaborative Filtering, and Hybrid approaches. "
        "Analyzes user reviews with ML-based sentiment classification."
    ),
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ----------------------------------------------------------------------
# CORS Middleware
# Must be added BEFORE routers are mounted
# ----------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------
# Routers
# Added incrementally as each sprint builds the feature
# ----------------------------------------------------------------------
from app.routers import auth        # Sprint 2
from app.routers import categories  # Sprint 3 - P1
from app.routers import events      # Sprint 3 - P3

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(events.router)

# Sprint 4:
# from app.routers import interactions, reviews
#
# Sprint 6:
# from app.routers import recommendations


# ----------------------------------------------------------------------
# Core Endpoints
# ----------------------------------------------------------------------
@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Returns application status. Used by Docker health checks and load balancers.",
)
async def health_check() -> dict:
    """
    Health check endpoint.
    Returns 200 OK with app info when the service is running.
    """
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get(
    "/",
    tags=["System"],
    summary="Root",
    description="Root endpoint — redirects users to API documentation.",
)
async def root() -> dict:
    """Root endpoint — quick reference to docs."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "health": "/health",
    }