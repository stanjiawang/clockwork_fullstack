# Testing Strategy

## Test Pyramid

- Go unit tests for topology generation and fault modeling
- Python unit tests for rolling Z-score logic and recommendation rules
- Frontend component tests for node rendering and detail panel behavior
- Cross-service integration test for healthy-to-straggler flow
- Contract fixtures for representative stream payloads

## Quality Gates

- No feature merges without at least one test at the correct layer.
- No contract change merges without fixture updates.
- No realtime-path change merges without stale/disconnect behavior review.

## Service-Specific Expectations

### Simulator

- topology generation is deterministic in seeded mode
- scenario bursts are testable without websocket transport
- config loading is covered with env override tests
- websocket hub behavior is covered for connection registration, broadcast, and close semantics

### BFF

- anomaly scoring is covered with fixed-window fixtures
- cluster health score is covered for healthy and degraded snapshots
- config loading is covered for environment overrides
- service health is covered for disconnect, stale-frame, and placeholder detail paths
- runtime queue semantics are covered so slow websocket consumers do not stall the broadcast path

### Web

- components are tested against typed fixture data
- render loops are tested with mocked animation frames and socket updates

## Current Commands

- BFF: `python3 -m venv .venv && .venv/bin/pip install -r services/bff/requirements.txt && .venv/bin/python -m pytest services/bff/tests`
- Simulator: `cd services/simulator && GOCACHE=/tmp/go-build go test ./...`
- Stack integration: `python3 -m venv .venv && .venv/bin/pip install -r services/bff/requirements.txt && .venv/bin/python -m pytest tests/integration`
