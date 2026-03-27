from __future__ import annotations

import time

from app.models import RawNodeMetric
from app.state import build_cluster_frame, ingest_metrics, publish_frame, register_client, runtime, unregister_client


def setup_function() -> None:
    runtime.reset()


def _metric(node_id: str, offset: float, latency: float, packet_loss: float, timestamp_ms: int) -> RawNodeMetric:
    host_id = node_id.split("-")[1]
    return RawNodeMetric(
        node_id=node_id,
        host_id=f"host-{host_id}",
        clock_offset_ns=offset,
        p2p_latency_us=latency,
        packet_loss_pct=packet_loss,
        timestamp_ms=timestamp_ms,
    )


def test_build_cluster_frame_uses_patch_nodes_only() -> None:
    timestamp_ms = int(time.time() * 1000)
    metrics = [
        _metric("gpu-00-00", 15.0, 1.8, 0.0, timestamp_ms),
        _metric("gpu-00-01", 18.0, 1.9, 0.75, timestamp_ms),
        _metric("gpu-00-02", 14.0, 1.7, 0.0, timestamp_ms),
    ]

    changed_ids = ingest_metrics(metrics)
    frame = build_cluster_frame(changed_ids, now_ms=timestamp_ms)

    assert [node.node_id for node in frame.changed_nodes] == [
        "gpu-00-00",
        "gpu-00-01",
        "gpu-00-02",
    ]
    assert frame.straggler_ids == ["gpu-00-01"]
    assert frame.cluster.straggler_count == 1
    assert frame.cluster.health_score < 100.0
    assert frame.cluster.is_stale is False


def test_publish_frame_replaces_stale_queue_items() -> None:
    queue = register_client(1)
    try:
        queue.put_nowait("stale")
        publish_frame("fresh")
        assert queue.get_nowait() == "fresh"
        assert runtime.broadcasts_dropped == 0
    finally:
        unregister_client(1)
