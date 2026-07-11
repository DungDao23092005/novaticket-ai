"""
schemas/review.py — Pydantic schemas for Review.

Schemas:
    ReviewCreate       — request body for POST /reviews
    ReviewResponse     — full review data returned by API
    SentimentSummary   — aggregated sentiment stats per event (S5-P5)

Note on sentiment fields:
    sentiment_label and sentiment_confidence are NOT in ReviewCreate.
    They are set by the backend (SentimentService) after the review is submitted.
    Clients cannot submit their own sentiment label.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserPublic

# Sentiment labels — must match CHECK constraint in ORM model
SentimentLabel = Literal["positive", "neutral", "negative"]


class ReviewCreate(BaseModel):
    """Request body for POST /reviews."""
    event_id: int = Field(..., description="ID of the event being reviewed")
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Star rating from 1 (worst) to 5 (best)",
        examples=[4],
    )
    content: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Review text (min 10 characters)",
        examples=["Amazing event! The speakers were incredibly insightful."],
    )


class ReviewResponse(BaseModel):
    """Full review data returned by API endpoints."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    event_id: int
    rating: int
    content: str
    sentiment_label: str | None      # Set by SentimentService
    sentiment_confidence: float | None  # Model confidence score
    created_at: datetime
    user: UserPublic | None          # Nested user info (username only, no email)


class SentimentSummary(BaseModel):
    """
    Aggregated sentiment statistics for an event.
    Returned by GET /events/{id}/sentiment-summary.
    """
    event_id: int
    total_reviews: int
    positive_count: int
    neutral_count: int
    negative_count: int
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    average_rating: float
