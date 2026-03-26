package main

import (
	"sync"
	"testing"
)

func TestPoolSequentialGetRelease(t *testing.T) {
	pool := NewPool(5)

	conn, err := pool.Get()
	if err != nil {
		t.Fatalf("Get() returned error: %v", err)
	}
	if conn == nil {
		t.Fatal("Get() returned nil connection")
	}
	if !conn.inUse {
		t.Error("Expected connection to be marked in use")
	}

	err = pool.Release(conn)
	if err != nil {
		t.Fatalf("Release() returned error: %v", err)
	}
	if conn.inUse {
		t.Error("Expected connection to be marked idle after release")
	}

	// Get again — should reuse the same connection.
	conn2, err := pool.Get()
	if err != nil {
		t.Fatalf("Second Get() returned error: %v", err)
	}
	if conn2.ID != conn.ID {
		t.Errorf("Expected reused connection ID %d, got %d", conn.ID, conn2.ID)
	}
}

func TestPoolConcurrentGetRelease(t *testing.T) {
	pool := NewPool(5)
	var wg sync.WaitGroup

	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 100; j++ {
				conn, err := pool.Get()
				if err != nil {
					continue
				}
				pool.Release(conn)
			}
		}()
	}

	wg.Wait()
}

func TestPoolExhaustion(t *testing.T) {
	pool := NewPool(3)

	conns := make([]*Conn, 0, 3)
	for i := 0; i < 3; i++ {
		conn, err := pool.Get()
		if err != nil {
			t.Fatalf("Get() #%d returned error: %v", i+1, err)
		}
		conns = append(conns, conn)
	}

	// Pool is full — next Get should fail.
	_, err := pool.Get()
	if err == nil {
		t.Error("Expected error when pool is exhausted, got nil")
	}

	// Release one and try again.
	pool.Release(conns[0])
	conn, err := pool.Get()
	if err != nil {
		t.Fatalf("Get() after release returned error: %v", err)
	}
	if conn == nil {
		t.Fatal("Get() after release returned nil connection")
	}
}

func TestPoolConnectionReuse(t *testing.T) {
	pool := NewPool(5)

	conn, err := pool.Get()
	if err != nil {
		t.Fatalf("Get() returned error: %v", err)
	}
	originalID := conn.ID

	pool.Release(conn)

	conn2, err := pool.Get()
	if err != nil {
		t.Fatalf("Second Get() returned error: %v", err)
	}

	if conn2.ID != originalID {
		t.Errorf("Expected connection reuse with ID %d, got %d", originalID, conn2.ID)
	}

	stats := pool.Stats()
	if stats.TotalReused != 1 {
		t.Errorf("Expected TotalReused=1, got %d", stats.TotalReused)
	}
}
