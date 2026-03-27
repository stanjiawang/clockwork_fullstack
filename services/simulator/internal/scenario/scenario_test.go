package scenario

import "testing"

func TestNameFlipsIntoBurstWindow(t *testing.T) {
	engine := New(42)

	if got := engine.Name(0); got != "baseline" {
		t.Fatalf("expected baseline, got %s", got)
	}

	if got := engine.Name(30); got != "straggler-burst" {
		t.Fatalf("expected burst, got %s", got)
	}
}

func TestBurstCohortHasLargerDrift(t *testing.T) {
	engine := New(42)

	if got := engine.DriftMultiplier(30, 12, 5); got < 3 {
		t.Fatalf("expected burst multiplier, got %.2f", got)
	}

	if got := engine.DriftMultiplier(0, 12, 5); got < 0.85 || got > 1.15 {
		t.Fatalf("expected baseline multiplier in nominal range, got %.2f", got)
	}
}

func TestParseModeAcceptsKnownValues(t *testing.T) {
	cases := []string{"auto", "baseline", "straggler-burst"}
	for _, raw := range cases {
		mode, err := ParseMode(raw)
		if err != nil {
			t.Fatalf("expected mode %q to parse: %v", raw, err)
		}
		if string(mode) != raw {
			t.Fatalf("expected round-trip mode %q, got %q", raw, mode)
		}
	}
}

func TestNameWithControlOverridesBurstWindow(t *testing.T) {
	engine := New(42)

	if got := engine.NameWithControl(0, ModeBaseline, 0); got != string(ModeBaseline) {
		t.Fatalf("expected forced baseline, got %s", got)
	}
	if got := engine.NameWithControl(0, ModeStragglerBurst, 4); got != string(ModeStragglerBurst) {
		t.Fatalf("expected forced burst, got %s", got)
	}
	if got := engine.NameWithControl(100, ModeAuto, 0); got != string(ModeBaseline) {
		t.Fatalf("expected auto mode to fall back to baseline outside burst window, got %s", got)
	}
}
