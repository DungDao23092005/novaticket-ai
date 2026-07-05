"""
routers/interactions.py — Interaction tracking endpoints.

Pattern: Thin router — delegates to InteractionRepository.
All endpoints require authentication (JWT).

Endpoints:
    POST /interactions          — Record a user interaction with an event
    GET  /interactions/me       — Get current user's interaction history

Design:
    - POST uses upsert: same (user, event, type) → update score, not duplicate
    - Score is set automatically based on interaction_type (not from client)
    - Event existence is validated before recording interaction
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.database.connection import get_db
from app.models.user import User
from app.repositories.event_repository import EventRepository
from app.repositories.interaction_repository import InteractionRepository
from app.schemas.interaction import (
    INTERACTION_SCORES,
    InteractionCreate,
    InteractionResponse,
)

router = APIRouter(prefix="/interactions", tags=["Interactions"])


# ----------------------------------------------------------------------
# POST /interactions
# ----------------------------------------------------------------------
@router.post(
    "",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a user interaction with an event",
)
def record_interaction(
    body: InteractionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InteractionResponse:
    """
    Record that the current authenticated user interacted with an event.

    **Interaction types and their recommendation weights:**
    | Type | Score | When to use |
    |---|---|---|
    | `view` | 1.0 | User viewed event detail page |
    | `click` | 2.0 | User clicked on event card |
    | `favorite` | 3.0 | User bookmarked/favorited event |
    | `register` | 5.0 | User registered for event (strongest signal) |

    **Upsert behavior**: If the same user already has a `view` on this event,
    calling again with `view` updates the score rather than creating a duplicate.

    Requires: `Authorization: Bearer <token>`
    """
    event_repo = EventRepository(db)
    interaction_repo = InteractionRepository(db)

    # Validate event exists
    event = event_repo.get_by_id(body.event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id={body.event_id} not found",
        )

    # Score is determined server-side from interaction type
    score = INTERACTION_SCORES[body.interaction_type]

    # Upsert: prevent duplicate rows for same (user, event, type)
    interaction = interaction_repo.upsert(
        user_id=current_user.id,
        event_id=body.event_id,
        interaction_type=body.interaction_type,
        interaction_score=score,
    )

    return interaction


# ----------------------------------------------------------------------
# GET /interactions/me
# ----------------------------------------------------------------------
@router.get(
    "/me",
    response_model=list[InteractionResponse],
    summary="Get current user's interaction history",
)
def get_my_interactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[InteractionResponse]:
    """
    Returns all interactions recorded for the current authenticated user,
    ordered by most recent first.

    Requires: `Authorization: Bearer <token>`
    """
    repo = InteractionRepository(db)
    return repo.get_by_user(current_user.id)
