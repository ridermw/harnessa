package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strings"
	"sync"
	"time"
)

// Item represents a stored resource.
type Item struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Value     string    `json:"value"`
	CreatedAt time.Time `json:"created_at"`
}

// Store holds items in memory with proper synchronization.
type Store struct {
	mu      sync.RWMutex
	items   map[string]*Item
	counter int
}

// NewStore creates an empty item store.
func NewStore() *Store {
	return &Store{
		items: make(map[string]*Item),
	}
}

// Server holds shared dependencies for the HTTP handlers.
type Server struct {
	pool  *Pool
	store *Store
}

// NewServer creates a server with the given pool and store.
func NewServer(pool *Pool, store *Store) *Server {
	return &Server{pool: pool, store: store}
}

// ServeHTTP routes requests to the appropriate handler.
func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// Acquire a pooled connection for every request.
	conn, err := s.pool.Get()
	if err != nil {
		http.Error(w, `{"error":"service unavailable"}`, http.StatusServiceUnavailable)
		return
	}
	defer s.pool.Release(conn)

	path := strings.TrimRight(r.URL.Path, "/")

	switch {
	case path == "/health" && r.Method == http.MethodGet:
		s.handleHealth(w, r)
	case path == "/items" && r.Method == http.MethodGet:
		s.handleListItems(w, r)
	case path == "/items" && r.Method == http.MethodPost:
		s.handleCreateItem(w, r)
	case strings.HasPrefix(path, "/items/") && r.Method == http.MethodGet:
		id := strings.TrimPrefix(path, "/items/")
		s.handleGetItem(w, r, id)
	default:
		http.Error(w, `{"error":"not found"}`, http.StatusNotFound)
	}
}

func (s *Server) handleHealth(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, `{"status":"ok"}`)
}

func (s *Server) handleListItems(w http.ResponseWriter, _ *http.Request) {
	s.store.mu.RLock()
	items := make([]*Item, 0, len(s.store.items))
	for _, item := range s.store.items {
		items = append(items, item)
	}
	s.store.mu.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(items)
}

func (s *Server) handleCreateItem(w http.ResponseWriter, r *http.Request) {
	var input struct {
		Name  string `json:"name"`
		Value string `json:"value"`
	}
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		http.Error(w, `{"error":"invalid json"}`, http.StatusBadRequest)
		return
	}
	if input.Name == "" {
		http.Error(w, `{"error":"name is required"}`, http.StatusBadRequest)
		return
	}

	s.store.mu.Lock()
	s.store.counter++
	id := fmt.Sprintf("%d", s.store.counter)
	item := &Item{
		ID:        id,
		Name:      input.Name,
		Value:     input.Value,
		CreatedAt: time.Now(),
	}
	s.store.items[id] = item
	s.store.mu.Unlock()

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(item)
}

func (s *Server) handleGetItem(w http.ResponseWriter, _ *http.Request, id string) {
	s.store.mu.RLock()
	item, ok := s.store.items[id]
	s.store.mu.RUnlock()

	if !ok {
		http.Error(w, `{"error":"item not found"}`, http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(item)
}

func main() {
	pool := NewPool(20)
	store := NewStore()
	srv := NewServer(pool, store)

	addr := ":8080"
	log.Printf("Starting server on %s", addr)
	if err := http.ListenAndServe(addr, srv); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
