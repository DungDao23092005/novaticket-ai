"""
services/review_service.py — Business logic for review creation with sentiment.

Orchestrates:
    1. ReviewRepository   — DB persistence
    2. EventRepository    — validate event exists
    3. SentimentModel     — predict label + confidence from review text

Pattern:
    Router → ReviewService → [ReviewRepository, EventRepository, SentimentModel]

Sentiment integration:
    - If model is loaded: predict label + confidence, save alongside review
    - If model NOT loaded (artifact missing): save review with sentiment_label=None
      (graceful degradation — API continues working without ML)
"""

import logging

from fastapi import HTTPException, status

from app.ml.sentiment_model import sentiment_model
from app.models.review import Review
from app.repositories.event_repository import EventRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate

logger = logging.getLogger(__name__)


class ReviewService:
    """Business logic for review creation with integrated sentiment analysis."""

    def __init__(self, db) -> None:
        self.db = db
        self.review_repo = ReviewRepository(db)
        self.event_repo = EventRepository(db)

    def create_review(self, user_id: int, data: ReviewCreate) -> Review:
        """
        Create a review and automatically predict sentiment from review text.

        Steps:
            1. Validate event exists and is active
            2. Enforce 1 review per user per event (409 if duplicate)
            3. Predict sentiment using SentimentModel (if loaded)
            4. Persist review with sentiment data
            5. Return review with nested user info

        Args:
            user_id: Authenticated user's ID
            data:    Validated ReviewCreate schema from router

        Returns:
            Created Review ORM instance (with user relationship loaded)

        Raises:
            HTTP 404 if event not found
            HTTP 409 if user already reviewed this event
        """
        # Step 1: Validate event exists
        event = self.event_repo.get_by_id(data.event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with id={data.event_id} not found",
            )

        # Step 2: Enforce 1 review per user per event
        existing = self.review_repo.get_by_user_and_event(user_id, data.event_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already reviewed this event",
            )

        # Step 3: Predict sentiment (graceful degradation if model not loaded)
        sentiment_label: str | None = None
        sentiment_confidence: float | None = None

        if sentiment_model.is_loaded():
            try:
                sentiment_label, sentiment_confidence = sentiment_model.predict(data.content)
                logger.info(
                    "Sentiment predicted for review (user=%d, event=%d): %s (%.3f)",
                    user_id, data.event_id, sentiment_label, sentiment_confidence,
                )
            except Exception as exc:
                # Never let ML failure block review creation
                logger.error("Sentiment prediction failed: %s", exc)
                sentiment_label = None
                sentiment_confidence = None
        else:
            logger.warning(
                "Sentiment model not loaded — review saved without sentiment label. "
                "Run: python training/train_sentiment.py"
            )

        # Step 4: Persist review
        review = self.review_repo.create(
            user_id=user_id,
            event_id=data.event_id,
            rating=data.rating,
            content=data.content,
            sentiment_label=sentiment_label,
            sentiment_confidence=sentiment_confidence,
        )

        return review
