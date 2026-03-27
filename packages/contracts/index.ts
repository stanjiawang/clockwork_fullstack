export type Severity = 'healthy' | 'warn' | 'critical'
export type HealthReason =
  | 'ok'
  | 'upstream_disconnected'
  | 'waiting_for_first_frame'
  | 'cluster_stale'
  | 'cluster_degraded'

export type RawNodeMetric = {
  node_id: string
  host_id: string
  clock_offset_ns: number
  p2p_latency_us: number
  packet_loss_pct: number
  timestamp_ms: number
}

export type TopologyNode = {
  id: string
  host_id: string
  group: number
}

export type TopologyLink = {
  source: string
  target: string
  kind: 'nvlink' | 'roce'
}

export type TopologyResponse = {
  nodes: TopologyNode[]
  links: TopologyLink[]
}

export type ClusterSummary = {
  health_score: number
  straggler_count: number
  mean_offset_ns: number
  p95_latency_us: number
  sync_stability_index: number
  is_stale: boolean
  last_frame_age_ms: number
}

export type ChangedNode = {
  node_id: string
  clock_offset_ns: number
  p2p_latency_us: number
  packet_loss_pct: number
  severity: Severity
  is_straggler: boolean
}

export type ClusterFrame = {
  timestamp_ms: number
  cluster: ClusterSummary
  changed_nodes: ChangedNode[]
  straggler_ids: string[]
}

export type HealthResponse = {
  status: string
  reason_code: HealthReason
  upstream_connected: boolean
  connected_clients: number
  last_frame_age_ms: number
  upstream_error?: string | null
  cluster: ClusterSummary | null
  seed?: number | null
  scenario?: string | null
  message: string
}

export type ServiceMetricsResponse = {
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
  reason_code: HealthReason
  health_status: string
  cluster_health_score?: number | null
  straggler_count: number
}

export type ScenarioStatusResponse = {
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

export type ScenarioControlRequest = {
  scenario: 'auto' | 'baseline' | 'straggler-burst'
  seed?: number | null
  reason?: string | null
  duration_steps?: number
}

export type ScenarioControlResponse = {
  accepted: boolean
  supported: boolean
  scenario: string
  seed?: number | null
  control_url?: string | null
  upstream_status_code?: number | null
  upstream_response?: Record<string, unknown> | null
  message: string
}

export type NodeDetail = {
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
