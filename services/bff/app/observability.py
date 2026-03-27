from __future__ import annotations

from .models import HealthReason, ServiceMetricsResponse
from .state import current_cluster_health, compute_health_reason, current_time_ms, runtime


def build_service_metrics(now_ms: int | None = None) -> ServiceMetricsResponse:
    current_ms = now_ms if now_ms is not None else current_time_ms()
    cluster = current_cluster_health()
    reason_code = compute_health_reason(runtime.upstream_connected, cluster, runtime.last_frame_age_ms(current_ms))
    health_status = "ok" if reason_code == HealthReason.OK else "degraded"

    return ServiceMetricsResponse(
        uptime_ms=runtime.uptime_ms(current_ms),
        messages_processed=runtime.messages_processed,
        broadcasts_dropped=runtime.broadcasts_dropped,
        connected_clients=runtime.client_count(),
        latest_frame_age_ms=runtime.last_frame_age_ms(current_ms),
        latest_broadcast_age_ms=runtime.last_broadcast_age_ms(current_ms),
        topology_loaded=runtime.topology is not None,
        upstream_connected=runtime.upstream_connected,
        upstream_error=runtime.upstream_error,
        scenario=runtime.scenario,
        seed=runtime.seed,
        reason_code=reason_code,
        health_status=health_status,
        cluster_health_score=cluster.health_score if cluster else None,
        straggler_count=cluster.straggler_count if cluster else 0,
    )
