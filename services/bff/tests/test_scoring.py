from app.scoring import (
    classify_severity,
    health_score,
    percentile,
    recommendation_for,
    should_flag_straggler,
    z_score,
)


def test_z_score_handles_flat_history() -> None:
    assert z_score(10.0, [10.0, 10.0, 10.0]) == 0.0


def test_percentile_uses_interpolation() -> None:
    assert percentile([10.0, 20.0, 30.0, 40.0], 0.75) == 32.5


def test_recommendation_prefers_packet_loss_first() -> None:
    assert "packet loss" in recommendation_for(0.0, 0.0, 0.75)


def test_classification_and_straggler_thresholds_align() -> None:
    assert classify_severity(0.2, 0.1, 0.0) == "healthy"
    assert classify_severity(1.8, 0.1, 0.0) == "warn"
    assert should_flag_straggler(3.0, 0.2, 0.0) is True


def test_cluster_health_penalizes_stragglers_and_staleness() -> None:
    healthy = health_score(
        straggler_count=0,
        mean_offset_ns=0.0,
        p95_latency_us=1.0,
        mean_packet_loss_pct=0.0,
        stale_ratio=0.0,
    )
    degraded = health_score(
        straggler_count=3,
        mean_offset_ns=400.0,
        p95_latency_us=6.0,
        mean_packet_loss_pct=0.6,
        stale_ratio=0.25,
    )
    assert healthy > degraded

