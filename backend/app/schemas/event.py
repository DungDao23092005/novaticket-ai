"""
schemas/event.py — Pydantic schemas for Event.

Schemas:
    EventResponse     — Full event detail (used by GET /events/{id})
    EventListItem     — Lightweight summary for paginated list views
    EventListResponse — Paginated wrapper for list of events

Note:
    CategoryResponse is imported from schemas/category.py (single source of truth).
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.category import CategoryResponse


class EventResponse(BaseModel):
    """
    Full event detail — returned by GET /events/{id}.
    Includes nested CategoryResponse for category info.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    category_id: int | None
    category: CategoryResponse | None
    venue: str | None
    city: str | None
    start_date: datetime
    end_date: datetime | None
    price: Decimal
    capacity: int | None
    tags: str | None
    is_active: bool
    created_at: datetime


class EventListItem(BaseModel):
    """
    Lightweight event summary — used in paginated list views.
    Fewer fields = faster serialization for large result sets.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: CategoryResponse | None
    venue: str | None
    city: str | None
    start_date: datetime
    price: Decimal
    tags: str | None


class EventListResponse(BaseModel):
    """
    Paginated list response for GET /events.

    Fields:
        items      — Current page of events
        total      — Total number of matching events (before pagination)
        page       — Current page number (1-indexed)
        page_size  — Number of items per page
        total_pages — Total pages given current page_size
    """
    items: list[EventListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
