from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


Severity = Literal["healthy", "warn", "critical"]


class HealthReason(StrEnum):
    OK = "ok"
    UPSTREAM_DISCONNECTED = "upstream_disconnected"
    WAITING_FOR_FIRST_FRAME = "waiting_for_first_frame"
    CLUSTER_STALE = "cluster_stale"
    CLUSTER_DEGRADED = "cluster_degraded"


class RawNodeMetric(BaseModel):
    node_id: str
    host_id: str
    clock_offset_ns: float
    p2p_latency_us: float
    packet_loss_pct: float
    timestamp_ms: int


class ChangedNode(BaseModel):
    node_id: str
    clock_offset_ns: float
    p2p_latency_us: float
    packet_loss_pct: float
    severity: Severity
    is_straggler: bool


class ClusterSummary(BaseModel):
    health_score: float
    straggler_count: int
    mean_offset_ns: float
    p95_latency_us: float
    sync_stability_index: float
    is_stale: bool
    last_frame_age_ms: int


class ClusterFrame(BaseModel):
    timestamp_ms: int
    cluster: ClusterSummary
    changed_nodes: list[ChangedNode]
    straggler_ids: list[str]


class NodeAnomaly(BaseModel):
    offset_zscore: float
    latency_zscore: float
    is_straggler: bool
    recommendation: str


class NodeDetail(BaseModel):
    node_id: str
    host_id: str
    recent_metrics: list[RawNodeMetric]
    anomaly: NodeAnomaly


class TopologyNode(BaseModel):
    id: str
    host_id: str
    group: int


class TopologyLink(BaseModel):
    source: str
    target: str
    kind: Literal["nvlink", "roce"]


class TopologyResponse(BaseModel):
    nodes: list[TopologyNode]
    links: list[TopologyLink]


class HealthResponse(BaseModel):
    status: str
    reason_code: HealthReason
    upstream_connected: bool
    connected_clients: int
    last_frame_age_ms: int = 0
    upstream_error: str | None = None
    cluster: ClusterSummary | None = None
    seed: int | None = None
    scenario: str | None = None
    message: str = Field(default="")


class ServiceMetricsResponse(BaseModel):
    uptime_ms: int
    messages_processed: int
    broadcasts_dropped: int
    connected_clients: int
    latest_frame_age_ms: int
    latest_broadcast_age_ms: int
    topology_loaded: bool
    upstream_connected: bool
    upstream_error: str | None = None
    scenario: str = ""
    seed: int | None = None
    reason_code: HealthReason = HealthReason.OK
    health_status: str = "ok"
    cluster_health_score: float | None = None
    straggler_count: int = 0


class ScenarioStatusResponse(BaseModel):
    name: str
    seed: int | None = None
    mode: str | None = None
    control_active: bool = False
    override_until_step: int | None = None
    step: int | None = None
    control_supported: bool
    control_url: str | None = None
    message: str = Field(default="")


class ScenarioControlRequest(BaseModel):
    scenario: str
    seed: int | None = None
    reason: str | None = None
    duration_steps: int | None = None


class ScenarioControlResponse(BaseModel):
    accepted: bool
    supported: bool
    scenario: str
    seed: int | None = None
    control_url: str | None = None
    upstream_status_code: int | None = None
    upstream_response: dict[str, Any] | None = None
    message: str = Field(default="")
