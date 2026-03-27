from __future__ import annotations

import asyncio

import httpx

from app.config import Settings
from app.models import ClusterFrame, ClusterSummary, NodeAnomaly, NodeDetail, RawNodeMetric, ScenarioControlRequest
from app.service import BFFService
from app.state import runtime


def setup_function() -> None:
    runtime.reset()


def _seed_cluster(*, health_score: float = 95.0, age_ms: int = 0, upstream_connected: bool = True) -> None:
    runtime.latest_detail["gpu-00-00"] = NodeDetail(
        node_id="gpu-00-00",
        host_id="host-00",
        recent_metrics=[
            RawNodeMetric(
                node_id="gpu-00-00",
                host_id="host-00",
                clock_offset_ns=125.0,
                p2p_latency_us=2.2,
                packet_loss_pct=0.01,
                timestamp_ms=1710000000000 - age_ms,
            )
        ],
        anomaly=NodeAnomaly(
            offset_zscore=0.5,
            latency_zscore=0.2,
            is_straggler=False,
            recommendation="Continue monitoring. No immediate operator action required.",
        ),
    )
    runtime.latest_timestamp_ms = 1710000000000 - age_ms
    runtime.latest_frame = ClusterFrame(
        timestamp_ms=runtime.latest_timestamp_ms,
        cluster=ClusterSummary(
            health_score=health_score,
            straggler_count=0,
            mean_offset_ns=125.0,
            p95_latency_us=2.2,
            sync_stability_index=round(health_score / 100.0, 3),
            is_stale=age_ms > 1500,
            last_frame_age_ms=age_ms,
        ),
        changed_nodes=[],
        straggler_ids=[],
    )
    runtime.upstream_connected = upstream_connected


def test_health_reports_upstream_disconnect() -> None:
    service = BFFService(Settings())
    _seed_cluster(upstream_connected=False)

    response = asyncio.run(service.health())

    assert response.status == "degraded"
    assert response.reason_code == "upstream_disconnected"
    assert response.upstream_connected is False
    assert response.message == "Upstream stream disconnected"


def test_health_reports_degraded_cluster() -> None:
    service = BFFService(Settings())
    _seed_cluster(health_score=62.0, age_ms=2000)

    response = asyncio.run(service.health())

    assert response.status == "degraded"
    assert response.reason_code == "cluster_stale"
    assert response.last_frame_age_ms >= 0
    assert response.cluster is not None
    assert response.cluster.health_score == 62.0


def test_node_detail_returns_placeholder_for_unknown_node() -> None:
    service = BFFService(Settings())

    response = asyncio.run(service.node_detail("gpu-missing"))

    assert response.node_id == "gpu-missing"
    assert response.recent_metrics == []
    assert response.anomaly.is_straggler is False


def test_metrics_report_runtime_counters() -> None:
    service = BFFService(Settings())
    _seed_cluster(health_score=88.0)
    runtime.messages_processed = 123
    runtime.broadcasts_dropped = 4

    metrics = asyncio.run(service.metrics())

    assert metrics.messages_processed == 123
    assert metrics.broadcasts_dropped == 4
    assert metrics.cluster_health_score == 88.0
    assert metrics.topology_loaded is False


def test_scenario_status_reports_control_enabled_by_default() -> None:
    service = BFFService(Settings())
    async def fake_client_factory():
        class FakeClient:
            async def get(self, url: str, timeout: float):
                raise httpx.ConnectError("simulator unavailable")

            async def aclose(self) -> None:
                return None

        return FakeClient()

    service._client = fake_client_factory  # type: ignore[method-assign]

    scenario = asyncio.run(service.current_scenario())

    assert scenario.name == "baseline"
    assert scenario.control_supported is True
    assert scenario.control_url == "http://localhost:8080/scenario/control"


def test_control_scenario_reports_proxy_failure_when_upstream_is_unreachable() -> None:
    service = BFFService(
        Settings(
            simulator_scenario_control_url="http://127.0.0.1:9/scenario/control",
        )
    )
    request = ScenarioControlRequest(scenario="straggler-burst", seed=7, reason="demo")

    response = asyncio.run(service.control_scenario(request))

    assert response.accepted is False
    assert response.supported is True
    assert response.scenario == "straggler-burst"
    assert response.control_url == "http://127.0.0.1:9/scenario/control"
    assert "proxy failed" in response.message


def test_control_scenario_proxies_when_configured(monkeypatch) -> None:
    service = BFFService(
        Settings(
            simulator_scenario_control_url="http://simulator.example/scenario/control",
        )
    )

    class FakeResponse:
        status_code = 200
        content = b'{"ok": true}'

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, bool]:
            return {"ok": True}

    class FakeClient:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, dict[str, object]]] = []

        async def post(self, url: str, json: dict[str, object], timeout: float):
            self.calls.append((url, "POST", json))
            return FakeResponse()

        async def aclose(self) -> None:
            return None

    fake_client = FakeClient()

    async def fake_client_factory() -> FakeClient:
        return fake_client

    monkeypatch.setattr(service, "_client", fake_client_factory)

    response = asyncio.run(
        service.control_scenario(
            ScenarioControlRequest(scenario="straggler-burst", seed=99, reason="test"),
        )
    )

    assert response.accepted is True
    assert response.supported is True
    assert response.upstream_status_code == 200
    assert response.upstream_response == {"ok": True}


def test_startup_closes_http_client_on_bootstrap_failure(monkeypatch) -> None:
    service = BFFService(Settings())

    async def boom() -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(service, "load_bootstrap_data", boom)

    try:
        asyncio.run(service.startup())
    except RuntimeError:
        pass

    assert service._http_client is None


def test_startup_retries_transient_bootstrap_failure(monkeypatch) -> None:
    service = BFFService(
        Settings(
            bootstrap_max_attempts=3,
            bootstrap_retry_delay_s=0.01,
            bootstrap_retry_delay_cap_s=0.01,
        )
    )
    attempts = {"count": 0}

    async def flaky_bootstrap() -> None:
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise httpx.ConnectError("temporary bootstrap failure")

    async def fast_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(service, "load_bootstrap_data", flaky_bootstrap)
    monkeypatch.setattr("app.service.asyncio.sleep", fast_sleep)

    asyncio.run(service.startup())

    assert attempts["count"] == 2
