"""
migrations/env.py — Alembic migration environment configuration.

This file is executed by Alembic when running migration commands.
It connects Alembic to our:
  1. Database (via app settings → database_url)
  2. ORM models (via Base.metadata import)

FIX NOTE:
  We do NOT use config.set_main_option("sqlalchemy.url", ...) because
  Python's configparser (used internally by Alembic) interprets % as
  interpolation syntax. URL-encoded passwords like %40 (for @) or %21 (for !)
  would cause "invalid interpolation syntax" errors.

  Solution: Create the SQLAlchemy engine DIRECTLY from settings.database_url,
  bypassing configparser entirely.
"""

from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context

# ----------------------------------------------------------------------
# Load our application settings (reads from backend/.env)
# ----------------------------------------------------------------------
from app.core.config import settings

# ----------------------------------------------------------------------
# Import Base — Alembic needs Base.metadata for autogenerate
# ----------------------------------------------------------------------
from app.database.base import Base

# ----------------------------------------------------------------------
# CRITICAL: Import ALL models so their tables are registered in metadata.
# If a model is not imported here, Alembic won't detect its table
# and will NOT generate a migration for it.
# ----------------------------------------------------------------------
import app.models  # noqa: F401 — side effect import, registers all tables

# ----------------------------------------------------------------------
# Alembic Config object — provides access to .ini file values
# ----------------------------------------------------------------------
config = context.config

# ----------------------------------------------------------------------
# Configure logging from alembic.ini [loggers] section
# ----------------------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ----------------------------------------------------------------------
# Target metadata for autogenerate
# Alembic compares this metadata against the actual DB schema
# ----------------------------------------------------------------------
target_metadata = Base.metadata

# NOTE: We intentionally do NOT call config.set_main_option("sqlalchemy.url", ...)
# here because configparser misinterprets % in URL-encoded passwords.
# Instead, we pass the URL directly to create_engine() in the functions below.


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode (generates SQL without connecting).
    Usage: alembic upgrade head --sql
    """
    context.configure(
        url=settings.database_url,  # Pass URL directly — bypasses configparser
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode (connects to DB and applies migrations).
    Usage: alembic upgrade head
    """
    # Create engine directly from settings — bypasses configparser % issue
    connectable = create_engine(
        settings.database_url,
        poolclass=pool.NullPool,  # NullPool: no connection reuse in migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=False,
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ----------------------------------------------------------------------
# Entry point — Alembic calls this file directly
# ----------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
