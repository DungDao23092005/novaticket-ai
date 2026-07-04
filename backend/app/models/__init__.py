"""
models/__init__.py — Exports all SQLAlchemy ORM models.

IMPORTANT: All models must be imported here so that:
1. SQLAlchemy knows about all tables via Base.metadata
2. Alembic autogenerate can detect all tables for migrations

Add new models here as they are created in each sprint.
"""

from app.models.category import Category
from app.models.user import User
from app.models.event import Event

# Sprint 1 Part 3 will add:
# from app.models.interaction import UserInteraction
# from app.models.review import Review

__all__ = [
    "Category",
    "User",
    "Event",
]
