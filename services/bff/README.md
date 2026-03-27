# BFF Service

The BFF is the browser-facing aggregation layer for the Clockwork AI Fabric demo. It ingests raw simulator telemetry, computes rolling anomaly signals, and exposes a curated HTTP and WebSocket API for the frontend.

## Responsibilities

- bootstrap topology and scenario metadata from the simulator
- maintain rolling node state in memory
- compute node-level anomaly scores and cluster-level health
- expose browser-facing APIs with stable contracts
- fan out latest-only patch frames to connected websocket clients
- fail fast on invalid runtime config
- emit machine-readable health reason codes for degraded states
- close bootstrap clients on startup failure so reconnect loops do not leak resources

## Runtime Interfaces

- `GET /health`
- `GET /api/health`
- `GET /api/metrics`
- `GET /api/topology`
- `GET /api/scenario`
- `POST /api/scenario`
- `GET /api/nodes/{node_id}`
- `WS /api/stream`

## Configuration

Environment variables:

- `SIMULATOR_HTTP_URL`
- `SIMULATOR_WS_URL`
- `BFF_BOOTSTRAP_TIMEOUT_S`
- `BFF_BOOTSTRAP_MAX_ATTEMPTS`
- `BFF_BOOTSTRAP_RETRY_DELAY_S`
- `BFF_BOOTSTRAP_RETRY_DELAY_CAP_S`
- `BFF_UPSTREAM_OPEN_TIMEOUT_S`
- `BFF_UPSTREAM_PING_INTERVAL_S`
- `BFF_UPSTREAM_PING_TIMEOUT_S`
- `BFF_UPSTREAM_MAX_MESSAGE_BYTES`
- `BFF_CLIENT_QUEUE_SIZE`
- `BFF_RECONNECT_DELAY_FLOOR_S`
- `BFF_RECONNECT_DELAY_CEILING_S`
- `BFF_SCENARIO_CONTROL_TIMEOUT_S`
- `BFF_LOG_LEVEL`
- `SIMULATOR_SCENARIO_CONTROL_URL`

## Operational Notes

- The service keeps runtime state in memory only.
- Websocket fanout is latest-value oriented: if a slow client falls behind, stale queued frames are replaced with the newest frame.
- Health degrades when the upstream disconnects, cluster frames become stale, or the cluster health score drops below the configured threshold logic in code.
- `/api/metrics` exposes machine-readable counters for uptime, ingest, fanout, and freshness.
- `/api/scenario` returns the current scenario snapshot and whether control proxying is configured.
- `POST /api/scenario` proxies simulator control and, by default, derives the control URL from `SIMULATOR_HTTP_URL`.
- Bootstrap now retries transient upstream failures before surfacing startup errors.

## Tests

Run from the repo root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r services/bff/requirements.txt
.venv/bin/python -m pytest services/bff/tests
```
