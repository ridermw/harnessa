# Task: Add Tags Feature to Todo API

## Overview
Add a complete tags/labeling system to the existing Todo API. Users should be able to create tags, assign them to todos, and filter todos by tag.

## Requirements

### Tag Model
- Create a Tag model with: id, name (unique), created_at
- Create a many-to-many relationship between Todo and Tag (association table)

### New Endpoints
1. **POST /tags** — Create a new tag (name required, must be unique)
2. **GET /tags** — List all tags
3. **POST /todos/{todo_id}/tags** — Assign a tag to a todo
4. **DELETE /todos/{todo_id}/tags/{tag_id}** — Remove a tag from a todo
5. **GET /tags/{tag_id}/count** — Get the number of todos with this tag

### Modified Endpoints
1. **GET /todos** — Add optional `tag` query parameter to filter by tag name
2. **GET /todos/{todo_id}** — Response should include assigned tags

### Business Rules
- Tag names must be unique (return 409 Conflict on duplicate)
- Tags can contain spaces and special characters
- Deleting a tag should remove it from all associated todos (cascade)
- A todo can have multiple tags
- Assigning the same tag twice to a todo should be idempotent or return appropriate error

### Constraints
- All existing tests must continue to pass
- Write a proper SQLAlchemy migration or update models appropriately
- Follow existing code style and patterns
- Update schemas for new request/response shapes
