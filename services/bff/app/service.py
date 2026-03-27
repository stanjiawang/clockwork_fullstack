from __future__ import annotations

import asyncio
import json
import logging
from contextlib import suppress
from typing import Any

import httpx
import websockets
from fastapi import WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed, WebSocketException

from .config import Settings
from .control import (
    build_scenario_control_payload,
    build_scenario_control_unavailable,
    build_scenario_status_response,
)
from .models import (
    HealthResponse,
    NodeAnomaly,
    NodeDetail,
    RawNodeMetric,
    ScenarioControlRequest,
    ScenarioControlResponse,
    ScenarioStatusResponse,
    ServiceMetricsResponse,
    TopologyResponse,
)
from .observability import build_service_metrics
from .state import (
    build_cluster_frame,
    compute_health_reason,
    ingest_metrics,
    mark_topology,
    mark_upstream_status,
    publish_frame,
    register_client,
    runtime,
    unregister_client,
)


logger = logging.getLogger(__name__)

DEFAULT_NODE_RECOMMENDATION = "Node has not emitted metrics yet."


class BFFService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._http_client: httpx.AsyncClient | None = None

    async def startup(self) -> None:
        self._http_client = httpx.AsyncClient(timeout=self.settings.bootstrap_timeout_s)
        try:
            await self._load_bootstrap_with_retries()
        except Exception:
            await self.shutdown()
            raise

    async def _load_bootstrap_with_retries(self) -> None:
        attempt = 0
        delay = self.settings.bootstrap_retry_delay_s
        while True:
            attempt += 1
            try:
                await self.load_bootstrap_data()
                return
            except (httpx.HTTPError, OSError, ValueError, json.JSONDecodeError, asyncio.TimeoutError) as exc:
                if attempt >= self.settings.bootstrap_max_attempts:
                    raise
                logger.warning(
                    "bootstrap retrying",
                    extra={
                        "attempt": attempt,
                        "max_attempts": self.settings.bootstrap_max_attempts,
                        "retry_delay_s": delay,
                        "error": str(exc),
                    },
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.settings.bootstrap_retry_delay_cap_s)

    async def shutdown(self) -> None:
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def _client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self.settings.bootstrap_timeout_s)
        return self._http_client

    async def load_bootstrap_data(self) -> None:
        client = await self._client()
        topology_response = await client.get(f"{self.settings.simulator_http_url}/topology")
        topology_response.raise_for_status()
        topology = TopologyResponse.model_validate(topology_response.json())

        scenario_response = await client.get(f"{self.settings.simulator_http_url}/scenario")
        scenario_response.raise_for_status()
        scenario_payload = scenario_response.json()
        scenario = scenario_payload.get("name", "baseline")
        seed = scenario_payload.get("seed", 42)

        mark_topology(topology, scenario, seed)
        logger.info("bootstrap loaded", extra={"scenario": scenario, "seed": seed})

    async def current_scenario(self) -> ScenarioStatusResponse:
        if not self.settings.simulator_scenario_control_url:
            return build_scenario_status_response(control_url=self.settings.simulator_scenario_control_url)

        client = await self._client()
        try:
            response = await client.get(
                f"{self.settings.simulator_http_url}/scenario",
                timeout=self.settings.scenario_control_timeout_s,
            )
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                return build_scenario_status_response(
                    control_url=self.settings.simulator_scenario_control_url,
                    upstream_payload=payload,
                )
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("scenario status fetch failed", extra={"error": str(exc)})
        return build_scenario_status_response(control_url=self.settings.simulator_scenario_control_url)

    async def metrics(self) -> ServiceMetricsResponse:
        return build_service_metrics()

    async def ingest_upstream(self) -> None:
        reconnect_delay = self.settings.reconnect_delay_floor_s
        while True:
            try:
                async with websockets.connect(
                    self.settings.simulator_ws_url,
                    open_timeout=self.settings.upstream_open_timeout_s,
                    ping_interval=self.settings.upstream_ping_interval_s,
                    ping_timeout=self.settings.upstream_ping_timeout_s,
                    max_size=self.settings.upstream_max_message_bytes,
                ) as websocket:
                    mark_upstream_status(True, None)
                    reconnect_delay = self.settings.reconnect_delay_floor_s
                    async for raw_message in websocket:
                        changed_nodes = self._process_upstream_message(raw_message)
                        if not changed_nodes:
                            continue
                        frame = build_cluster_frame(changed_nodes)
                        runtime.latest_frame = frame
                        runtime.latest_frame_payload = frame.model_dump_json()
                        dropped = publish_frame(runtime.latest_frame_payload)
                        logger.debug(
                            "published cluster frame",
                            extra={
                                "changed_nodes": len(frame.changed_nodes),
                                "health_score": frame.cluster.health_score,
                                "straggler_count": frame.cluster.straggler_count,
                                "dropped_clients": dropped,
                                "messages_processed": runtime.messages_processed,
                            },
                        )
            except (httpx.HTTPError, ConnectionClosed, OSError, WebSocketException, json.JSONDecodeError, ValueError) as exc:  # pragma: no cover - network recovery path
                mark_upstream_status(False, str(exc))
                logger.warning("upstream reconnecting", extra={"error": str(exc)})
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, self.settings.reconnect_delay_ceiling_s)

    def _process_upstream_message(self, raw_message: str) -> list[str]:
        payload: Any = json.loads(raw_message)
        if isinstance(payload, list):
            metrics = [RawNodeMetric.model_validate(item) for item in payload]
        else:
            metrics = [RawNodeMetric.model_validate(payload)]
        return ingest_metrics(metrics)

    @staticmethod
    def _placeholder_detail(node_id: str) -> NodeDetail:
        return NodeDetail(
            node_id=node_id,
            host_id="unknown",
            recent_metrics=[],
            anomaly=NodeAnomaly(
                offset_zscore=0.0,
                latency_zscore=0.0,
                is_straggler=False,
                recommendation=DEFAULT_NODE_RECOMMENDATION,
            ),
        )

    async def health(self) -> HealthResponse:
        cluster = runtime.latest_frame.cluster if runtime.latest_frame else None
        age_ms = runtime.last_frame_age_ms()
        status = "ok"
        message = "FastAPI aggregation service"
        if not runtime.upstream_connected:
            status = "degraded"
            message = "Upstream stream disconnected"
        elif cluster is None:
            status = "degraded"
            message = "Waiting for first cluster frame"
        elif age_ms > 1500 or cluster.is_stale or cluster.health_score < 70:
            status = "degraded"
            message = "Cluster frame is stale or degraded"
        reason_code = compute_health_reason(runtime.upstream_connected, cluster, age_ms)

        return HealthResponse(
            status=status,
            reason_code=reason_code,
            upstream_connected=runtime.upstream_connected,
            connected_clients=runtime.client_count(),
            last_frame_age_ms=age_ms,
            upstream_error=runtime.upstream_error,
            cluster=cluster,
            seed=runtime.seed,
            scenario=runtime.scenario,
            message=message,
        )

    async def topology(self) -> TopologyResponse:
        if runtime.topology is None:
            await self.load_bootstrap_data()
        assert runtime.topology is not None
        return runtime.topology

    async def node_detail(self, node_id: str) -> NodeDetail:
        detail = runtime.latest_detail.get(node_id)
        if detail is not None:
            return detail
        return self._placeholder_detail(node_id)

    async def control_scenario(self, request: ScenarioControlRequest) -> ScenarioControlResponse:
        if not self.settings.simulator_scenario_control_url:
            return build_scenario_control_unavailable(request)

        client = await self._client()
        try:
            response = await client.post(
                self.settings.simulator_scenario_control_url,
                json=build_scenario_control_payload(request),
                timeout=self.settings.scenario_control_timeout_s,
            )
            response.raise_for_status()
            upstream_payload: dict[str, Any] | None
            if response.content:
                payload = response.json()
                upstream_payload = payload if isinstance(payload, dict) else {"data": payload}
            else:
                upstream_payload = None
            return ScenarioControlResponse(
                accepted=True,
                supported=True,
                scenario=request.scenario,
                seed=request.seed,
                control_url=self.settings.simulator_scenario_control_url,
                upstream_status_code=response.status_code,
                upstream_response=upstream_payload,
                message="Scenario control request proxied successfully.",
            )
        except (httpx.HTTPError, ValueError) as exc:
            return ScenarioControlResponse(
                accepted=False,
                supported=True,
                scenario=request.scenario,
                seed=request.seed,
                control_url=self.settings.simulator_scenario_control_url,
                upstream_status_code=getattr(getattr(exc, "response", None), "status_code", None),
                upstream_response=None,
                message=f"Scenario control proxy failed: {exc}",
            )

    async def stream_client(self, websocket: WebSocket) -> None:
        await websocket.accept()
        client_id = id(websocket)
        queue = register_client(client_id, queue_size=self.settings.client_queue_size)
        if runtime.latest_frame_payload:
            with suppress(asyncio.QueueFull):
                queue.put_nowait(runtime.latest_frame_payload)

        try:
            while True:
                payload = await queue.get()
                await websocket.send_text(payload)
        except WebSocketDisconnect:
            logger.info("stream client disconnected", extra={"client_id": client_id})
        finally:
            unregister_client(client_id)
