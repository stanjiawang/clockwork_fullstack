package config

import "testing"

func TestLoadUsesDefaultsWhenEnvMissing(t *testing.T) {
	t.Setenv("SIMULATOR_SEED", "")
	t.Setenv("SIMULATOR_BIND_ADDRESS", "")
	t.Setenv("SIMULATOR_FRAME_INTERVAL_MS", "")
	t.Setenv("SIMULATOR_SHUTDOWN_TIMEOUT_MS", "")

	cfg, err := Load()
	if err != nil {
		t.Fatalf("expected default config to load, got error: %v", err)
	}

	if cfg.Seed != 42 {
		t.Fatalf("expected default seed 42, got %d", cfg.Seed)
	}
	if cfg.BindAddress != ":8080" {
		t.Fatalf("expected default bind address, got %s", cfg.BindAddress)
	}
	if cfg.FrameInterval.Milliseconds() != 100 {
		t.Fatalf("expected 100ms frame interval, got %d", cfg.FrameInterval.Milliseconds())
	}
}

func TestLoadUsesEnvironmentOverrides(t *testing.T) {
	t.Setenv("SIMULATOR_SEED", "99")
	t.Setenv("SIMULATOR_BIND_ADDRESS", "127.0.0.1:18080")
	t.Setenv("SIMULATOR_FRAME_INTERVAL_MS", "250")
	t.Setenv("SIMULATOR_SHUTDOWN_TIMEOUT_MS", "7500")

	cfg, err := Load()
	if err != nil {
		t.Fatalf("expected override config to load, got error: %v", err)
	}

	if cfg.Seed != 99 {
		t.Fatalf("expected seed 99, got %d", cfg.Seed)
	}
	if cfg.BindAddress != "127.0.0.1:18080" {
		t.Fatalf("unexpected bind address: %s", cfg.BindAddress)
	}
	if cfg.FrameInterval.Milliseconds() != 250 {
		t.Fatalf("expected 250ms frame interval, got %d", cfg.FrameInterval.Milliseconds())
	}
	if cfg.ShutdownTimeout.Milliseconds() != 7500 {
		t.Fatalf("expected 7500ms shutdown timeout, got %d", cfg.ShutdownTimeout.Milliseconds())
	}
}

func TestValidateRejectsInvalidValues(t *testing.T) {
	cases := []Config{
		{BindAddress: "", FrameInterval: 100, ShutdownTimeout: 1000},
		{BindAddress: ":8080", FrameInterval: 0, ShutdownTimeout: 1000},
		{BindAddress: ":8080", FrameInterval: 100, ShutdownTimeout: 0},
	}

	for index, cfg := range cases {
		if err := cfg.Validate(); err == nil {
			t.Fatalf("case %d: expected validation error", index)
		}
	}
}

func TestLoadRejectsInvalidEnvironmentValues(t *testing.T) {
	t.Setenv("SIMULATOR_SEED", "not-an-int")
	t.Setenv("SIMULATOR_FRAME_INTERVAL_MS", "0")

	_, err := Load()
	if err == nil {
		t.Fatal("expected load to fail for invalid env values")
	}
}
