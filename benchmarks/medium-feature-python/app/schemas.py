"""Pydantic v2 schemas for request / response validation.

Each schema is deliberately narrow — it validates *exactly* the shape of the
JSON that the corresponding endpoint expects or returns.  This makes it easy
to spot breaking changes when new features are added later.

Naming conventions
------------------
- ``*Create``  — request body for POST endpoints.
- ``*Update``  — request body for PUT / PATCH endpoints (all fields optional).
- ``*Response`` — response body (includes server-generated fields like ``id``).
- ``*ListResponse`` — paginated wrapper around a list of response objects.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Todo schemas
# ---------------------------------------------------------------------------


class TodoBase(BaseModel):
    """Shared fields used when creating or reading a todo."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Short summary of the task",
        examples=["Buy groceries"],
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional detailed notes about the task",
        examples=["Milk, eggs, bread, and butter"],
    )


class TodoCreate(TodoBase):
    """Request body for ``POST /todos``.

    Only ``title`` is required; ``description`` defaults to ``None``.
    """

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must contain non-whitespace characters")
        return v.strip()


class TodoUpdate(BaseModel):
    """Request body for ``PUT /todos/{id}``.

    All fields are optional — only the supplied fields will be updated.
    Sending an empty body is considered a client error (400).
    """

    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="New title for the todo",
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="New description (pass explicit null to clear)",
    )
    completed: Optional[bool] = Field(
        None,
        description="Set completion status",
    )

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Title must contain non-whitespace characters")
        return v.strip() if v else v


class TodoResponse(TodoBase):
    """Full representation of a todo returned by the API.

    Includes all server-generated fields (``id``, timestamps).
    """

    id: int
    completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TodoListResponse(BaseModel):
    """Paginated list of todos.

    ``total`` reflects the *filtered* count (before pagination), so the client
    knows how many pages exist.
    """

    todos: list[TodoResponse]
    total: int


class TodoStatsResponse(BaseModel):
    """Aggregate statistics about all todos in the system."""

    total: int = Field(..., description="Total number of todos")
    completed: int = Field(..., description="Number of completed todos")
    pending: int = Field(..., description="Number of pending (incomplete) todos")
    completion_rate: float = Field(
        ...,
        description="Percentage of todos completed (0.0–100.0)",
        ge=0.0,
        le=100.0,
    )


# ---------------------------------------------------------------------------
# Generic response helpers
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Standard error envelope returned for 4xx / 5xx responses."""

    detail: str = Field(..., description="Human-readable error message")


class MessageResponse(BaseModel):
    """Simple message response used by utility endpoints."""

    message: str
    version: Optional[str] = None


class HealthResponse(BaseModel):
    """Response shape for the ``/health`` endpoint."""

    status: str = Field(..., examples=["healthy"])
