"""Tests for the Todo API.

Uses an in-memory SQLite database so that each test session starts with a
clean slate and no on-disk artefacts are produced.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# Test database setup
# ---------------------------------------------------------------------------

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test and drop them afterwards."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_todo(
    title: str = "Test todo",
    description: str | None = None,
) -> dict:
    """Shortcut to create a todo and return the JSON response."""
    payload: dict = {"title": title}
    if description is not None:
        payload["description"] = description
    response = client.post("/todos", json=payload)
    assert response.status_code == 201
    return response.json()


def _create_multiple_todos(count: int = 5) -> list[dict]:
    """Create *count* todos with predictable titles and return them."""
    todos = []
    for i in range(count):
        todo = _create_todo(f"Todo item {i}", f"Description for item {i}")
        todos.append(todo)
    return todos


# =========================================================================
# Tests — utility endpoints
# =========================================================================


class TestUtilityEndpoints:
    """Tests for root, health, and other utility routes."""

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to the Todo API"
        assert data["version"] == "1.0.0"

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_root_returns_json_content_type(self):
        response = client.get("/")
        assert "application/json" in response.headers["content-type"]

    def test_process_time_header_present(self):
        response = client.get("/health")
        assert "x-process-time" in response.headers


# =========================================================================
# Tests — create
# =========================================================================


class TestCreateTodo:
    """Tests for ``POST /todos``."""

    def test_create_todo(self):
        response = client.post("/todos", json={"title": "Buy milk"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Buy milk"
        assert data["description"] is None
        assert data["completed"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_todo_with_description(self):
        response = client.post(
            "/todos",
            json={"title": "Grocery run", "description": "Eggs, bread, cheese"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Grocery run"
        assert data["description"] == "Eggs, bread, cheese"

    def test_create_todo_missing_title(self):
        response = client.post("/todos", json={})
        assert response.status_code == 422

    def test_create_todo_empty_title(self):
        response = client.post("/todos", json={"title": ""})
        assert response.status_code == 422

    def test_create_todo_whitespace_only_title(self):
        response = client.post("/todos", json={"title": "   "})
        assert response.status_code == 422

    def test_create_todo_strips_whitespace_from_title(self):
        response = client.post("/todos", json={"title": "  Trimmed  "})
        assert response.status_code == 201
        assert response.json()["title"] == "Trimmed"

    def test_create_todo_title_max_length(self):
        long_title = "A" * 200
        response = client.post("/todos", json={"title": long_title})
        assert response.status_code == 201

        too_long = "A" * 201
        response = client.post("/todos", json={"title": too_long})
        assert response.status_code == 422

    def test_create_todo_returns_sequential_ids(self):
        t1 = _create_todo("First")
        t2 = _create_todo("Second")
        assert t2["id"] > t1["id"]

    def test_create_todo_defaults_completed_false(self):
        data = _create_todo("Check defaults")
        assert data["completed"] is False

    def test_create_todo_timestamps_populated(self):
        data = _create_todo("Timestamped")
        assert data["created_at"] is not None
        assert data["updated_at"] is not None


# =========================================================================
# Tests — list / get
# =========================================================================


class TestReadTodos:
    """Tests for ``GET /todos`` and ``GET /todos/{id}``."""

    def test_get_todos_empty(self):
        response = client.get("/todos")
        assert response.status_code == 200
        data = response.json()
        assert data["todos"] == []
        assert data["total"] == 0

    def test_get_todos_with_items(self):
        _create_todo("Alpha")
        _create_todo("Beta")
        _create_todo("Gamma")

        response = client.get("/todos")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["todos"]) == 3

    def test_get_todo_by_id(self):
        created = _create_todo("Specific item", "With a description")
        todo_id = created["id"]

        response = client.get(f"/todos/{todo_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == "Specific item"
        assert data["description"] == "With a description"

    def test_get_todo_not_found(self):
        response = client.get("/todos/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_todo_invalid_id_type(self):
        response = client.get("/todos/abc")
        assert response.status_code == 422

    def test_list_todos_returns_newest_first(self):
        _create_todo("First created")
        _create_todo("Second created")
        _create_todo("Third created")

        response = client.get("/todos")
        titles = [t["title"] for t in response.json()["todos"]]
        assert titles[0] == "Third created"

    def test_list_todos_response_shape(self):
        _create_todo("Shape test")
        response = client.get("/todos")
        data = response.json()

        assert "todos" in data
        assert "total" in data
        assert isinstance(data["todos"], list)
        assert isinstance(data["total"], int)

        todo = data["todos"][0]
        for key in ("id", "title", "completed", "created_at", "updated_at"):
            assert key in todo


# =========================================================================
# Tests — update
# =========================================================================


class TestUpdateTodo:
    """Tests for ``PUT /todos/{id}``."""

    def test_update_todo_title(self):
        created = _create_todo("Old title")
        todo_id = created["id"]

        response = client.put(f"/todos/{todo_id}", json={"title": "New title"})
        assert response.status_code == 200
        assert response.json()["title"] == "New title"

    def test_update_todo_completed(self):
        created = _create_todo("Finish report")
        todo_id = created["id"]

        response = client.put(f"/todos/{todo_id}", json={"completed": True})
        assert response.status_code == 200
        assert response.json()["completed"] is True

        # Verify persistence
        response = client.get(f"/todos/{todo_id}")
        assert response.json()["completed"] is True

    def test_update_todo_description(self):
        created = _create_todo("Needs description")
        todo_id = created["id"]

        response = client.put(
            f"/todos/{todo_id}", json={"description": "Now it has one"}
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Now it has one"

    def test_update_todo_multiple_fields(self):
        created = _create_todo("Original")
        todo_id = created["id"]

        response = client.put(
            f"/todos/{todo_id}",
            json={"title": "Updated", "completed": True, "description": "Done"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["completed"] is True
        assert data["description"] == "Done"

    def test_update_todo_not_found(self):
        response = client.put("/todos/99999", json={"title": "Nope"})
        assert response.status_code == 404

    def test_update_todo_empty_body(self):
        created = _create_todo("Won't change")
        response = client.put(f"/todos/{created['id']}", json={})
        assert response.status_code == 400

    def test_update_preserves_unset_fields(self):
        created = _create_todo("Keep me", "Also keep me")
        todo_id = created["id"]

        # Only update completed
        client.put(f"/todos/{todo_id}", json={"completed": True})

        response = client.get(f"/todos/{todo_id}")
        data = response.json()
        assert data["title"] == "Keep me"
        assert data["description"] == "Also keep me"
        assert data["completed"] is True


# =========================================================================
# Tests — delete
# =========================================================================


class TestDeleteTodo:
    """Tests for ``DELETE /todos/{id}``."""

    def test_delete_todo(self):
        created = _create_todo("To be deleted")
        todo_id = created["id"]

        response = client.delete(f"/todos/{todo_id}")
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/todos/{todo_id}")
        assert response.status_code == 404

    def test_delete_todo_not_found(self):
        response = client.delete("/todos/99999")
        assert response.status_code == 404

    def test_delete_todo_reduces_count(self):
        todos = _create_multiple_todos(3)
        client.delete(f"/todos/{todos[0]['id']}")

        response = client.get("/todos")
        assert response.json()["total"] == 2

    def test_delete_then_get_returns_404(self):
        created = _create_todo("Will be deleted")
        old_id = created["id"]
        client.delete(f"/todos/{old_id}")

        response = client.get(f"/todos/{old_id}")
        assert response.status_code == 404


# =========================================================================
# Tests — stats
# =========================================================================


class TestTodoStats:
    """Tests for ``GET /todos/stats/summary``."""

    def test_get_todos_stats(self):
        _create_todo("Task A")
        _create_todo("Task B")
        created_c = _create_todo("Task C")
        client.put(f"/todos/{created_c['id']}", json={"completed": True})

        response = client.get("/todos/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["completed"] == 1
        assert data["pending"] == 2
        assert data["completion_rate"] == pytest.approx(33.33, abs=0.01)

    def test_get_todos_stats_empty(self):
        response = client.get("/todos/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["completed"] == 0
        assert data["pending"] == 0
        assert data["completion_rate"] == 0.0

    def test_stats_all_completed(self):
        for title in ("A", "B", "C"):
            t = _create_todo(title)
            client.put(f"/todos/{t['id']}", json={"completed": True})

        data = client.get("/todos/stats/summary").json()
        assert data["total"] == 3
        assert data["completed"] == 3
        assert data["pending"] == 0
        assert data["completion_rate"] == 100.0

    def test_stats_reflects_deletes(self):
        t1 = _create_todo("Keep")
        t2 = _create_todo("Delete me")
        client.delete(f"/todos/{t2['id']}")

        data = client.get("/todos/stats/summary").json()
        assert data["total"] == 1


# =========================================================================
# Tests — filtering & search
# =========================================================================


class TestFilterAndSearch:
    """Tests for query-parameter-based filtering and search."""

    def test_filter_todos_by_completed(self):
        _create_todo("Pending task")
        t2 = _create_todo("Done task")
        client.put(f"/todos/{t2['id']}", json={"completed": True})

        # Only completed
        response = client.get("/todos", params={"completed": True})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["todos"][0]["title"] == "Done task"

        # Only pending
        response = client.get("/todos", params={"completed": False})
        data = response.json()
        assert data["total"] == 1
        assert data["todos"][0]["title"] == "Pending task"

    def test_search_todos_by_title(self):
        _create_todo("Buy groceries", "Milk and eggs")
        _create_todo("Read a book", "Science fiction novel")
        _create_todo("Clean kitchen", "Scrub the counters")

        response = client.get("/todos", params={"search": "groceries"})
        data = response.json()
        assert data["total"] == 1
        assert data["todos"][0]["title"] == "Buy groceries"

    def test_search_todos_by_description(self):
        _create_todo("Read a book", "Science fiction novel")
        _create_todo("Clean kitchen", "Scrub the counters")

        response = client.get("/todos", params={"search": "fiction"})
        data = response.json()
        assert data["total"] == 1
        assert data["todos"][0]["title"] == "Read a book"

    def test_search_todos_no_matches(self):
        _create_todo("Something")
        response = client.get("/todos", params={"search": "nonexistent"})
        assert response.json()["total"] == 0

    def test_search_is_case_insensitive(self):
        _create_todo("Buy GROCERIES")
        response = client.get("/todos", params={"search": "groceries"})
        assert response.json()["total"] == 1

    def test_combined_filter_and_search(self):
        t1 = _create_todo("Buy groceries")
        t2 = _create_todo("Buy a car")
        client.put(f"/todos/{t1['id']}", json={"completed": True})

        # Search "Buy" + completed=True → only groceries
        response = client.get(
            "/todos", params={"search": "Buy", "completed": True}
        )
        data = response.json()
        assert data["total"] == 1
        assert data["todos"][0]["title"] == "Buy groceries"


# =========================================================================
# Tests — pagination
# =========================================================================


class TestPagination:
    """Tests for skip / limit pagination."""

    def test_list_todos_pagination(self):
        _create_multiple_todos(5)

        response = client.get("/todos", params={"skip": 2, "limit": 2})
        data = response.json()
        assert len(data["todos"]) == 2
        assert data["total"] == 5

    def test_pagination_skip_beyond_total(self):
        _create_multiple_todos(3)

        response = client.get("/todos", params={"skip": 100})
        data = response.json()
        assert data["todos"] == []
        assert data["total"] == 3

    def test_pagination_limit_one(self):
        _create_multiple_todos(5)

        response = client.get("/todos", params={"limit": 1})
        data = response.json()
        assert len(data["todos"]) == 1
        assert data["total"] == 5

    def test_pagination_default_limit(self):
        _create_multiple_todos(3)
        response = client.get("/todos")
        assert len(response.json()["todos"]) == 3


# =========================================================================
# Tests — batch operations
# =========================================================================


class TestBatchOperations:
    """Tests for bulk create and bulk complete."""

    def test_batch_create(self):
        payload = [
            {"title": "Batch 1"},
            {"title": "Batch 2", "description": "With desc"},
            {"title": "Batch 3"},
        ]
        response = client.post("/todos/batch", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["total"] == 3
        assert len(data["todos"]) == 3

    def test_batch_create_empty_list(self):
        response = client.post("/todos/batch", json=[])
        assert response.status_code == 400

    def test_batch_complete(self):
        todos = _create_multiple_todos(3)
        ids = [t["id"] for t in todos[:2]]

        response = client.post("/todos/batch/complete", json=ids)
        assert response.status_code == 200
        data = response.json()
        assert all(t["completed"] for t in data["todos"])

        # Third should still be pending
        third = client.get(f"/todos/{todos[2]['id']}").json()
        assert third["completed"] is False

    def test_batch_complete_empty_list(self):
        response = client.post("/todos/batch/complete", json=[])
        assert response.status_code == 400
