from __future__ import annotations

import asyncio
import json

import httpx
from fastapi.testclient import TestClient

from app import main as bff_main
from app.models import ClusterFrame, ClusterSummary, NodeAnomaly, NodeDetail, RawNodeMetric, TopologyLink, TopologyNode, TopologyResponse
from app.state import runtime


def setup_function() -> None:
    runtime.reset()


async def _noop() -> None:
    return None


def _seed_runtime() -> None:
    runtime.topology = TopologyResponse(
        nodes=[TopologyNode(id="gpu-00-00", host_id="host-00", group=0)],
        links=[TopologyLink(source="gpu-00-00", target="gpu-00-00", kind="nvlink")],
    )
    runtime.latest_detail["gpu-00-00"] = NodeDetail(
        node_id="gpu-00-00",
        host_id="host-00",
        recent_metrics=[
            RawNodeMetric(
                node_id="gpu-00-00",
                host_id="host-00",
                clock_offset_ns=220.0,
                p2p_latency_us=3.4,
                packet_loss_pct=0.0,
                timestamp_ms=1710000000000,
            )
        ],
        anomaly=NodeAnomaly(
            offset_zscore=2.8,
            latency_zscore=0.9,
            is_straggler=True,
            recommendation="Re-sync node clock to reduce drift before the next training step barrier.",
        ),
    )
    frame = ClusterFrame(
        timestamp_ms=1710000000000,
        cluster=ClusterSummary(
            health_score=68.0,
            straggler_count=1,
            mean_offset_ns=220.0,
            p95_latency_us=3.4,
            sync_stability_index=0.68,
            is_stale=True,
            last_frame_age_ms=2000,
        ),
        changed_nodes=[
            {
                "node_id": "gpu-00-00",
                "clock_offset_ns": 220.0,
                "p2p_latency_us": 3.4,
                "packet_loss_pct": 0.0,
                "severity": "critical",
                "is_straggler": True,
            }
        ],
        straggler_ids=["gpu-00-00"],
    )
    runtime.latest_frame = frame
    runtime.latest_frame_payload = frame.model_dump_json()
    runtime.latest_timestamp_ms = 1710000000000
    runtime.upstream_connected = True


def test_health_and_stream_surface_cluster_state(monkeypatch) -> None:
    monkeypatch.setattr(bff_main.service, "load_bootstrap_data", _noop)
    monkeypatch.setattr(bff_main.service, "ingest_upstream", _noop)

    class FakeScenarioResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "name": "baseline",
                "seed": 42,
                "mode": "auto",
                "control_active": False,
                "step": 0,
            }

    class FakeClient:
        async def get(self, url: str, timeout: float):
            assert url.endswith("/scenario")
            return FakeScenarioResponse()

        async def post(self, url: str, json: dict[str, object], timeout: float):
            raise httpx.ConnectError("simulator unavailable")

        async def aclose(self) -> None:
            return None

    async def fake_client_factory() -> FakeClient:
        return FakeClient()

    monkeypatch.setattr(bff_main.service, "_client", fake_client_factory)
    _seed_runtime()

    with TestClient(bff_main.app) as client:
        response = client.get("/api/health")
        payload = response.json()
        assert payload["status"] == "degraded"
        assert payload["reason_code"] == "cluster_stale"
        assert payload["cluster"]["straggler_count"] == 1
        assert payload["scenario"] == "baseline"
        assert payload["last_frame_age_ms"] >= 0

        detail = client.get("/api/nodes/gpu-00-00").json()
        assert detail["anomaly"]["is_straggler"] is True
        assert "Re-sync" in detail["anomaly"]["recommendation"]

        metrics = client.get("/api/metrics").json()
        assert metrics["messages_processed"] == 0
        assert metrics["reason_code"] == "cluster_stale"

        scenario = client.get("/api/scenario").json()
        assert scenario["name"] == "baseline"
        assert scenario["control_supported"] is True
        assert scenario["control_url"] == "http://localhost:8080/scenario/control"

        control = client.post("/api/scenario", json={"scenario": "straggler-burst", "seed": 17, "reason": "demo"}).json()
        assert control["accepted"] is False
        assert control["supported"] is True

        with client.websocket_connect("/api/stream") as websocket:
            received = json.loads(websocket.receive_text())
            assert received["cluster"]["health_score"] == 68.0
            assert received["straggler_ids"] == ["gpu-00-00"]
