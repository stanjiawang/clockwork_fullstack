# Observability Runbook

## What To Watch

### Simulator

- `/health`
- `/metrics`
- current `scenario`
- `mode`
- `frames_emitted`
- `last_frame_age_ms`
- `connected_clients`
- `dropped_clients`

### BFF

- `/health`
- `/api/health`
- `/api/metrics`
- `reason_code`
- `upstream_connected`
- `latest_frame_age_ms`
- `broadcasts_dropped`
- `messages_processed`
- `connected_clients`

### Frontend

- connection badge state
- last frame age
- approximate FPS
- dropped frame count
- selected-node detail freshness

## Health Endpoints

### Simulator

`GET /health` should tell you:

- whether the simulator is alive
- current seed
- active scenario
- control mode
- frame age and emitted frame count
- current client count

### BFF

`GET /health` and `GET /api/health` should tell you:

- whether upstream is connected
- current reason code
- current cluster health summary
- last frame age
- connected client count
- active scenario and seed

## Common Failure Modes

### Stream disconnects

Check in this order:

1. simulator `/health`
2. BFF `/health`
3. BFF `upstream_error`
4. frontend connection badge and diagnostics

Typical interpretation:

- simulator down: BFF degrades and frontend goes stale/disconnected
- simulator up but BFF stale: ingest or transport issue
- BFF healthy but UI stale: browser transport or state application issue

### Node highlights stop updating

Check:

1. BFF `/api/stream` behavior and latest frame age
2. BFF `changed_nodes` generation
3. frontend websocket connection state
4. Pinia store updates and diagnostics

### Trend chart stops moving

Check:

1. `/api/health` cluster summary still changes
2. frontend is receiving new frames
3. chart history buffer is advancing
4. selected shell/layout changes did not suppress the chart render path

### Scenario controls look unavailable

Check:

1. BFF `/api/scenario`
2. `control_supported`
3. `control_url`
4. simulator `/scenario` and `POST /scenario/control`

The frontend disables those controls when the BFF reports scenario control as unavailable.

## Service Notes

### BFF

- logging is JSON structured
- scenario control is proxied through the BFF
- websocket fanout is latest-value oriented, so slow consumers are dropped rather than stalling the service

### Simulator

- startup logs include bind address, seed, and frame interval
- shutdown is signal-aware
- runtime mode and override windows are observable through `/scenario` and `/metrics`

## Deployment Smoke Checks

The deploy workflow validates:

- `${PUBLIC_WEB_URL}/healthz`
- `${PUBLIC_BFF_HTTP_URL}/health`
- `${PUBLIC_BFF_HTTP_URL}/api/health`
- `${PUBLIC_BFF_HTTP_URL}/api/scenario`
- `${PUBLIC_BFF_HTTP_URL}/api/topology`

If smoke tests fail, treat the deployment as unhealthy even if containers started successfully.
