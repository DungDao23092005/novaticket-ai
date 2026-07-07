"""
routers/recommendations.py — Endpoints for event recommendations.

Provides:
- GET /recommendations/me: Personalized hybrid recommendations for the logged-in user.
- GET /recommendations/events/{event_id}/similar: Content-based similar events.
"""

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.dependencies import get_current_user
from app.schemas.user import UserResponse
from app.schemas.event import EventResponse
from app.services.recommendation_service import RecommendationService


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/me",
    response_model=list[EventResponse],
    summary="Get personalized event recommendations",
    description=(
        "Returns a list of recommended events for the currently authenticated user. "
        "Uses Hybrid ML (Content-Based + Collaborative Filtering) if user has interactions. "
        "Falls back to newest active events if user is new (Cold Start)."
    ),
)
def get_my_recommendations(
    top_k: int = Query(
        5, ge=1, le=20, description="Number of recommendations to return"
    ),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns personalized recommendations.
    """
    service = RecommendationService(db)
    # user_id is accessed via current_user.id
    recommended_events = service.get_recommendations_for_user(
        user_id=current_user.id, top_k=top_k
    )
    return recommended_events


@router.get(
    "/events/{event_id}/similar",
    response_model=list[EventResponse],
    summary="Get similar events",
    description="Returns a list of events similar to the given event ID using Content-Based ML.",
)
def get_similar_events(
    event_id: int = Path(..., title="The ID of the event"),
    top_k: int = Query(4, ge=1, le=10, description="Number of similar events to return"),
    db: Session = Depends(get_db),
):
    """
    Returns similar events for a specific event.
    """
    service = RecommendationService(db)
    similar_events = service.get_similar_events(event_id=event_id, top_k=top_k)
    return similar_events
