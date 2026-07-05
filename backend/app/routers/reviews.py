"""
routers/reviews.py — Review creation and listing endpoints.

Pattern: Thin router — delegates to ReviewService (POST) and ReviewRepository (GET).

Endpoints:
    POST /reviews                    — Submit a review (auth required); auto-predicts sentiment
    GET  /reviews/me                 — Get all reviews by current user (auth required)
    GET  /events/{event_id}/reviews  — Get all reviews for an event (public)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.database.connection import get_db
from app.models.user import User
from app.repositories.event_repository import EventRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewResponse
from app.services.review_service import ReviewService

router = APIRouter(tags=["Reviews"])


# ----------------------------------------------------------------------
# POST /reviews
# ----------------------------------------------------------------------
@router.post(
    "/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a review for an event (sentiment auto-predicted)",
)
def create_review(
    body: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReviewResponse:
    """
    Submit a star rating and text review for an event.

    **Sentiment is automatically predicted** from review content:
    - `sentiment_label`: `positive` | `neutral` | `negative`
    - `sentiment_confidence`: Model confidence (0.0 – 1.0)

    **One review per user per event** — submitting again returns 409.

    Requires: `Authorization: Bearer <token>`
    """
    service = ReviewService(db)
    return service.create_review(user_id=current_user.id, data=body)


# ----------------------------------------------------------------------
# GET /reviews/me
# ----------------------------------------------------------------------
@router.get(
    "/reviews/me",
    response_model=list[ReviewResponse],
    summary="Get all reviews by the current user",
)
def get_my_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ReviewResponse]:
    """
    Returns all reviews written by the authenticated user.

    Requires: `Authorization: Bearer <token>`
    """
    repo = ReviewRepository(db)
    return repo.get_by_user(current_user.id)


# ----------------------------------------------------------------------
# GET /events/{event_id}/reviews
# ----------------------------------------------------------------------
@router.get(
    "/events/{event_id}/reviews",
    response_model=list[ReviewResponse],
    summary="Get all reviews for an event",
)
def get_event_reviews(
    event_id: int,
    db: Session = Depends(get_db),
) -> list[ReviewResponse]:
    """
    Returns all reviews for a specific event, ordered by most recent first.
    Public endpoint — no authentication required.

    Returns an empty list if the event has no reviews (not 404).
    """
    event_repo = EventRepository(db)
    event = event_repo.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id={event_id} not found",
        )

    review_repo = ReviewRepository(db)
    return review_repo.get_by_event(event_id)

