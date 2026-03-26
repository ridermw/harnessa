"""FastAPI application — Todo API.

Provides CRUD operations for todo items with filtering, searching,
pagination, batch operations, and basic statistics.

Start the server with::

    uvicorn app.main:app --reload

The interactive Swagger docs are available at ``/docs`` and ReDoc at ``/redoc``.
"""

import logging
import time
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from . import models, schemas
from .database import engine, get_db

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bootstrap — create tables on startup
# ---------------------------------------------------------------------------

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Todo API",
    description=(
        "A simple but complete TODO application built with FastAPI and SQLite. "
        "Supports CRUD, filtering, full-text search, pagination, batch "
        "operations, and aggregate statistics."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Attach an ``X-Process-Time`` header to every response."""
    start = time.perf_counter()
    response: Response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}"
    return response


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Catch database integrity errors and return a clean 409."""
    logger.warning("IntegrityError: %s", exc.orig)
    return JSONResponse(
        status_code=409,
        content={"detail": "Database integrity error — possible duplicate."},
    )


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _get_todo_or_404(todo_id: int, db: Session) -> models.Todo:
    """Fetch a todo by primary key or raise 404."""
    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(
            status_code=404,
            detail=f"Todo with id {todo_id} not found",
        )
    return todo


# ---------------------------------------------------------------------------
# Utility endpoints
# ---------------------------------------------------------------------------


@app.get(
    "/",
    response_model=schemas.MessageResponse,
    summary="API root",
)
def root():
    """Root endpoint — returns basic API information."""
    return {"message": "Welcome to the Todo API", "version": "1.0.0"}


@app.get(
    "/health",
    response_model=schemas.HealthResponse,
    summary="Health check",
)
def health_check():
    """Health-check endpoint used by load balancers and monitoring."""
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Stats — registered BEFORE ``/todos/{todo_id}`` to avoid path conflict
# ---------------------------------------------------------------------------


@app.get(
    "/todos/stats/summary",
    response_model=schemas.TodoStatsResponse,
    summary="Todo statistics",
)
def get_todos_stats(db: Session = Depends(get_db)):
    """Return aggregate counts and completion rate for all todos.

    Response shape::

        {
            "total": 10,
            "completed": 4,
            "pending": 6,
            "completion_rate": 40.0
        }
    """
    total: int = db.query(func.count(models.Todo.id)).scalar() or 0
    completed: int = (
        db.query(func.count(models.Todo.id))
        .filter(models.Todo.completed.is_(True))
        .scalar()
    ) or 0
    pending = total - completed
    completion_rate = round((completed / total) * 100, 2) if total > 0 else 0.0

    return schemas.TodoStatsResponse(
        total=total,
        completed=completed,
        pending=pending,
        completion_rate=completion_rate,
    )


# ---------------------------------------------------------------------------
# CRUD — Create
# ---------------------------------------------------------------------------


@app.post(
    "/todos",
    response_model=schemas.TodoResponse,
    status_code=201,
    summary="Create a todo",
    responses={
        201: {"description": "Todo created successfully"},
        422: {"description": "Validation error"},
    },
)
def create_todo(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo item.

    The ``title`` field is required and must be between 1 and 200 characters.
    ``description`` is optional.  ``completed`` defaults to ``False``.
    """
    db_todo = models.Todo(
        title=todo.title,
        description=todo.description,
    )
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    logger.info("Created todo id=%d title=%r", db_todo.id, db_todo.title)
    return db_todo


# ---------------------------------------------------------------------------
# CRUD — Read (list)
# ---------------------------------------------------------------------------


@app.get(
    "/todos",
    response_model=schemas.TodoListResponse,
    summary="List todos",
)
def list_todos(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum items to return"),
    completed: Optional[bool] = Query(
        None, description="Filter by completion status"
    ),
    search: Optional[str] = Query(
        None,
        min_length=1,
        max_length=200,
        description="Case-insensitive search in title and description",
    ),
    db: Session = Depends(get_db),
):
    """List todos with optional pagination, filtering, and search.

    Query parameters
    ----------------
    skip : int
        Offset for pagination (default ``0``).
    limit : int
        Maximum results per page (default ``100``, max ``500``).
    completed : bool | None
        If supplied, return only todos matching this completion status.
    search : str | None
        Case-insensitive substring search across ``title`` and ``description``.

    The ``total`` field in the response reflects the count **after** filtering
    but **before** pagination, so the client can compute the number of pages.
    """
    query = db.query(models.Todo)

    # ---- completed filter ------------------------------------------------
    if completed is not None:
        query = query.filter(models.Todo.completed.is_(completed))

    # ---- search ----------------------------------------------------------
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Todo.title.ilike(search_term),
                models.Todo.description.ilike(search_term),
            )
        )

    total = query.count()

    todos = (
        query.order_by(models.Todo.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return schemas.TodoListResponse(todos=todos, total=total)


# ---------------------------------------------------------------------------
# CRUD — Read (single)
# ---------------------------------------------------------------------------


@app.get(
    "/todos/{todo_id}",
    response_model=schemas.TodoResponse,
    summary="Get a todo",
    responses={404: {"model": schemas.ErrorResponse}},
)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """Retrieve a single todo by its ID.

    Returns 404 if the todo does not exist.
    """
    return _get_todo_or_404(todo_id, db)


# ---------------------------------------------------------------------------
# CRUD — Update
# ---------------------------------------------------------------------------


@app.put(
    "/todos/{todo_id}",
    response_model=schemas.TodoResponse,
    summary="Update a todo",
    responses={
        404: {"model": schemas.ErrorResponse},
        400: {"model": schemas.ErrorResponse},
    },
)
def update_todo(
    todo_id: int,
    todo_update: schemas.TodoUpdate,
    db: Session = Depends(get_db),
):
    """Partially update an existing todo.

    Only the fields present in the request body will be modified.  Sending an
    empty body returns **400 Bad Request**.
    """
    todo = _get_todo_or_404(todo_id, db)

    update_data = todo_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update",
        )

    for field, value in update_data.items():
        setattr(todo, field, value)

    db.commit()
    db.refresh(todo)
    logger.info("Updated todo id=%d fields=%s", todo.id, list(update_data))
    return todo


# ---------------------------------------------------------------------------
# CRUD — Delete
# ---------------------------------------------------------------------------


@app.delete(
    "/todos/{todo_id}",
    status_code=204,
    summary="Delete a todo",
    responses={404: {"model": schemas.ErrorResponse}},
)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo by its ID.

    Returns **204 No Content** on success.
    """
    todo = _get_todo_or_404(todo_id, db)
    db.delete(todo)
    db.commit()
    logger.info("Deleted todo id=%d", todo_id)
    return None


# ---------------------------------------------------------------------------
# Batch operations
# ---------------------------------------------------------------------------


@app.post(
    "/todos/batch",
    response_model=schemas.TodoListResponse,
    status_code=201,
    summary="Create multiple todos",
)
def create_todos_batch(
    todos: list[schemas.TodoCreate],
    db: Session = Depends(get_db),
):
    """Create several todos in a single request.

    Accepts a JSON array of todo objects.  All items are inserted in a single
    transaction — if any item fails validation, none are persisted.

    Returns the list of created todos and the count.
    """
    if not todos:
        raise HTTPException(status_code=400, detail="Empty todo list")

    if len(todos) > 50:
        raise HTTPException(
            status_code=400,
            detail="Batch size exceeds maximum of 50 items",
        )

    db_todos = []
    for item in todos:
        db_todo = models.Todo(title=item.title, description=item.description)
        db.add(db_todo)
        db_todos.append(db_todo)

    db.commit()
    for t in db_todos:
        db.refresh(t)

    logger.info("Batch-created %d todos", len(db_todos))
    return schemas.TodoListResponse(todos=db_todos, total=len(db_todos))


@app.post(
    "/todos/batch/complete",
    response_model=schemas.TodoListResponse,
    summary="Mark multiple todos as completed",
)
def batch_complete_todos(
    todo_ids: list[int],
    db: Session = Depends(get_db),
):
    """Mark a list of todos as completed in one request.

    Todos that are already completed are left unchanged.  IDs that do not
    exist are silently skipped.
    """
    if not todo_ids:
        raise HTTPException(status_code=400, detail="Empty id list")

    todos = (
        db.query(models.Todo)
        .filter(models.Todo.id.in_(todo_ids))
        .all()
    )

    for todo in todos:
        todo.completed = True

    db.commit()
    for todo in todos:
        db.refresh(todo)

    logger.info("Batch-completed %d todos", len(todos))
    return schemas.TodoListResponse(todos=todos, total=len(todos))
