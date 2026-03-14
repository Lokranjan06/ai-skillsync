"""
app/database/session.py
-----------------------
Database engine and session factory.

SQLite is used by default (file: skillsync.db in the project root).
Switch to PostgreSQL by setting DATABASE_URL in your .env file:

    DATABASE_URL=postgresql+psycopg2://user:pass@localhost/skillsync

The session dependency (get_db) is injected into every route that needs
database access — never instantiate SessionLocal directly in route handlers.
"""

from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

_settings = get_settings()
DATABASE_URL: str = _settings.DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=_settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=1800,
)

# Enable WAL mode for SQLite
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

logger.info("Database engine created: %s", DATABASE_URL.split("@")[-1])

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ---------------------------------------------------------------------------
# Declarative base (shared by all models)
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Dependency — injected into every route that needs a DB session
# ---------------------------------------------------------------------------

def get_db():
    """
    FastAPI dependency that yields a SQLAlchemy session and guarantees
    it is closed after the request finishes — even on exception.
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
