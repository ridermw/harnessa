"""Hidden acceptance tests for the Tags feature.

These tests validate the tags/labeling system described in TASK.md.
The feature does NOT yet exist in the codebase — these tests define the
expected behaviour and will only pass once the feature is correctly
implemented.

Endpoints under test
--------------------
- POST   /tags                     — create a tag
- GET    /tags                     — list all tags
- POST   /todos/{todo_id}/tags     — assign a tag to a todo
- DELETE  /todos/{todo_id}/tags/{tag_id} — remove a tag from a todo
- GET    /todos?tag=<name>         — filter todos by tag name
- GET    /tags/{tag_id}/count      — count of todos for a tag
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# Test database setup (in-memory SQLite, isolated per session)
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
    """Create all tables before each test and tear them down afterwards."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_todo(title: str = "Test todo", description: str | None = None) -> dict:
    payload: dict = {"title": title}
    if description is not None:
        payload["description"] = description
    resp = client.post("/todos", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_tag(name: str) -> dict:
    resp = client.post("/tags", json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _assign_tag(todo_id: int, tag_id: int) -> None:
    resp = client.post(f"/todos/{todo_id}/tags", json={"tag_id": tag_id})
    assert resp.status_code in (200, 201), resp.text


# ---------------------------------------------------------------------------
# 1. Create a tag
# ---------------------------------------------------------------------------

def test_create_tag():
    resp = client.post("/tags", json={"name": "urgent"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "urgent"
    assert "id" in data
    assert "created_at" in data


# ---------------------------------------------------------------------------
# 2. List tags
# ---------------------------------------------------------------------------

def test_list_tags():
    _create_tag("urgent")
    _create_tag("work")
    _create_tag("personal")

    resp = client.get("/tags")
    assert resp.status_code == 200
    data = resp.json()

    assert "tags" in data
    assert "total" in data
    assert data["total"] == 3

    names = {t["name"] for t in data["tags"]}
    assert names == {"urgent", "work", "personal"}


# ---------------------------------------------------------------------------
# 3. Assign a tag to a todo
# ---------------------------------------------------------------------------

def test_assign_tag_to_todo():
    todo = _create_todo("Buy groceries")
    tag = _create_tag("shopping")

    resp = client.post(f"/todos/{todo['id']}/tags", json={"tag_id": tag["id"]})
    assert resp.status_code in (200, 201)

    # Verify the tag appears on the todo
    resp = client.get(f"/todos/{todo['id']}")
    assert resp.status_code == 200
    todo_data = resp.json()
    assert "tags" in todo_data
    tag_names = [t["name"] for t in todo_data["tags"]]
    assert "shopping" in tag_names


# ---------------------------------------------------------------------------
# 4. Remove a tag from a todo
# ---------------------------------------------------------------------------

def test_remove_tag_from_todo():
    todo = _create_todo("Clean house")
    tag = _create_tag("chores")
    _assign_tag(todo["id"], tag["id"])

    # Remove the tag
    resp = client.delete(f"/todos/{todo['id']}/tags/{tag['id']}")
    assert resp.status_code in (200, 204)

    # Confirm it is gone
    resp = client.get(f"/todos/{todo['id']}")
    todo_data = resp.json()
    tag_names = [t["name"] for t in todo_data.get("tags", [])]
    assert "chores" not in tag_names


# ---------------------------------------------------------------------------
# 5. Filter todos by tag
# ---------------------------------------------------------------------------

def test_filter_todos_by_tag():
    todo_a = _create_todo("Buy groceries")
    todo_b = _create_todo("Read a book")
    tag = _create_tag("urgent")
    _assign_tag(todo_a["id"], tag["id"])

    resp = client.get("/todos", params={"tag": "urgent"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["todos"][0]["title"] == "Buy groceries"


# ---------------------------------------------------------------------------
# 6. Multiple tags per todo
# ---------------------------------------------------------------------------

def test_multiple_tags_per_todo():
    todo = _create_todo("Plan vacation")
    tag1 = _create_tag("personal")
    tag2 = _create_tag("travel")
    tag3 = _create_tag("fun")

    _assign_tag(todo["id"], tag1["id"])
    _assign_tag(todo["id"], tag2["id"])
    _assign_tag(todo["id"], tag3["id"])

    resp = client.get(f"/todos/{todo['id']}")
    assert resp.status_code == 200
    todo_data = resp.json()
    assert "tags" in todo_data
    tag_names = {t["name"] for t in todo_data["tags"]}
    assert tag_names == {"personal", "travel", "fun"}


# ---------------------------------------------------------------------------
# 7. Tag with special characters
# ---------------------------------------------------------------------------

def test_tag_with_special_characters():
    resp = client.post("/tags", json={"name": "work & life"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "work & life"

    # Verify it appears in the list
    resp = client.get("/tags")
    names = [t["name"] for t in resp.json()["tags"]]
    assert "work & life" in names


# ---------------------------------------------------------------------------
# 8. Delete tag cascades (tag removed from all todos)
# ---------------------------------------------------------------------------

def test_delete_tag_cascades():
    todo_a = _create_todo("Task A")
    todo_b = _create_todo("Task B")
    tag = _create_tag("temporary")
    _assign_tag(todo_a["id"], tag["id"])
    _assign_tag(todo_b["id"], tag["id"])

    # Delete the tag
    resp = client.delete(f"/tags/{tag['id']}")
    assert resp.status_code in (200, 204)

    # Confirm tag no longer on either todo
    for tid in (todo_a["id"], todo_b["id"]):
        resp = client.get(f"/todos/{tid}")
        tag_names = [t["name"] for t in resp.json().get("tags", [])]
        assert "temporary" not in tag_names

    # Confirm tag itself is gone
    resp = client.get("/tags")
    tag_names = [t["name"] for t in resp.json()["tags"]]
    assert "temporary" not in tag_names


# ---------------------------------------------------------------------------
# 9. Duplicate tag prevention
# ---------------------------------------------------------------------------

def test_duplicate_tag_prevention():
    _create_tag("unique-label")

    resp = client.post("/tags", json={"name": "unique-label"})
    assert resp.status_code == 409
    assert "conflict" in resp.json().get("detail", "").lower() or "exists" in resp.json().get("detail", "").lower()


# ---------------------------------------------------------------------------
# 10. Tag count endpoint
# ---------------------------------------------------------------------------

def test_tag_count_endpoint():
    todo_a = _create_todo("Task A")
    todo_b = _create_todo("Task B")
    todo_c = _create_todo("Task C")
    tag = _create_tag("important")
    _assign_tag(todo_a["id"], tag["id"])
    _assign_tag(todo_b["id"], tag["id"])
    _assign_tag(todo_c["id"], tag["id"])

    resp = client.get(f"/tags/{tag['id']}/count")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tag_id"] == tag["id"]
    assert data["name"] == "important"
    assert data["todo_count"] == 3
