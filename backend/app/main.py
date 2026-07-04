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

    Currently: just logs startup/shutdown.
    Will be expanded in Sprint 1 (DB) and Sprint 5 (ML models).
    """
    # --- STARTUP ---
    print(f"[NovaTicket] Starting {settings.app_name} v{settings.app_version}")
    print(f"[NovaTicket] Environment: {settings.environment}")
    print(f"[NovaTicket] Debug mode: {settings.debug}")

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
# Will be added incrementally as each sprint builds the feature:
#
# Sprint 2: from app.routers import auth, users
#           app.include_router(auth.router)
#           app.include_router(users.router)
#
# Sprint 3: from app.routers import events, categories
# Sprint 4: from app.routers import interactions, reviews
# Sprint 6: from app.routers import recommendations
# ----------------------------------------------------------------------


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
