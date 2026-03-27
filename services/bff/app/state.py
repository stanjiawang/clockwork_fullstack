from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Deque

from .models import ClusterFrame, ClusterSummary, HealthReason, NodeAnomaly, NodeDetail, RawNodeMetric, TopologyResponse
from .scoring import (
    RollingNodeState,
    classify_severity,
    health_score,
    percentile,
    recommendation_for,
    should_flag_straggler,
    stability_index,
    z_score,
)


STALE_AFTER_MS = 1500
DEFAULT_SCENARIO = "baseline"
DEFAULT_SEED = 42


@dataclass
class RuntimeState:
    topology: TopologyResponse | None = None
    nodes: dict[str, RollingNodeState] = field(default_factory=dict)
    latest_detail: dict[str, NodeDetail] = field(default_factory=dict)
    latest_frame: ClusterFrame | None = None
    latest_frame_payload: str = ""
    latest_timestamp_ms: int = 0
    latest_broadcast_ms: int = 0
    started_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    messages_processed: int = 0
    broadcasts_dropped: int = 0
    upstream_connected: bool = False
    upstream_error: str | None = None
    connected_clients: dict[int, asyncio.Queue[str]] = field(default_factory=dict)
    scenario: str = DEFAULT_SCENARIO
    seed: int = DEFAULT_SEED

    def reset(self) -> None:
        self.topology = None
        self.nodes.clear()
        self.latest_detail.clear()
        self.latest_frame = None
        self.latest_frame_payload = ""
        self.latest_timestamp_ms = 0
        self.latest_broadcast_ms = 0
        self.started_at_ms = current_time_ms()
        self.messages_processed = 0
        self.broadcasts_dropped = 0
        self.upstream_connected = False
        self.upstream_error = None
        self.connected_clients.clear()
        self.scenario = DEFAULT_SCENARIO
        self.seed = DEFAULT_SEED

    def client_count(self) -> int:
        return len(self.connected_clients)

    def last_frame_age_ms(self, now_ms: int | None = None) -> int:
        if self.latest_timestamp_ms == 0:
            return 0
        current_ms = now_ms if now_ms is not None else int(time.time() * 1000)
        return max(0, current_ms - self.latest_timestamp_ms)

    def is_cluster_stale(self, now_ms: int | None = None) -> bool:
        return self.last_frame_age_ms(now_ms) > STALE_AFTER_MS

    def uptime_ms(self, now_ms: int | None = None) -> int:
        current_ms = now_ms if now_ms is not None else current_time_ms()
        return max(0, current_ms - self.started_at_ms)

    def last_broadcast_age_ms(self, now_ms: int | None = None) -> int:
        if self.latest_broadcast_ms == 0:
            return 0
        current_ms = now_ms if now_ms is not None else current_time_ms()
        return max(0, current_ms - self.latest_broadcast_ms)


runtime = RuntimeState()


def current_time_ms() -> int:
    return int(time.time() * 1000)


def register_client(client_id: int, queue_size: int = 1) -> asyncio.Queue[str]:
    queue: asyncio.Queue[str] = asyncio.Queue(maxsize=queue_size)
    runtime.connected_clients[client_id] = queue
    return queue


def unregister_client(client_id: int) -> None:
    runtime.connected_clients.pop(client_id, None)


def publish_frame(payload: str) -> int:
    dropped = 0
    for queue in runtime.connected_clients.values():
        if queue.full():
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            dropped += 1
    runtime.latest_broadcast_ms = current_time_ms()
    runtime.broadcasts_dropped += dropped
    return dropped


def _node_detail_from_state(node_id: str, node_state: RollingNodeState) -> NodeDetail:
    metrics = [RawNodeMetric.model_validate(item) for item in node_state.metrics]
    current = metrics[-1]
    offset_history: Deque[float] = node_state.offsets
    latency_history: Deque[float] = node_state.latencies

    offset_history_without_current = list(offset_history)[:-1]
    latency_history_without_current = list(latency_history)[:-1]

    offset_z = z_score(current.clock_offset_ns, offset_history_without_current)
    latency_z = z_score(current.p2p_latency_us, latency_history_without_current)

    anomaly = NodeAnomaly(
        offset_zscore=round(offset_z, 3),
        latency_zscore=round(latency_z, 3),
        is_straggler=should_flag_straggler(offset_z, latency_z, current.packet_loss_pct),
        recommendation=recommendation_for(abs(offset_z), abs(latency_z), current.packet_loss_pct),
    )
    return NodeDetail(
        node_id=node_id,
        host_id=current.host_id,
        recent_metrics=metrics,
        anomaly=anomaly,
    )


def ingest_metric(metric: RawNodeMetric) -> NodeDetail:
    node_state = runtime.nodes.setdefault(metric.node_id, RollingNodeState())
    node_state.metrics.append(metric.model_dump())
    node_state.offsets.append(metric.clock_offset_ns)
    node_state.latencies.append(metric.p2p_latency_us)
    node_state.packet_losses.append(metric.packet_loss_pct)
    node_state.last_seen_ms = metric.timestamp_ms

    detail = _node_detail_from_state(metric.node_id, node_state)
    runtime.latest_detail[metric.node_id] = detail
    runtime.latest_timestamp_ms = max(runtime.latest_timestamp_ms, metric.timestamp_ms)
    return detail


def ingest_metrics(metrics: list[RawNodeMetric]) -> list[str]:
    changed_ids: list[str] = []
    seen: set[str] = set()
    for metric in metrics:
        ingest_metric(metric)
        if metric.node_id not in seen:
            changed_ids.append(metric.node_id)
            seen.add(metric.node_id)
    runtime.messages_processed += len(metrics)
    return changed_ids


def build_cluster_summary(now_ms: int | None = None) -> ClusterSummary:
    current_ms = now_ms if now_ms is not None else current_time_ms()
    details = list(runtime.latest_detail.values())
    if not details:
        return ClusterSummary(
            health_score=100.0,
            straggler_count=0,
            mean_offset_ns=0.0,
            p95_latency_us=0.0,
            sync_stability_index=1.0,
            is_stale=True,
            last_frame_age_ms=0,
        )

    latest_metrics = [detail.recent_metrics[-1] for detail in details if detail.recent_metrics]
    offsets = [metric.clock_offset_ns for metric in latest_metrics]
    latencies = [metric.p2p_latency_us for metric in latest_metrics]
    packet_losses = [metric.packet_loss_pct for metric in latest_metrics]
    straggler_count = sum(1 for detail in details if detail.anomaly.is_straggler)
    stale_count = sum(1 for metric in latest_metrics if current_ms - metric.timestamp_ms > STALE_AFTER_MS)
    stale_ratio = stale_count / len(latest_metrics) if latest_metrics else 1.0
    mean_offset_ns = sum(offsets) / len(offsets) if offsets else 0.0
    p95_latency_us = percentile(latencies, 0.95)
    mean_packet_loss_pct = sum(packet_losses) / len(packet_losses) if packet_losses else 0.0
    score = health_score(
        straggler_count=straggler_count,
        mean_offset_ns=mean_offset_ns,
        p95_latency_us=p95_latency_us,
        mean_packet_loss_pct=mean_packet_loss_pct,
        stale_ratio=stale_ratio,
    )

    return ClusterSummary(
        health_score=score,
        straggler_count=straggler_count,
        mean_offset_ns=round(mean_offset_ns, 2),
        p95_latency_us=round(p95_latency_us, 2),
        sync_stability_index=stability_index(score),
        is_stale=stale_ratio > 0.05,
        last_frame_age_ms=runtime.last_frame_age_ms(current_ms),
    )


def compute_health_reason(
    upstream_connected: bool,
    cluster: ClusterSummary | None,
    age_ms: int,
) -> HealthReason:
    if not upstream_connected:
        return HealthReason.UPSTREAM_DISCONNECTED
    if cluster is None:
        return HealthReason.WAITING_FOR_FIRST_FRAME
    if age_ms > STALE_AFTER_MS or cluster.is_stale:
        return HealthReason.CLUSTER_STALE
    if cluster.health_score < 70:
        return HealthReason.CLUSTER_DEGRADED
    return HealthReason.OK


def current_cluster_health() -> ClusterSummary | None:
    return runtime.latest_frame.cluster if runtime.latest_frame else None


def build_cluster_frame(changed_node_ids: list[str], now_ms: int | None = None) -> ClusterFrame:
    current_ms = now_ms if now_ms is not None else current_time_ms()
    changed_nodes = []
    straggler_ids: list[str] = []

    for node_id in changed_node_ids:
        detail = runtime.latest_detail.get(node_id)
        if detail is None or not detail.recent_metrics:
            continue
        current_metric = detail.recent_metrics[-1]
        changed_nodes.append(
            {
                "node_id": node_id,
                "clock_offset_ns": current_metric.clock_offset_ns,
                "p2p_latency_us": current_metric.p2p_latency_us,
                "packet_loss_pct": current_metric.packet_loss_pct,
                "severity": classify_severity(
                    detail.anomaly.offset_zscore,
                    detail.anomaly.latency_zscore,
                    current_metric.packet_loss_pct,
                ),
                "is_straggler": detail.anomaly.is_straggler,
            }
        )
        if detail.anomaly.is_straggler:
            straggler_ids.append(node_id)

    summary = build_cluster_summary(current_ms)
    return ClusterFrame(
        timestamp_ms=runtime.latest_timestamp_ms or current_ms,
        cluster=summary,
        changed_nodes=changed_nodes,
        straggler_ids=straggler_ids,
    )


def mark_topology(topology: TopologyResponse, scenario: str, seed: int) -> None:
    runtime.topology = topology
    runtime.scenario = scenario
    runtime.seed = seed


def mark_upstream_status(connected: bool, error: str | None = None) -> None:
    runtime.upstream_connected = connected
    runtime.upstream_error = error
