package main

import (
	"bytes"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/stan/clockwork_fullstack/services/simulator/internal/scenario"
	"github.com/stan/clockwork_fullstack/services/simulator/internal/sim"
	"github.com/stan/clockwork_fullstack/services/simulator/internal/topology"
	"github.com/stan/clockwork_fullstack/services/simulator/internal/ws"
)

func TestScenarioControlEndpointTriggersBurst(t *testing.T) {
	simulator := sim.New(42)
	hub := ws.NewHub()
	mux := newMux(simulator, hub, topology.Build(), slog.New(slog.NewTextHandler(io.Discard, nil)))

	req := httptest.NewRequest(http.MethodPost, "/scenario/control", strings.NewReader(`{"mode":"straggler-burst","duration_steps":3}`))
	rr := httptest.NewRecorder()
	mux.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rr.Code)
	}

	var response scenarioStatusResponse
	if err := json.NewDecoder(bytes.NewReader(rr.Body.Bytes())).Decode(&response); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if response.Mode != string(scenario.ModeStragglerBurst) {
		t.Fatalf("expected burst mode, got %s", response.Mode)
	}
	if !response.ControlActive {
		t.Fatal("expected control active")
	}

	snapshot := simulator.RuntimeSnapshot()
	if snapshot.Mode != scenario.ModeStragglerBurst {
		t.Fatalf("expected simulator mode override, got %s", snapshot.Mode)
	}
	if snapshot.OverrideUntilStep == 0 {
		t.Fatal("expected override duration to be recorded")
	}
}

func TestScenarioControlEndpointRejectsInvalidMode(t *testing.T) {
	simulator := sim.New(42)
	hub := ws.NewHub()
	mux := newMux(simulator, hub, topology.Build(), slog.New(slog.NewTextHandler(io.Discard, nil)))

	req := httptest.NewRequest(http.MethodPost, "/scenario/control", strings.NewReader(`{"mode":"unknown"}`))
	rr := httptest.NewRecorder()
	mux.ServeHTTP(rr, req)

	if rr.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", rr.Code)
	}
}

func TestMetricsEndpointReportsRuntimeCounters(t *testing.T) {
	simulator := sim.New(42)
	simulator.NextFrame()
	hub := ws.NewHub()
	hub.Broadcast(map[string]string{"status": "ok"})
	mux := newMux(simulator, hub, topology.Build(), slog.New(slog.NewTextHandler(io.Discard, nil)))

	req := httptest.NewRequest(http.MethodGet, "/metrics", nil)
	rr := httptest.NewRecorder()
	mux.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rr.Code)
	}

	var response runtimeMetricsResponse
	if err := json.NewDecoder(bytes.NewReader(rr.Body.Bytes())).Decode(&response); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if response.FramesEmitted != 1 {
		t.Fatalf("expected one emitted frame, got %d", response.FramesEmitted)
	}
	if response.Seed != 42 {
		t.Fatalf("expected seed 42, got %d", response.Seed)
	}
	if response.Broadcasts == 0 {
		t.Fatal("expected broadcast counter to be recorded")
	}
}

func TestHealthEndpointIncludesRuntimeCounters(t *testing.T) {
	simulator := sim.New(42)
	simulator.NextFrame()
	hub := ws.NewHub()
	mux := newMux(simulator, hub, topology.Build(), slog.New(slog.NewTextHandler(io.Discard, nil)))

	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	rr := httptest.NewRecorder()
	mux.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rr.Code)
	}

	var response runtimeHealthResponse
	if err := json.NewDecoder(bytes.NewReader(rr.Body.Bytes())).Decode(&response); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if response.FramesEmitted != 1 {
		t.Fatalf("expected one emitted frame, got %d", response.FramesEmitted)
	}
	if response.LastFrameAgeMS < 0 {
		t.Fatalf("expected non-negative frame age, got %d", response.LastFrameAgeMS)
	}
}

func BenchmarkScenarioControl(b *testing.B) {
	simulator := sim.New(42)
	hub := ws.NewHub()
	mux := newMux(simulator, hub, topology.Build(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	body := bytes.NewBufferString(`{"mode":"straggler-burst","duration_steps":4}`)

	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		req := httptest.NewRequest(http.MethodPost, "/scenario/control", bytes.NewReader(body.Bytes()))
		rr := httptest.NewRecorder()
		mux.ServeHTTP(rr, req)
		if rr.Code != http.StatusOK {
			b.Fatalf("unexpected status %d", rr.Code)
		}
	}
}
