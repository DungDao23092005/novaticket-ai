"""
routers/events.py — Event listing and detail endpoints.

Pattern: Thin router — delegates all DB queries to EventRepository.

Endpoints:
    GET /events           — Paginated event list with optional filters
    GET /events/{id}      — Full event detail by ID

Query parameters for GET /events:
    category_id  — Filter by category (int)
    city         — Filter by city (partial match, case-insensitive)
    search       — Search in title and description
    page         — Page number, 1-indexed (default: 1)
    page_size    — Items per page (default: 20, max: 100)

Both endpoints are public — no authentication required.
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventListResponse, EventResponse

router = APIRouter(prefix="/events", tags=["Events"])


# ----------------------------------------------------------------------
# POST /events/batch — get multiple events by IDs
# ----------------------------------------------------------------------
@router.post(
    "/batch",
    response_model=list[EventResponse],
    summary="Get multiple events by IDs",
)
def get_events_batch(
    ids: list[int] = Body(..., description="Array of event IDs to fetch"),
    db: Session = Depends(get_db),
) -> list[EventResponse]:
    """
    Returns a list of active events matching the given IDs.
    IDs not found or inactive are omitted from the result.
    """
    repo = EventRepository(db)
    return repo.get_by_ids(ids)


# ----------------------------------------------------------------------
# GET /events
# ----------------------------------------------------------------------
@router.get(
    "",
    response_model=EventListResponse,
    summary="List events with optional filters and pagination",
)
def list_events(
    category_id: int | None = Query(default=None, description="Filter by category ID"),
    city: str | None = Query(default=None, description="Filter by city (partial match)"),
    search: str | None = Query(default=None, description="Search in title and description"),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    db: Session = Depends(get_db),
) -> EventListResponse:
    """
    Returns a paginated list of active events.

    **Filters** (all optional, combinable):
    - `category_id`: Show only events in this category
    - `city`: Partial city name match (e.g. `hanoi` matches `Hanoi`)
    - `search`: Search across event title and description

    **Pagination**:
    - `page`: Starting from 1
    - `page_size`: 1–100 items per page (default 20)

    **Ordering**: Events are sorted by `start_date` ascending (soonest first).
    """
    repo = EventRepository(db)
    events, total, total_pages = repo.get_list(
        category_id=category_id,
        city=city,
        search=search,
        page=page,
        page_size=page_size,
    )

    return EventListResponse(
        items=events,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ----------------------------------------------------------------------
# GET /events/{event_id}
# ----------------------------------------------------------------------
@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Get event detail by ID",
)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
) -> EventResponse:
    """
    Returns the full detail of a single event, including nested category info.

    Returns **404** if the event does not exist or is inactive.
    """
    repo = EventRepository(db)
    event = repo.get_by_id(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id={event_id} not found",
        )

    return event
