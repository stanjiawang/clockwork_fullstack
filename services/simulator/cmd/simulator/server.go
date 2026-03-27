package main

import (
	"encoding/json"
	"log/slog"
	"net/http"
	"time"

	"github.com/stan/clockwork_fullstack/services/simulator/internal/scenario"
	"github.com/stan/clockwork_fullstack/services/simulator/internal/sim"
	"github.com/stan/clockwork_fullstack/services/simulator/internal/ws"
)

type scenarioControlRequest struct {
	Mode          string `json:"mode"`
	DurationSteps int64  `json:"duration_steps,omitempty"`
}

type scenarioStatusResponse struct {
	Name              string `json:"name"`
	Seed              int64  `json:"seed"`
	Mode              string `json:"mode"`
	ControlActive     bool   `json:"control_active"`
	OverrideUntilStep int64  `json:"override_until_step,omitempty"`
	Step              int64  `json:"step"`
}

type runtimeHealthResponse struct {
	Status               string `json:"status"`
	Seed                 int64  `json:"seed"`
	ConnectedClients     int    `json:"connected_clients"`
	Scenario             string `json:"scenario"`
	Mode                 string `json:"mode"`
	Step                 int64  `json:"step"`
	FramesEmitted        uint64 `json:"frames_emitted"`
	LastFrameAgeMS       int64  `json:"last_frame_age_ms"`
	LastFrameGeneratedMS int64  `json:"last_frame_generated_ms"`
	DroppedClients       uint64 `json:"dropped_clients_total"`
	UptimeMS             int64  `json:"uptime_ms"`
	Message              string `json:"message"`
}

type runtimeMetricsResponse struct {
	Seed                 int64  `json:"seed"`
	Scenario             string `json:"scenario"`
	Mode                 string `json:"mode"`
	Step                 int64  `json:"step"`
	FramesEmitted        uint64 `json:"frames_emitted"`
	ConnectedClients     int    `json:"connected_clients"`
	Broadcasts           uint64 `json:"broadcasts"`
	DroppedClients       uint64 `json:"dropped_clients"`
	LastFrameAgeMS       int64  `json:"last_frame_age_ms"`
	LastFrameGeneratedMS int64  `json:"last_frame_generated_ms"`
	UptimeMS             int64  `json:"uptime_ms"`
}

func newMux(simulator *sim.Simulator, hub *ws.Hub, topologyData any, logger *slog.Logger) *http.ServeMux {
	mux := http.NewServeMux()

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		nowMS := time.Now().UnixMilli()
		snapshot := simulator.RuntimeSnapshot()
		health := runtimeHealthResponse{
			Status:               "ok",
			Seed:                 snapshot.Seed,
			ConnectedClients:     hub.Count(),
			Scenario:             snapshot.ScenarioName,
			Mode:                 string(snapshot.Mode),
			Step:                 snapshot.Step,
			FramesEmitted:        snapshot.FramesEmitted,
			LastFrameAgeMS:       ageMS(nowMS, snapshot.LastFrameGeneratedMS),
			LastFrameGeneratedMS: snapshot.LastFrameGeneratedMS,
			DroppedClients:       hub.Snapshot().DroppedClients,
			UptimeMS:             ageMS(nowMS, snapshot.StartedAtMS),
			Message:              "simulator runtime healthy",
		}
		writeJSON(w, health)
	})

	mux.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
		nowMS := time.Now().UnixMilli()
		snapshot := simulator.RuntimeSnapshot()
		hubStats := hub.Snapshot()
		writeJSON(w, runtimeMetricsResponse{
			Seed:                 snapshot.Seed,
			Scenario:             snapshot.ScenarioName,
			Mode:                 string(snapshot.Mode),
			Step:                 snapshot.Step,
			FramesEmitted:        snapshot.FramesEmitted,
			ConnectedClients:     hubStats.ConnectedClients,
			Broadcasts:           hubStats.Broadcasts,
			DroppedClients:       hubStats.DroppedClients,
			LastFrameAgeMS:       ageMS(nowMS, snapshot.LastFrameGeneratedMS),
			LastFrameGeneratedMS: snapshot.LastFrameGeneratedMS,
			UptimeMS:             ageMS(nowMS, snapshot.StartedAtMS),
		})
	})

	mux.HandleFunc("/topology", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, topologyData)
	})

	mux.HandleFunc("/scenario", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			methodNotAllowed(w, http.MethodGet)
			return
		}
		writeJSON(w, scenarioStatus(simulator))
	})

	mux.HandleFunc("/scenario/control", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			methodNotAllowed(w, http.MethodPost)
			return
		}
		if err := applyScenarioControl(simulator, r); err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		writeJSON(w, scenarioStatus(simulator))
	})

	mux.HandleFunc("/stream", func(w http.ResponseWriter, r *http.Request) {
		if err := hub.Handle(w, r); err != nil {
			logger.Warn("stream connection failed", "error", err)
		}
	})

	return mux
}

func scenarioStatus(simulator *sim.Simulator) scenarioStatusResponse {
	snapshot := simulator.RuntimeSnapshot()
	return scenarioStatusResponse{
		Name:              snapshot.ScenarioName,
		Seed:              snapshot.Seed,
		Mode:              string(snapshot.Mode),
		ControlActive:     snapshot.Mode != scenario.ModeAuto,
		OverrideUntilStep: snapshot.OverrideUntilStep,
		Step:              snapshot.Step,
	}
}

func applyScenarioControl(simulator *sim.Simulator, r *http.Request) error {
	var request scenarioControlRequest
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&request); err != nil {
		return err
	}
	mode, err := scenario.ParseMode(request.Mode)
	if err != nil {
		return err
	}
	if request.DurationSteps > 0 {
		return simulator.TriggerMode(mode, request.DurationSteps)
	}
	return simulator.SetMode(mode)
}

func writeJSON(w http.ResponseWriter, payload any) {
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(payload); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func writeError(w http.ResponseWriter, statusCode int, err error) {
	http.Error(w, err.Error(), statusCode)
}

func methodNotAllowed(w http.ResponseWriter, allowed string) {
	w.Header().Set("Allow", allowed)
	http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
}

func ageMS(nowMS int64, baseMS int64) int64 {
	if baseMS <= 0 {
		return 0
	}
	return nowMS - baseMS
}
