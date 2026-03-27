from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import websockets


ROOT = Path(__file__).resolve().parents[2]
SIMULATOR_DIR = ROOT / "services" / "simulator"
SIMULATOR_PORT = 18080
BFF_PORT = 18000


def wait_for_http(url: str, timeout_s: float = 20.0) -> dict:
    deadline = time.time() + timeout_s
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=2.0) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - retry path
            last_error = exc
            time.sleep(0.2)
    raise AssertionError(f"Timed out waiting for {url}: {last_error}")


def start_process(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.Popen[str]:
    return subprocess.Popen(
        command,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        preexec_fn=os.setsid if os.name != "nt" else None,
    )


def stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name != "nt":
            os.killpg(process.pid, signal.SIGTERM)
        else:  # pragma: no cover - windows path
            process.terminate()
        process.wait(timeout=5)
    except Exception:  # pragma: no cover - cleanup fallback
        process.kill()


def test_simulator_and_bff_integration() -> None:
    simulator_env = os.environ.copy()
    simulator_env.update(
        {
            "SIMULATOR_BIND_ADDRESS": f"127.0.0.1:{SIMULATOR_PORT}",
            "SIMULATOR_SEED": "42",
        }
    )
    bff_env = os.environ.copy()
    bff_env.update(
        {
            "PYTHONPATH": str(ROOT),
            "SIMULATOR_HTTP_URL": f"http://127.0.0.1:{SIMULATOR_PORT}",
            "SIMULATOR_WS_URL": f"ws://127.0.0.1:{SIMULATOR_PORT}/stream",
        }
    )

    simulator = start_process(["go", "run", "./cmd/simulator"], cwd=SIMULATOR_DIR, env=simulator_env)
    bff: subprocess.Popen[str] | None = None

    try:
        simulator_health = wait_for_http(f"http://127.0.0.1:{SIMULATOR_PORT}/health")
        assert simulator_health["status"] == "ok"

        bff = start_process(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "services.bff.app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(BFF_PORT),
            ],
            cwd=ROOT,
            env=bff_env,
        )

        bff_health = wait_for_http(f"http://127.0.0.1:{BFF_PORT}/api/health")
        assert bff_health["status"] in {"ok", "degraded"}
        assert "connected_clients" in bff_health

        topology = wait_for_http(f"http://127.0.0.1:{BFF_PORT}/api/topology")
        assert len(topology["nodes"]) == 256
        assert len(topology["links"]) > 0

        node_detail = wait_for_http(f"http://127.0.0.1:{BFF_PORT}/api/nodes/gpu-00-00")
        assert node_detail["node_id"] == "gpu-00-00"
        assert "anomaly" in node_detail

        async def read_stream() -> dict:
            async with websockets.connect(f"ws://127.0.0.1:{BFF_PORT}/api/stream") as websocket:
                payload = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                return json.loads(payload)

        frame = asyncio.run(read_stream())
        assert "cluster" in frame
        assert "changed_nodes" in frame
        assert "straggler_ids" in frame
    finally:
        if bff is not None:
            stop_process(bff)
        stop_process(simulator)
