"""
database/base.py — SQLAlchemy Declarative Base.

All ORM models must inherit from this Base class.
SQLAlchemy uses Base.metadata to track all registered tables,
which Alembic then uses to generate migrations.

Usage:
    from app.database.base import Base

    class User(Base):
        __tablename__ = "users"
        ...

IMPORTANT:
- This file must NOT import from models/ (circular import risk).
- All model files must be imported in migrations/env.py so Alembic
  can detect them during autogenerate.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    Inheriting from DeclarativeBase (SQLAlchemy 2.0 style)
    instead of the legacy declarative_base() function.
    """
    pass
