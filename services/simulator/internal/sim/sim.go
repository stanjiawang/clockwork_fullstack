package sim

import (
	"fmt"
	"math"
	"sync"
	"time"

	"github.com/stan/clockwork_fullstack/services/simulator/internal/contracts"
	"github.com/stan/clockwork_fullstack/services/simulator/internal/scenario"
	"github.com/stan/clockwork_fullstack/services/simulator/internal/topology"
)

type Simulator struct {
	mu                   sync.Mutex
	Seed                 int64
	Step                 int64
	Scenario             scenario.Engine
	startedAt            time.Time
	framesEmitted        uint64
	lastFrameGeneratedMS int64
	overrideMode         scenario.Mode
	overrideUntilStep    int64
}

type snapshot struct {
	step                 int64
	scenarioName         string
	mode                 scenario.Mode
	overrideUntilStep    int64
	framesEmitted        uint64
	startedAtMS          int64
	lastFrameGeneratedMS int64
}

type MetricsSnapshot struct {
	Seed                 int64         `json:"seed"`
	Step                 int64         `json:"step"`
	ScenarioName         string        `json:"scenario"`
	Mode                 scenario.Mode `json:"mode"`
	OverrideUntilStep    int64         `json:"override_until_step,omitempty"`
	FramesEmitted        uint64        `json:"frames_emitted"`
	StartedAtMS          int64         `json:"started_at_ms"`
	LastFrameGeneratedMS int64         `json:"last_frame_generated_ms"`
}

func New(seed int64) *Simulator {
	return &Simulator{
		Seed:      seed,
		Scenario:  scenario.New(seed),
		startedAt: time.Now().UTC(),
	}
}

func (s *Simulator) NextFrame() []contracts.RawNodeMetric {
	s.mu.Lock()
	defer s.mu.Unlock()
	nowMS := time.Now().UnixMilli()
	frame := make([]contracts.RawNodeMetric, 0, topology.TotalNodeCount)
	scenarioName := s.resolveScenarioNameLocked()
	for host := 0; host < topology.HostCount; host++ {
		for gpu := 0; gpu < topology.GPUsPerHost; gpu++ {
			nodeID := topology.NodeID(host, gpu)
			hostID := topology.HostID(host)
			offset := s.Scenario.ClockDrift(s.Step, host, gpu)
			multiplier := s.Scenario.DriftMultiplier(s.Step, host, gpu)
			jitter := s.noise(s.Step, host, gpu) * 5
			offset = (offset + jitter) * multiplier
			latency := 1.35 + math.Abs(offset)/170 + float64(host%4)*0.14 + math.Abs(jitter)/12
			if scenarioName == "straggler-burst" && host >= 10 && host <= 14 {
				latency += 0.8
			}
			frame = append(frame, contracts.RawNodeMetric{
				NodeID:        nodeID,
				HostID:        hostID,
				ClockOffsetNS: math.Round(offset*100) / 100,
				P2PLatencyUS:  math.Round(latency*100) / 100,
				PacketLossPct: s.Scenario.PacketLoss(s.Step, host, gpu),
				TimestampMS:   nowMS,
			})
		}
	}
	s.Step++
	s.framesEmitted++
	s.lastFrameGeneratedMS = nowMS
	return frame
}

func (s *Simulator) Snapshot() (step int64, scenarioName string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	current := s.snapshotLocked()
	return current.step, current.scenarioName
}

func (s *Simulator) RuntimeSnapshot() MetricsSnapshot {
	s.mu.Lock()
	defer s.mu.Unlock()
	current := s.snapshotLocked()
	return MetricsSnapshot{
		Seed:                 s.Seed,
		Step:                 current.step,
		ScenarioName:         current.scenarioName,
		Mode:                 current.mode,
		OverrideUntilStep:    current.overrideUntilStep,
		FramesEmitted:        current.framesEmitted,
		StartedAtMS:          current.startedAtMS,
		LastFrameGeneratedMS: current.lastFrameGeneratedMS,
	}
}

func (s *Simulator) SetMode(mode scenario.Mode) error {
	if mode != scenario.ModeAuto && mode != scenario.ModeBaseline && mode != scenario.ModeStragglerBurst {
		return validationError{value: mode}
	}

	s.mu.Lock()
	defer s.mu.Unlock()
	s.overrideMode = mode
	s.overrideUntilStep = 0
	return nil
}

func (s *Simulator) TriggerMode(mode scenario.Mode, durationSteps int64) error {
	if mode != scenario.ModeBaseline && mode != scenario.ModeStragglerBurst {
		return validationError{value: mode}
	}
	if durationSteps <= 0 {
		return validationError{value: durationSteps}
	}

	s.mu.Lock()
	defer s.mu.Unlock()
	s.overrideMode = mode
	s.overrideUntilStep = s.Step + durationSteps
	return nil
}

func (s *Simulator) noise(step int64, host int, gpu int) float64 {
	raw := float64((step+int64(host*37)+int64(gpu*19)+s.Seed*11)%1000) / 1000.0
	return (raw - 0.5) * 2
}

func (s *Simulator) snapshotLocked() snapshot {
	scenarioName := s.resolveScenarioNameLocked()
	mode := s.overrideMode
	overrideUntilStep := s.overrideUntilStep
	return snapshot{
		step:                 s.Step,
		scenarioName:         scenarioName,
		mode:                 mode,
		overrideUntilStep:    overrideUntilStep,
		framesEmitted:        s.framesEmitted,
		startedAtMS:          s.startedAt.UnixMilli(),
		lastFrameGeneratedMS: s.lastFrameGeneratedMS,
	}
}

func (s *Simulator) resolveScenarioNameLocked() string {
	if s.overrideMode != scenario.ModeAuto && s.overrideUntilStep > 0 && s.Step >= s.overrideUntilStep {
		s.overrideMode = scenario.ModeAuto
		s.overrideUntilStep = 0
	}
	return s.Scenario.NameWithControl(s.Step, s.overrideMode, s.overrideUntilStep)
}

type validationError struct {
	value any
}

func (e validationError) Error() string {
	return fmt.Sprintf("invalid scenario control value: %v", e.value)
}
