"""
repositories/review_repository.py — Database access layer for Review.

Key design decisions:
    - 1 review per user per event (enforced by UNIQUE constraint in DB)
    - sentiment_label and sentiment_confidence updated by SentimentService
    - Eagerly loads User (for ReviewResponse.user field)
    - Provides sentiment aggregation query for GET /events/{id}/sentiment-summary
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case

from app.models.review import Review


class ReviewRepository:
    """Encapsulates all DB queries for the Review entity."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_event(self, event_id: int) -> list[Review]:
        """
        Get all reviews for an event, ordered by most recent first.
        Eagerly loads the associated User (for review attribution).
        """
        return (
            self.db.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.event_id == event_id)
            .order_by(Review.created_at.desc())
            .all()
        )

    def get_by_user(self, user_id: int) -> list[Review]:
        """Get all reviews written by a user, ordered by most recent."""
        return (
            self.db.query(Review)
            .filter(Review.user_id == user_id)
            .order_by(Review.created_at.desc())
            .all()
        )

    def get_by_user_and_event(self, user_id: int, event_id: int) -> Review | None:
        """
        Check if a user has already reviewed an event.
        Used to enforce 1 review per user per event rule.
        """
        return (
            self.db.query(Review)
            .filter(Review.user_id == user_id, Review.event_id == event_id)
            .first()
        )

    def get_sentiment_summary(self, event_id: int) -> dict:
        """
        Aggregate sentiment counts and average rating for an event.
        Used by GET /events/{id}/sentiment-summary.

        Returns a dict with keys:
            total, positive, neutral, negative, avg_rating
        """
        # Use case() for SQL Server compatibility
        # Generates: SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END)
        results = (
            self.db.query(
                func.count(Review.id).label("total"),
                func.sum(
                    case((Review.sentiment_label == "positive", 1), else_=0)
                ).label("positive"),
                func.sum(
                    case((Review.sentiment_label == "neutral", 1), else_=0)
                ).label("neutral"),
                func.sum(
                    case((Review.sentiment_label == "negative", 1), else_=0)
                ).label("negative"),
                func.avg(Review.rating).label("avg_rating"),
            )
            .filter(Review.event_id == event_id)
            .first()
        )

        total = results.total or 0
        positive = results.positive or 0
        neutral = results.neutral or 0
        negative = results.negative or 0
        avg_rating = float(results.avg_rating) if results.avg_rating else 0.0

        return {
            "total": total,
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "avg_rating": round(avg_rating, 2),
        }

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        user_id: int,
        event_id: int,
        rating: int,
        content: str,
        sentiment_label: str | None = None,
        sentiment_confidence: float | None = None,
    ) -> Review:
        """
        Create a new review.

    sentiment_label and sentiment_confidence are optional at creation time.
    They are populated by SentimentService before calling create().

        Returns:
            The created Review ORM instance with user relationship loaded.
        """
        review = Review(
            user_id=user_id,
            event_id=event_id,
            rating=rating,
            content=content,
            sentiment_label=sentiment_label,
            sentiment_confidence=sentiment_confidence,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)

        # Reload with user relationship for response serialization
        return (
            self.db.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.id == review.id)
            .first()
        )

    def update_sentiment(
        self,
        review_id: int,
        *,
        sentiment_label: str,
        sentiment_confidence: float,
    ) -> Review | None:
        """
        Update sentiment fields after ML prediction.
        Called by SentimentService after ML prediction.
        """
        review = self.db.query(Review).filter(Review.id == review_id).first()
        if not review:
            return None
        review.sentiment_label = sentiment_label
        review.sentiment_confidence = sentiment_confidence
        self.db.commit()
        self.db.refresh(review)
        return review
