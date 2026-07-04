"""
models/user.py — SQLAlchemy ORM model for User.

Represents a registered user on the NovaTicket platform.
Users can write reviews and have interaction history tracked.

Table: users

IMPORTANT: This model stores hashed_password, NEVER plaintext password.
Password hashing is handled in core/security.py.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# TYPE_CHECKING: avoids circular imports at runtime
if TYPE_CHECKING:
    from app.models.interaction import UserInteraction
    from app.models.review import Review


class User(Base):
    __tablename__ = "users"

    # ------------------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------------------
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address — used for login, must be unique",
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Display username — must be unique",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt-hashed password — NEVER store plaintext",
    )
    full_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Optional full name for display purposes",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        comment="Soft delete / account activation flag",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.getdate(),
        comment="Account creation timestamp",
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=func.getdate(),
        comment="Last profile update timestamp",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    interactions: Mapped[list["UserInteraction"]] = relationship(
        "UserInteraction",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",  # Delete interactions when user is deleted
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",  # Delete reviews when user is deleted
    )

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} username={self.username!r}>"
