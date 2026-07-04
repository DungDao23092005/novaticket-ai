"""
models/category.py — SQLAlchemy ORM model for Category.

Represents event categories (e.g., Music, Sports, Technology).
Each Event belongs to one Category (Many-to-One).

Table: categories
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# TYPE_CHECKING: avoids circular imports at runtime
# Only used by type checkers (mypy, pyright) and IDEs
if TYPE_CHECKING:
    from app.models.event import Event


class Category(Base):
    __tablename__ = "categories"

    # ------------------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------------------
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Category name (e.g., Music, Sports, Technology)",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description of the category",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.getdate(),
        comment="Timestamp when category was created",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    events: Mapped[list["Event"]] = relationship(
        "Event",
        back_populates="category",
        lazy="select",  # Load events only when explicitly accessed
    )

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name!r}>"
