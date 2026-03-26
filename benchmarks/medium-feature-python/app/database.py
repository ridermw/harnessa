"""Database configuration and session management.

This module centralises all database-related setup so that the rest of the
application can import ``engine``, ``SessionLocal``, ``Base``, and the
``get_db`` FastAPI dependency without worrying about connection details.

The default database URL points to a local SQLite file (``todos.db``).
Override by setting the ``DATABASE_URL`` environment variable.
"""

import os
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todos.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=bool(os.getenv("SQL_ECHO")),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ---------------------------------------------------------------------------
# SQLite pragmas — enable WAL mode and foreign keys for better concurrency
# ---------------------------------------------------------------------------

@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    """Configure SQLite pragmas on every new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_db():
    """FastAPI dependency that yields a database session.

    Usage::

        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            ...

    The session is automatically closed when the request finishes, even if
    an unhandled exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context-manager variant of ``get_db`` for use outside of FastAPI.

    Useful in CLI scripts, background jobs, or tests::

        with get_db_context() as db:
            todos = db.query(Todo).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Create all tables defined on ``Base``.

    Idempotent — safe to call multiple times.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created (or already exist).")
