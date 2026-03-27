from __future__ import annotations

from typing import Any

from .models import ScenarioControlRequest, ScenarioControlResponse, ScenarioStatusResponse
from .state import runtime


def build_scenario_status_response(
    *,
    control_url: str | None = None,
    upstream_payload: dict[str, Any] | None = None,
) -> ScenarioStatusResponse:
    payload = upstream_payload or {}
    return ScenarioStatusResponse(
        name=str(payload.get("name", runtime.scenario)),
        seed=payload.get("seed", runtime.seed),
        mode=payload.get("mode"),
        control_active=bool(payload.get("control_active", bool(control_url))),
        override_until_step=payload.get("override_until_step"),
        step=payload.get("step"),
        control_supported=bool(control_url),
        control_url=control_url,
        message="Scenario metadata sourced from the simulator runtime payload.",
    )


def build_scenario_control_unavailable(request: ScenarioControlRequest, control_url: str | None = None) -> ScenarioControlResponse:
    return ScenarioControlResponse(
        accepted=False,
        supported=bool(control_url),
        scenario=request.scenario,
        seed=request.seed,
        control_url=control_url,
        upstream_status_code=None,
        upstream_response=None,
        message="Scenario control proxy is not configured.",
    )


def build_scenario_control_payload(request: ScenarioControlRequest) -> dict[str, Any]:
    payload: dict[str, Any] = {"mode": request.scenario}
    if request.duration_steps is not None:
        payload["duration_steps"] = request.duration_steps
    return payload
