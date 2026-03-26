package main

import (
	"sync"
	"testing"
)

// TestPoolRaceDetector is designed to deterministically trigger the race condition.
// Run with: go test -race -run TestPoolRaceDetector -count=5
func TestPoolRaceDetector(t *testing.T) {
	pool := NewPool(10)
	var wg sync.WaitGroup

	// 100 goroutines hammering the pool simultaneously.
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 50; j++ {
				conn, err := pool.Get()
				if err != nil {
					continue
				}
				// Don't sleep — maximize contention.
				pool.Release(conn)
			}
		}()
	}

	wg.Wait()

	// Verify pool integrity after concurrent access.
	stats := pool.Stats()
	if stats.ActiveCount < 0 {
		t.Errorf("ActiveCount went negative: %d", stats.ActiveCount)
	}
}

// TestPoolStatsConsistency runs multiple rounds of concurrent access and
// verifies that statistics remain internally consistent.
func TestPoolStatsConsistency(t *testing.T) {
	pool := NewPool(5)

	var wg sync.WaitGroup
	rounds := 20
	goroutines := 50

	for i := 0; i < goroutines; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < rounds; j++ {
				conn, err := pool.Get()
				if err != nil {
					continue
				}
				pool.Release(conn)
			}
		}()
	}

	wg.Wait()

	stats := pool.Stats()
	t.Logf("Stats: created=%d, reused=%d, released=%d, active=%d",
		stats.TotalCreated, stats.TotalReused, stats.TotalReleased, stats.ActiveCount)

	if stats.ActiveCount != 0 {
		t.Errorf("Expected 0 active connections after all released, got %d", stats.ActiveCount)
	}
}
