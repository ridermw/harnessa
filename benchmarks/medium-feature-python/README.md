# Todo API

A simple TODO application built with FastAPI and SQLite.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

## Test

```bash
pytest tests/ -v
```

## API Endpoints

- `GET /` — Root endpoint
- `GET /health` — Health check
- `POST /todos` — Create a todo
- `GET /todos` — List todos (with filtering and search)
- `GET /todos/{id}` — Get a todo
- `PUT /todos/{id}` — Update a todo
- `DELETE /todos/{id}` — Delete a todo
- `GET /todos/stats/summary` — Todo statistics
