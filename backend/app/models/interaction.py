"""
models/interaction.py — SQLAlchemy ORM model for UserInteraction.

Tracks user behavior on the platform. This data feeds the
Collaborative Filtering recommendation engine.

Interaction types and their implicit scores:
    view      = 1.0  — user viewed event listing
    click     = 2.0  — user clicked into event detail
    favorite  = 3.0  — user saved/favorited the event
    register  = 5.0  — user registered for the event (strongest signal)

Table: user_interactions

Design note:
    We allow multiple interactions of the same type from the same user
    on the same event (e.g., viewing an event 3 times = 3 view rows).
    The CF model aggregates these scores per (user_id, event_id) pair.
    This gives richer signal than just recording "viewed once".
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.event import Event

# Valid interaction types and their default scores
INTERACTION_SCORES: dict[str, float] = {
    "view": 1.0,
    "click": 2.0,
    "favorite": 3.0,
    "register": 5.0,
}


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    # ------------------------------------------------------------------
    # Table-level constraints and indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        # Enforce valid interaction types at DB level
        CheckConstraint(
            "interaction_type IN ('view', 'click', 'favorite', 'register')",
            name="ck_interaction_type",
        ),
        # Composite index for CF matrix queries: "all interactions by user"
        # and "all interactions on event"
        Index("ix_user_interactions_user_event", "user_id", "event_id"),
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
        comment="FK to users — delete interactions when user is deleted",
    )
    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to events — delete interactions when event is deleted",
    )
    interaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of interaction: view | click | favorite | register",
    )
    interaction_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
        server_default="1.0",
        comment=(
            "Implicit feedback score: view=1.0, click=2.0, "
            "favorite=3.0, register=5.0"
        ),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.getdate(),
        comment="When the interaction occurred",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship(
        "User",
        back_populates="interactions",
        lazy="select",
    )
    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="interactions",
        lazy="select",
    )

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        return (
            f"<UserInteraction id={self.id} "
            f"user_id={self.user_id} "
            f"event_id={self.event_id} "
            f"type={self.interaction_type!r}>"
        )
