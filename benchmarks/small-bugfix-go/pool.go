package main

import (
	"errors"
	"fmt"
	"sync/atomic"
	"time"
)

// Conn represents a pooled connection.
type Conn struct {
	ID        int
	CreatedAt time.Time
	inUse     bool
}

// Pool manages a set of reusable connections.
// The counter and stats use atomic operations, but the conns map is
// NOT protected by a mutex — this is the race condition.
type Pool struct {
	conns   map[int]*Conn
	maxSize int
	counter int64
	stats   PoolStats
}

// PoolStats tracks pool usage metrics.
type PoolStats struct {
	TotalCreated  int64
	TotalReused   int64
	TotalReleased int64
	ActiveCount   int64
}

// NewPool creates a connection pool with the given maximum size.
func NewPool(maxSize int) *Pool {
	return &Pool{
		conns:   make(map[int]*Conn),
		maxSize: maxSize,
	}
}

// Get retrieves an idle connection from the pool or creates a new one.
// It iterates over the map without holding a lock — this races with Release.
func (p *Pool) Get() (*Conn, error) {
	// Try to find an idle connection by iterating over the map.
	// BUG: this map read is not synchronized with writes in Release().
	for id, conn := range p.conns {
		if !conn.inUse {
			p.conns[id].inUse = true
			atomic.AddInt64(&p.stats.TotalReused, 1)
			atomic.AddInt64(&p.stats.ActiveCount, 1)
			return conn, nil
		}
	}

	// No idle connection available — create a new one if under the limit.
	if len(p.conns) >= p.maxSize {
		return nil, errors.New("pool exhausted: maximum connections reached")
	}

	id := int(atomic.AddInt64(&p.counter, 1))
	conn := &Conn{
		ID:        id,
		CreatedAt: time.Now(),
		inUse:     true,
	}

	// BUG: this map write is not synchronized with the range read above.
	p.conns[id] = conn

	atomic.AddInt64(&p.stats.TotalCreated, 1)
	atomic.AddInt64(&p.stats.ActiveCount, 1)

	return conn, nil
}

// Release returns a connection to the pool, marking it as idle.
// It writes to the map without holding a lock — this races with Get.
func (p *Pool) Release(conn *Conn) error {
	if conn == nil {
		return errors.New("cannot release nil connection")
	}

	// BUG: this map read+write is not synchronized with Get().
	existing, ok := p.conns[conn.ID]
	if !ok {
		return fmt.Errorf("connection %d not found in pool", conn.ID)
	}

	if !existing.inUse {
		return fmt.Errorf("connection %d is already released", conn.ID)
	}

	p.conns[conn.ID].inUse = false

	atomic.AddInt64(&p.stats.TotalReleased, 1)
	atomic.AddInt64(&p.stats.ActiveCount, -1)

	return nil
}

// Stats returns a snapshot of the pool statistics.
func (p *Pool) Stats() PoolStats {
	return PoolStats{
		TotalCreated:  atomic.LoadInt64(&p.stats.TotalCreated),
		TotalReused:   atomic.LoadInt64(&p.stats.TotalReused),
		TotalReleased: atomic.LoadInt64(&p.stats.TotalReleased),
		ActiveCount:   atomic.LoadInt64(&p.stats.ActiveCount),
	}
}

// Close marks all connections as no longer in use and clears the pool.
func (p *Pool) Close() error {
	for id, conn := range p.conns {
		if conn.inUse {
			atomic.AddInt64(&p.stats.ActiveCount, -1)
		}
		delete(p.conns, id)
	}
	return nil
}
