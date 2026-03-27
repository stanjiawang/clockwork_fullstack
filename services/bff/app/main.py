from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .logging_config import configure_logging
from .models import (
    HealthResponse,
    NodeDetail,
    ScenarioControlRequest,
    ScenarioControlResponse,
    ScenarioStatusResponse,
    ServiceMetricsResponse,
    TopologyResponse,
)
from .service import BFFService

settings = Settings.from_env()
configure_logging(settings.log_level)
service = BFFService(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await service.startup()
    ingest_task = asyncio.create_task(service.ingest_upstream())
    try:
        yield
    finally:
        ingest_task.cancel()
        with suppress(asyncio.CancelledError):
            await ingest_task
        await service.shutdown()


app = FastAPI(title="Clockwork BFF", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return await service.health()


@app.get("/api/health", response_model=HealthResponse)
async def api_health() -> HealthResponse:
    return await service.health()


@app.get("/api/topology", response_model=TopologyResponse)
async def api_topology() -> TopologyResponse:
    return await service.topology()


@app.get("/api/metrics", response_model=ServiceMetricsResponse)
async def api_metrics() -> ServiceMetricsResponse:
    return await service.metrics()


@app.get("/api/scenario", response_model=ScenarioStatusResponse)
async def api_scenario() -> ScenarioStatusResponse:
    return await service.current_scenario()


@app.post("/api/scenario", response_model=ScenarioControlResponse)
async def api_control_scenario(request: ScenarioControlRequest) -> ScenarioControlResponse:
    return await service.control_scenario(request)


@app.get("/api/nodes/{node_id}", response_model=NodeDetail)
async def api_node_detail(node_id: str) -> NodeDetail:
    return await service.node_detail(node_id)


@app.websocket("/api/stream")
async def api_stream(websocket: WebSocket) -> None:
    await service.stream_client(websocket)
