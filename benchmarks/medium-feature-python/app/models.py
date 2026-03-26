"""SQLAlchemy ORM models for the Todo application.

All models inherit from ``Base`` (declared in :mod:`app.database`) and map to
SQLite tables.  Timestamps use timezone-aware UTC datetimes so that callers
never have to guess the zone.

Adding a new model
------------------
1.  Define the class here, inheriting from ``Base``.
2.  Run ``models.Base.metadata.create_all(bind=engine)`` (handled at startup).
3.  Create corresponding Pydantic schemas in ``app.schemas``.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    event,
)

from .database import Base


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Todo model
# ---------------------------------------------------------------------------


class Todo(Base):
    """Represents a single todo item.

    Attributes
    ----------
    id : int
        Auto-incrementing primary key.
    title : str
        Short summary of the task (max 200 characters).
    description : str | None
        Optional longer description / notes.
    completed : bool
        Whether the task has been finished.
    created_at : datetime
        UTC timestamp of when the todo was created.
    updated_at : datetime
        UTC timestamp of the most recent modification.
    """

    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def mark_complete(self) -> None:
        """Mark this todo as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark this todo as not completed."""
        self.completed = False

    @property
    def is_pending(self) -> bool:
        """Return ``True`` if the todo has not been completed."""
        return not self.completed

    @property
    def summary(self) -> str:
        """One-line summary useful for logging and debugging."""
        status = "✓" if self.completed else "○"
        return f"[{status}] {self.title}"

    def to_dict(self) -> dict:
        """Serialise the todo to a plain dictionary.

        Useful outside of Pydantic contexts (e.g. background tasks, logging).
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<Todo(id={self.id}, title={self.title!r}, "
            f"completed={self.completed})>"
        )

    def __str__(self) -> str:
        return self.summary


# ---------------------------------------------------------------------------
# Model-level event listeners
# ---------------------------------------------------------------------------


@event.listens_for(Todo, "before_update")
def _todo_before_update(mapper, connection, target):
    """Ensure ``updated_at`` is refreshed on every UPDATE.

    SQLAlchemy's ``onupdate`` only fires when the column itself is part
    of the SET clause.  This listener guarantees the timestamp is always
    current, even for in-place attribute mutations.
    """
    target.updated_at = _utcnow()
