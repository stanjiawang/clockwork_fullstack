# API Contracts

This document describes the canonical wire contracts shared by the simulator, BFF, and frontend.

Source of truth in code:

- [packages/contracts/index.ts](/Users/stan/Work/clockwork_fullstack/packages/contracts/index.ts)
- [services/bff/app/models.py](/Users/stan/Work/clockwork_fullstack/services/bff/app/models.py)
- [services/simulator/internal/contracts/contracts.go](/Users/stan/Work/clockwork_fullstack/services/simulator/internal/contracts/contracts.go)

## Naming Rules

- Wire payloads use `snake_case`
- Timestamps use epoch milliseconds
- Metric names include units where needed
- Frontend internal view models may adapt data, but transport payloads should remain stable

## Core Types

### `RawNodeMetric`

```ts
type RawNodeMetric = {
  node_id: string
  host_id: string
  clock_offset_ns: number
  p2p_latency_us: number
  packet_loss_pct: number
  timestamp_ms: number
}
```

### `TopologyResponse`

```ts
type TopologyResponse = {
  nodes: Array<{
    id: string
    host_id: string
    group: number
  }>
  links: Array<{
    source: string
    target: string
    kind: 'nvlink' | 'roce'
  }>
}
```

### `ClusterSummary`

```ts
type ClusterSummary = {
  health_score: number
  straggler_count: number
  mean_offset_ns: number
  p95_latency_us: number
  sync_stability_index: number
  is_stale: boolean
  last_frame_age_ms: number
}
```

### `ClusterFrame`

```ts
type ClusterFrame = {
  timestamp_ms: number
  cluster: ClusterSummary
  changed_nodes: Array<{
    node_id: string
    clock_offset_ns: number
    p2p_latency_us: number
    packet_loss_pct: number
    severity: 'healthy' | 'warn' | 'critical'
    is_straggler: boolean
  }>
  straggler_ids: string[]
}
```

### `HealthResponse`

```ts
type HealthResponse = {
  status: string
  reason_code:
    | 'ok'
    | 'upstream_disconnected'
    | 'waiting_for_first_frame'
    | 'cluster_stale'
    | 'cluster_degraded'
  upstream_connected: boolean
  connected_clients: number
  last_frame_age_ms: number
  upstream_error?: string | null
  cluster: ClusterSummary | null
  seed?: number | null
  scenario?: string | null
  message: string
}
```

### `ServiceMetricsResponse`

```ts
type ServiceMetricsResponse = {
  uptime_ms: number
  messages_processed: number
  broadcasts_dropped: number
  connected_clients: number
  latest_frame_age_ms: number
  latest_broadcast_age_ms: number
  topology_loaded: boolean
  upstream_connected: boolean
  upstream_error?: string | null
  scenario: string
  seed?: number | null
  reason_code: 'ok' | 'upstream_disconnected' | 'waiting_for_first_frame' | 'cluster_stale' | 'cluster_degraded'
  health_status: string
  cluster_health_score?: number | null
  straggler_count: number
}
```

### `ScenarioStatusResponse`

```ts
type ScenarioStatusResponse = {
  name: string
  seed?: number | null
  mode?: string | null
  control_active?: boolean
  override_until_step?: number
  step?: number
  control_supported: boolean
  control_url?: string | null
  message: string
}
```

### `ScenarioControlRequest`

```ts
type ScenarioControlRequest = {
  scenario: 'auto' | 'baseline' | 'straggler-burst'
  seed?: number | null
  reason?: string | null
  duration_steps?: number
}
```

### `ScenarioControlResponse`

```ts
type ScenarioControlResponse = {
  accepted: boolean
  supported: boolean
  scenario: string
  seed?: number | null
  control_url?: string | null
  upstream_status_code?: number | null
  upstream_response?: Record<string, unknown> | null
  message: string
}
```

### `NodeDetail`

```ts
type NodeDetail = {
  node_id: string
  host_id: string
  recent_metrics: RawNodeMetric[]
  anomaly: {
    offset_zscore: number
    latency_zscore: number
    is_straggler: boolean
    recommendation: string
  }
}
```

## Units and Semantics

- `clock_offset_ns`: nanoseconds
- `p2p_latency_us`: microseconds
- `packet_loss_pct`: percent in the range `0.0 - 100.0`
- `timestamp_ms`: epoch milliseconds

## Severity Values

- `healthy`
- `warn`
- `critical`

## Health Reason Codes

- `ok`
- `upstream_disconnected`
- `waiting_for_first_frame`
- `cluster_stale`
- `cluster_degraded`

These values are used to explain degraded states in a machine-readable way and should not be changed casually.

## Stale Data Rules

- A frame is considered stale once `last_frame_age_ms` crosses the current threshold in the BFF runtime logic
- The frontend should treat stale data as a first-class state, separate from total disconnect
- Health may still be returned as `degraded` rather than total failure when stale frames exist

## Runtime Interfaces

### Simulator

- `GET /health`
- `GET /metrics`
- `GET /topology`
- `GET /scenario`
- `POST /scenario/control`
- `WS /stream`

### BFF

- `GET /health`
- `GET /api/health`
- `GET /api/metrics`
- `GET /api/topology`
- `GET /api/scenario`
- `POST /api/scenario`
- `GET /api/nodes/{id}`
- `WS /api/stream`

## Versioning Rules

- Prefer additive changes
- Update [packages/contracts/index.ts](/Users/stan/Work/clockwork_fullstack/packages/contracts/index.ts) first
- Update example payloads in the same change
- Coordinate BFF, simulator, and frontend updates together for breaking changes

## Example Payloads

- [raw-node-metric.example.json](/Users/stan/Work/clockwork_fullstack/packages/contracts/raw-node-metric.example.json)
- [cluster-frame.example.json](/Users/stan/Work/clockwork_fullstack/packages/contracts/cluster-frame.example.json)
- [node-detail.example.json](/Users/stan/Work/clockwork_fullstack/packages/contracts/node-detail.example.json)
