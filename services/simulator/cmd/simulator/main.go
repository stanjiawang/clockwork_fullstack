package main

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/stan/clockwork_fullstack/services/simulator/internal/config"
	"github.com/stan/clockwork_fullstack/services/simulator/internal/sim"
	"github.com/stan/clockwork_fullstack/services/simulator/internal/topology"
	"github.com/stan/clockwork_fullstack/services/simulator/internal/ws"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	cfg, err := config.Load()
	if err != nil {
		logger.Error("invalid simulator config", "error", err)
		os.Exit(1)
	}
	simulator := sim.New(cfg.Seed)
	hub := ws.NewHub()
	topologyData := topology.Build()
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

	mux := newMux(simulator, hub, topologyData, logger)

	go func() {
		ticker := time.NewTicker(cfg.FrameInterval)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				frame := simulator.NextFrame()
				hub.Broadcast(frame)
			}
		}
	}()

	server := &http.Server{
		Addr:              cfg.BindAddress,
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
		WriteTimeout:      10 * time.Second,
		IdleTimeout:       60 * time.Second,
	}

	go func() {
		<-ctx.Done()
		hub.Close()
		shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), cfg.ShutdownTimeout)
		defer shutdownCancel()
		_ = server.Shutdown(shutdownCtx)
	}()

	logger.Info("simulator listening", "bind_address", cfg.BindAddress, "seed", cfg.Seed, "frame_interval_ms", cfg.FrameInterval.Milliseconds())
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		logger.Error("simulator server exited", "error", err)
		os.Exit(1)
	}
}
