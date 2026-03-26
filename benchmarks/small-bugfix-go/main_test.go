package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func newTestServer() *Server {
	return NewServer(NewPool(20), NewStore())
}

func TestHealthEndpoint(t *testing.T) {
	srv := newTestServer()

	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()

	srv.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	var body map[string]string
	if err := json.NewDecoder(w.Body).Decode(&body); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}
	if body["status"] != "ok" {
		t.Errorf("Expected status=ok, got %q", body["status"])
	}
}

func TestCreateAndGetItem(t *testing.T) {
	srv := newTestServer()

	// Create an item.
	createBody := `{"name":"widget","value":"42"}`
	req := httptest.NewRequest(http.MethodPost, "/items", strings.NewReader(createBody))
	w := httptest.NewRecorder()
	srv.ServeHTTP(w, req)

	if w.Code != http.StatusCreated {
		t.Fatalf("Create: expected 201, got %d", w.Code)
	}

	var created Item
	if err := json.NewDecoder(w.Body).Decode(&created); err != nil {
		t.Fatalf("Failed to decode created item: %v", err)
	}
	if created.Name != "widget" {
		t.Errorf("Expected name=widget, got %q", created.Name)
	}

	// Retrieve the item by ID.
	req = httptest.NewRequest(http.MethodGet, "/items/"+created.ID, nil)
	w = httptest.NewRecorder()
	srv.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("Get: expected 200, got %d", w.Code)
	}

	var fetched Item
	if err := json.NewDecoder(w.Body).Decode(&fetched); err != nil {
		t.Fatalf("Failed to decode fetched item: %v", err)
	}
	if fetched.ID != created.ID || fetched.Name != created.Name {
		t.Errorf("Fetched item does not match created item")
	}
}

func TestListItems(t *testing.T) {
	srv := newTestServer()

	// Create two items.
	for _, name := range []string{"alpha", "beta"} {
		body := `{"name":"` + name + `","value":"v"}`
		req := httptest.NewRequest(http.MethodPost, "/items", strings.NewReader(body))
		w := httptest.NewRecorder()
		srv.ServeHTTP(w, req)
		if w.Code != http.StatusCreated {
			t.Fatalf("Create %s: expected 201, got %d", name, w.Code)
		}
	}

	// List all items.
	req := httptest.NewRequest(http.MethodGet, "/items", nil)
	w := httptest.NewRecorder()
	srv.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("List: expected 200, got %d", w.Code)
	}

	var items []*Item
	if err := json.NewDecoder(w.Body).Decode(&items); err != nil {
		t.Fatalf("Failed to decode items list: %v", err)
	}
	if len(items) != 2 {
		t.Errorf("Expected 2 items, got %d", len(items))
	}
}

func TestGetItemNotFound(t *testing.T) {
	srv := newTestServer()

	req := httptest.NewRequest(http.MethodGet, "/items/999", nil)
	w := httptest.NewRecorder()
	srv.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("Expected 404, got %d", w.Code)
	}
}
