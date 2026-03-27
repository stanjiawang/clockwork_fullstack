package sim

import (
	"testing"

	"github.com/stan/clockwork_fullstack/services/simulator/internal/scenario"
)

func TestNextFrameReturnsFullCluster(t *testing.T) {
	simulator := New(42)
	frame := simulator.NextFrame()

	if got := len(frame); got != 256 {
		t.Fatalf("expected 256 metrics, got %d", got)
	}

	first := frame[0]
	if first.NodeID != "gpu-00-00" {
		t.Fatalf("unexpected first node id: %s", first.NodeID)
	}
	if first.TimestampMS <= 0 {
		t.Fatalf("expected timestamp, got %d", first.TimestampMS)
	}
}

func TestNextFrameProducesStragglerWindowMetrics(t *testing.T) {
	simulator := New(42)
	simulator.Step = 30
	frame := simulator.NextFrame()

	var found bool
	for _, metric := range frame {
		if metric.HostID == "host-12" && metric.PacketLossPct >= 0.5 {
			found = true
			break
		}
	}
	if !found {
		t.Fatal("expected burst metrics on host-12")
	}
}

func TestRuntimeSnapshotIncludesCountersAndControlMode(t *testing.T) {
	simulator := New(42)
	if err := simulator.SetMode(scenario.ModeBaseline); err != nil {
		t.Fatalf("set mode: %v", err)
	}
	simulator.NextFrame()

	snapshot := simulator.RuntimeSnapshot()
	if snapshot.FramesEmitted != 1 {
		t.Fatalf("expected one emitted frame, got %d", snapshot.FramesEmitted)
	}
	if snapshot.Mode != scenario.ModeBaseline {
		t.Fatalf("expected baseline override, got %s", snapshot.Mode)
	}
	if snapshot.ScenarioName != string(scenario.ModeBaseline) {
		t.Fatalf("expected baseline scenario, got %s", snapshot.ScenarioName)
	}
}

func BenchmarkNextFrame(b *testing.B) {
	simulator := New(42)
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		_ = simulator.NextFrame()
	}
}
