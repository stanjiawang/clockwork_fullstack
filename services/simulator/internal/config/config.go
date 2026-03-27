package config

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

type Config struct {
	Seed            int64
	BindAddress     string
	FrameInterval   time.Duration
	ShutdownTimeout time.Duration
}

func Load() (Config, error) {
	seed, err := envInt64("SIMULATOR_SEED", 42)
	if err != nil {
		return Config{}, err
	}
	frameInterval, err := envDuration("SIMULATOR_FRAME_INTERVAL_MS", 100*time.Millisecond)
	if err != nil {
		return Config{}, err
	}
	shutdownTimeout, err := envDuration("SIMULATOR_SHUTDOWN_TIMEOUT_MS", 5*time.Second)
	if err != nil {
		return Config{}, err
	}

	cfg := Config{
		Seed:            seed,
		BindAddress:     envString("SIMULATOR_BIND_ADDRESS", ":8080"),
		FrameInterval:   frameInterval,
		ShutdownTimeout: shutdownTimeout,
	}
	if err := cfg.Validate(); err != nil {
		return Config{}, err
	}
	return cfg, nil
}

func (c Config) Validate() error {
	if c.BindAddress == "" {
		return fmt.Errorf("simulator bind address must not be empty")
	}
	if c.FrameInterval <= 0 {
		return fmt.Errorf("simulator frame interval must be positive")
	}
	if c.ShutdownTimeout <= 0 {
		return fmt.Errorf("simulator shutdown timeout must be positive")
	}
	return nil
}

func envString(key string, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func envInt64(key string, fallback int64) (int64, error) {
	if value := os.Getenv(key); value != "" {
		parsed, err := strconv.ParseInt(value, 10, 64)
		if err != nil {
			return 0, fmt.Errorf("%s must be an integer: %w", key, err)
		}
		return parsed, nil
	}
	return fallback, nil
}

func envDuration(key string, fallback time.Duration) (time.Duration, error) {
	if value := os.Getenv(key); value != "" {
		milliseconds, err := strconv.Atoi(value)
		if err != nil {
			return 0, fmt.Errorf("%s must be an integer number of milliseconds: %w", key, err)
		}
		return time.Duration(milliseconds) * time.Millisecond, nil
	}
	return fallback, nil
}
