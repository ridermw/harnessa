# small-bugfix-go

A simple HTTP server backed by an in-memory item store and a connection pool.

## Endpoints

| Method | Path          | Description          |
|--------|---------------|----------------------|
| GET    | /health       | Health check         |
| GET    | /items        | List all items       |
| POST   | /items        | Create a new item    |
| GET    | /items/{id}   | Get an item by ID    |

## Running

```bash
go build && ./small-bugfix-go
```

## Testing

```bash
go test ./...
```
