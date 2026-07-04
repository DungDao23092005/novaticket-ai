"""
models/event.py — SQLAlchemy ORM model for Event.

Represents an event on the NovaTicket platform.
Events belong to a Category (Many-to-One).
Events receive user interactions and reviews (One-to-Many).

Table: events

Note on 'tags':
    Stored as comma-separated string (e.g., "music,outdoor,festival").
    This is intentional for this project scope — avoids a separate tags
    table while still enabling TF-IDF feature extraction for recommendations.
    The tag parsing is handled in the service/ML layer.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
    func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# TYPE_CHECKING: avoids circular imports at runtime
if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.interaction import UserInteraction
    from app.models.review import Review


class Event(Base):
    __tablename__ = "events"

    # ------------------------------------------------------------------
    # Composite table-level indexes (defined at bottom via __table_args__)
    # ------------------------------------------------------------------
    __table_args__ = (
        # Index for filtering upcoming events (most common query)
        Index("ix_events_start_date", "start_date"),
        # Index for filtering by category
        Index("ix_events_category_id", "category_id"),
    )

    # ------------------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------------------
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------
    title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        comment="Event title shown on listing and detail pages",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Full event description — used for TF-IDF content-based filtering",
    )
    category_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK to categories table — SET NULL if category is deleted",
    )
    venue: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        comment="Venue name or address",
    )
    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="City where the event takes place — used for location-based filtering",
    )
    start_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Event start date and time",
    )
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="Event end date and time (optional)",
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
        comment="Ticket price in VND (0 = free)",
    )
    capacity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Maximum number of attendees (NULL = unlimited)",
    )
    tags: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment=(
            "Comma-separated tags for content-based filtering "
            "(e.g., 'music,outdoor,festival'). "
            "Parsed by the ML training pipeline."
        ),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        comment="Soft delete flag — inactive events are hidden from listings",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.getdate(),
        comment="Timestamp when the event was created",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    category: Mapped["Category | None"] = relationship(
        "Category",
        back_populates="events",
        lazy="select",
    )
    interactions: Mapped[list["UserInteraction"]] = relationship(
        "UserInteraction",
        back_populates="event",
        lazy="select",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="event",
        lazy="select",
        cascade="all, delete-orphan",
    )

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        return f"<Event id={self.id} title={self.title!r}>"
