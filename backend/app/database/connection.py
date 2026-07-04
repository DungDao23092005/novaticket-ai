"""
database/connection.py — SQLAlchemy engine, session factory, and FastAPI dependency.

Design decisions:
- Single engine instance shared across all requests (connection pooling).
- Session-per-request pattern via FastAPI dependency injection.
- pool_pre_ping=True: validates connections before use (critical for SQL Server).
- pool_recycle=3600: recycle connections every hour to avoid server-side timeout.

Usage in router:
    from app.database.connection import get_db
    from sqlalchemy.orm import Session

    @router.get("/example")
    def example(db: Session = Depends(get_db)):
        result = db.execute(text("SELECT 1"))
        ...
"""

from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings


# ----------------------------------------------------------------------
# Engine — created once at module load time
# Connection string comes from settings.database_url (never hardcoded)
# ----------------------------------------------------------------------
engine = create_engine(
    settings.database_url,
    # pool_pre_ping: execute a lightweight query before using a pooled
    # connection to detect stale/dropped connections (important for SQL Server)
    pool_pre_ping=True,
    # pool_recycle: recycle connections older than 1 hour to avoid
    # SQL Server's idle connection timeout cutting them
    pool_recycle=3600,
    # echo: log all SQL statements — only in debug mode
    echo=settings.debug,
    # pool_size: number of persistent connections kept in pool
    pool_size=5,
    # max_overflow: additional connections allowed beyond pool_size
    max_overflow=10,
)

# ----------------------------------------------------------------------
# Session Factory
# autocommit=False: transactions must be committed explicitly
# autoflush=False: don't flush automatically before queries
# ----------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
)


# ----------------------------------------------------------------------
# FastAPI Dependency — Session per Request
# ----------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    Yields a database session for a single request.

    Pattern:
        try:
            yield session   ← request runs here
        finally:
            session.close() ← always closes, even if exception

    The session is automatically closed after the request completes
    (whether successful or not), returning the connection to the pool.

    Usage:
        @router.get("/users")
        def get_users(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    Test database connectivity.
    Used during application startup to fail fast if DB is unreachable.
    Returns True if connection succeeds, raises exception otherwise.
    """
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
