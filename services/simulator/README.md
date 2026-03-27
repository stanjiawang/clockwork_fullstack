# Simulator Service

The simulator is the raw telemetry engine for the Clockwork AI Fabric demo. It generates synthetic cluster metrics for 256 GPUs and publishes them as a websocket stream for the BFF.

## Responsibilities

- build the static GPU topology
- simulate clock drift, latency, and packet loss
- expose deterministic seeded scenario behavior
- publish raw telemetry at a fixed frame interval
- expose lightweight health and topology endpoints

## Runtime Interfaces

- `GET /health`
- `GET /topology`
- `GET /scenario`
- `POST /scenario/control`
- `GET /metrics`
- `WS /stream`

## Configuration

Environment variables:

- `SIMULATOR_SEED`
- `SIMULATOR_BIND_ADDRESS`
- `SIMULATOR_FRAME_INTERVAL_MS`
- `SIMULATOR_SHUTDOWN_TIMEOUT_MS`

Validation rules:

- bind address must not be empty
- frame interval must be positive
- shutdown timeout must be positive

## Operational Notes

- Scenario generation is deterministic for a given seed.
- The websocket hub is designed for bounded fanout and evicts slow clients rather than blocking the broadcast path.
- The server supports graceful shutdown and signal-aware termination.
- `GET /health` includes runtime counters such as frame count, mode, and last-frame age.
- `GET /metrics` exposes machine-readable counters for observability and troubleshooting.
- `POST /scenario/control` accepts `mode` and optional `duration_steps` to switch or trigger simulation modes at runtime.
- Container builds are available through [Dockerfile](/Users/stan/Work/clockwork_fullstack/services/simulator/Dockerfile) and are validated in CI.

## Tests

Run from `services/simulator`:

```bash
gofmt -w ./...
GOCACHE=/tmp/go-build go test ./...
```

Benchmarks:

```bash
GOCACHE=/tmp/go-build go test -bench=. ./...
```
