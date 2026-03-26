# Task: Fix the Race Condition

Fix the race condition in `pool.go`. All tests should pass with the `-race` flag.

## Problem
The connection pool in `pool.go` has a race condition: the `conns` map is read and written
concurrently without synchronization. The `Get()` method iterates over the map while
`Release()` writes to it, causing a data race under concurrent access.

## Requirements
- All tests should pass with `go test -race ./...`
- The fix should be minimal — don't restructure the entire pool
- Don't change the Pool's public API
- Maintain reasonable performance (don't hold locks longer than necessary)

## Files
- `pool.go` — connection pool implementation (contains the race condition)
- `pool_test.go` — test suite including a concurrent test
- `main.go` — HTTP server (should not need changes)
