"""
repositories/event_repository.py — Database access layer for Event.

Supports:
    - Listing events with optional filters (category, city, search)
    - Pagination (skip/limit)
    - Count query (for computing total_pages)
    - Fetch by ID
"""

import math
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.models.event import Event
from app.models.category import Category


class EventRepository:
    """Encapsulates all DB queries for the Event entity."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, event_id: int) -> Event | None:
        """
        Fetch a single event by ID with category eagerly loaded.
        Returns None if not found or if event is inactive.
        """
        return (
            self.db.query(Event)
            .options(joinedload(Event.category))
            .filter(Event.id == event_id, Event.is_active == True)
            .first()
        )

    def get_list(
        self,
        *,
        category_id: int | None = None,
        city: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Event], int, int]:
        """
        Fetch paginated events with optional filters.

        Filters:
            category_id — Filter by category FK
            city        — Filter by city (case-insensitive partial match)
            search      — Search in title and description (case-insensitive)

        Returns:
            (events, total_count, total_pages) tuple

        Args:
            page      — 1-indexed page number
            page_size — Items per page (max enforced by caller/router)
        """
        query = (
            self.db.query(Event)
            .options(joinedload(Event.category))
            .filter(Event.is_active == True)
        )

        # Apply filters
        if category_id is not None:
            query = query.filter(Event.category_id == category_id)

        if city is not None:
            # Case-insensitive LIKE — SQL Server uses NVARCHAR, LIKE is case-insensitive by default
            query = query.filter(Event.city.ilike(f"%{city}%"))

        if search is not None:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Event.title.ilike(search_term),
                    Event.description.ilike(search_term),
                )
            )

        # Get total before applying pagination
        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        # Apply ordering and pagination
        offset = (page - 1) * page_size
        events = (
            query
            .order_by(Event.start_date.asc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return events, total, total_pages
