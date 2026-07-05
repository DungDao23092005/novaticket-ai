"""
routers/reviews.py — Review creation and listing endpoints.

Pattern: Thin router — delegates to ReviewRepository.
Sentiment analysis will be integrated in Sprint 5 (currently sentiment_label = None).

Endpoints:
    POST /reviews                    — Submit a review for an event (auth required)
    GET  /reviews/me                 — Get all reviews by current user (auth required)
    GET  /events/{event_id}/reviews  — Get all reviews for an event (public)

Design decisions:
    - 1 review per user per event (enforced in router + DB UNIQUE constraint)
    - sentiment_label left None until Sprint 5 integrates SentimentService
    - Validates event exists before creating review
    - GET /events/{id}/reviews is public — anyone can read reviews
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.database.connection import get_db
from app.models.user import User
from app.repositories.event_repository import EventRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewResponse

router = APIRouter(tags=["Reviews"])


# ----------------------------------------------------------------------
# POST /reviews
# ----------------------------------------------------------------------
@router.post(
    "/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a review for an event",
)
def create_review(
    body: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReviewResponse:
    """
    Submit a star rating and text review for an event.

    - **event_id**: The event being reviewed
    - **rating**: 1–5 stars
    - **content**: Review text (min 10 characters)

    **One review per user per event** — submitting again returns 409.

    Sentiment analysis will be added automatically in Sprint 5.

    Requires: `Authorization: Bearer <token>`
    """
    event_repo = EventRepository(db)
    review_repo = ReviewRepository(db)

    # Validate event exists
    event = event_repo.get_by_id(body.event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id={body.event_id} not found",
        )

    # Enforce 1 review per user per event
    existing = review_repo.get_by_user_and_event(current_user.id, body.event_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this event",
        )

    # Create review (sentiment_label=None until Sprint 5)
    review = review_repo.create(
        user_id=current_user.id,
        event_id=body.event_id,
        rating=body.rating,
        content=body.content,
        sentiment_label=None,
        sentiment_confidence=None,
    )

    return review


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
    # Validate event exists
    event_repo = EventRepository(db)
    event = event_repo.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id={event_id} not found",
        )

    review_repo = ReviewRepository(db)
    return review_repo.get_by_event(event_id)
