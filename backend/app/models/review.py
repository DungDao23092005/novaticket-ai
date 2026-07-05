"""
models/review.py — SQLAlchemy ORM model for Review.

Stores user reviews for events. Each review contains:
- A numeric rating (1-5)
- A text review (used for sentiment analysis)
- Sentiment label + confidence (populated by the ML sentiment model)

Table: reviews

Key constraints:
- UNIQUE(user_id, event_id): one review per user per event
- CHECK rating BETWEEN 1 AND 5
- CHECK sentiment_label IN ('positive', 'neutral', 'negative')

Sentiment flow:
    User submits review text
    → ReviewService calls SentimentService.predict(text)
    → Returns label + confidence
    → Both saved together with the review in one DB write
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    Float,
    String,
    Text,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.event import Event

# Valid sentiment labels produced by the ML model
SENTIMENT_LABELS = ("positive", "neutral", "negative")


class Review(Base):
    __tablename__ = "reviews"

    # ------------------------------------------------------------------
    # Table-level constraints and indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        # One review per user per event — enforced at DB level
        UniqueConstraint("user_id", "event_id", name="uq_review_user_event"),
        # Enforce valid rating values
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating"),
        # Enforce valid sentiment labels (NULL allowed before ML prediction)
        CheckConstraint(
            "sentiment_label IS NULL OR sentiment_label IN ('positive', 'neutral', 'negative')",
            name="ck_review_sentiment_label",
        ),
        # Index for fetching all reviews of an event (sentiment summary)
        Index("ix_reviews_event_id", "event_id"),
        # Index for fetching all reviews by a user (dashboard)
        Index("ix_reviews_user_id", "user_id"),
    )

    # ------------------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------------------
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to users — delete reviews when user is deleted",
    )
    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to events — delete reviews when event is deleted",
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Numeric rating from 1 (worst) to 5 (best)",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Review text — input for sentiment analysis ML model",
    )
    sentiment_label: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment=(
            "ML model prediction: positive | neutral | negative. "
            "NULL if model has not run yet or prediction failed."
        ),
    )
    sentiment_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment=(
            "Confidence score of the sentiment prediction (0.0–1.0). "
            "NULL if sentiment_label is NULL."
        ),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.getdate(),
        comment="When the review was submitted",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship(
        "User",
        back_populates="reviews",
        lazy="select",
    )
    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="reviews",
        lazy="select",
    )

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        return (
            f"<Review id={self.id} "
            f"user_id={self.user_id} "
            f"event_id={self.event_id} "
            f"rating={self.rating} "
            f"sentiment={self.sentiment_label!r}>"
        )
