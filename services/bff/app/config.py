from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse


@dataclass(frozen=True)
class Settings:
    simulator_http_url: str = "http://localhost:8080"
    simulator_ws_url: str = "ws://localhost:8080/stream"
    simulator_scenario_control_url: str | None = None
    bootstrap_timeout_s: float = 5.0
    bootstrap_max_attempts: int = 10
    bootstrap_retry_delay_s: float = 0.5
    bootstrap_retry_delay_cap_s: float = 5.0
    upstream_open_timeout_s: float = 5.0
    upstream_ping_interval_s: float = 20.0
    upstream_ping_timeout_s: float = 20.0
    upstream_max_message_bytes: int = 8 * 1024 * 1024
    client_queue_size: int = 1
    reconnect_delay_floor_s: float = 1.0
    reconnect_delay_ceiling_s: float = 5.0
    scenario_control_timeout_s: float = 5.0
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        if self.simulator_scenario_control_url is None:
            object.__setattr__(
                self,
                "simulator_scenario_control_url",
                _derive_scenario_control_url(self.simulator_http_url),
            )

    @classmethod
    def from_env(cls) -> "Settings":
        settings = cls(
            simulator_http_url=_validate_url(
                os.getenv("SIMULATOR_HTTP_URL", cls.simulator_http_url),
                ("http", "https"),
                "SIMULATOR_HTTP_URL",
            ),
            simulator_ws_url=_validate_url(
                os.getenv("SIMULATOR_WS_URL", cls.simulator_ws_url),
                ("ws", "wss"),
                "SIMULATOR_WS_URL",
            ),
            simulator_scenario_control_url=_validate_optional_url(
                os.getenv("SIMULATOR_SCENARIO_CONTROL_URL"),
                ("http", "https"),
                "SIMULATOR_SCENARIO_CONTROL_URL",
            ),
            bootstrap_timeout_s=_parse_positive_float(
                os.getenv("BFF_BOOTSTRAP_TIMEOUT_S", str(cls.bootstrap_timeout_s)),
                "BFF_BOOTSTRAP_TIMEOUT_S",
            ),
            bootstrap_max_attempts=_parse_positive_int(
                os.getenv("BFF_BOOTSTRAP_MAX_ATTEMPTS", str(cls.bootstrap_max_attempts)),
                "BFF_BOOTSTRAP_MAX_ATTEMPTS",
            ),
            bootstrap_retry_delay_s=_parse_positive_float(
                os.getenv("BFF_BOOTSTRAP_RETRY_DELAY_S", str(cls.bootstrap_retry_delay_s)),
                "BFF_BOOTSTRAP_RETRY_DELAY_S",
            ),
            bootstrap_retry_delay_cap_s=_parse_positive_float(
                os.getenv("BFF_BOOTSTRAP_RETRY_DELAY_CAP_S", str(cls.bootstrap_retry_delay_cap_s)),
                "BFF_BOOTSTRAP_RETRY_DELAY_CAP_S",
            ),
            upstream_open_timeout_s=_parse_positive_float(
                os.getenv("BFF_UPSTREAM_OPEN_TIMEOUT_S", str(cls.upstream_open_timeout_s)),
                "BFF_UPSTREAM_OPEN_TIMEOUT_S",
            ),
            upstream_ping_interval_s=_parse_positive_float(
                os.getenv("BFF_UPSTREAM_PING_INTERVAL_S", str(cls.upstream_ping_interval_s)),
                "BFF_UPSTREAM_PING_INTERVAL_S",
            ),
            upstream_ping_timeout_s=_parse_positive_float(
                os.getenv("BFF_UPSTREAM_PING_TIMEOUT_S", str(cls.upstream_ping_timeout_s)),
                "BFF_UPSTREAM_PING_TIMEOUT_S",
            ),
            upstream_max_message_bytes=_parse_positive_int(
                os.getenv("BFF_UPSTREAM_MAX_MESSAGE_BYTES", str(cls.upstream_max_message_bytes)),
                "BFF_UPSTREAM_MAX_MESSAGE_BYTES",
            ),
            client_queue_size=_parse_positive_int(
                os.getenv("BFF_CLIENT_QUEUE_SIZE", str(cls.client_queue_size)),
                "BFF_CLIENT_QUEUE_SIZE",
            ),
            reconnect_delay_floor_s=_parse_positive_float(
                os.getenv("BFF_RECONNECT_DELAY_FLOOR_S", str(cls.reconnect_delay_floor_s)),
                "BFF_RECONNECT_DELAY_FLOOR_S",
            ),
            reconnect_delay_ceiling_s=_parse_positive_float(
                os.getenv("BFF_RECONNECT_DELAY_CEILING_S", str(cls.reconnect_delay_ceiling_s)),
                "BFF_RECONNECT_DELAY_CEILING_S",
            ),
            scenario_control_timeout_s=_parse_positive_float(
                os.getenv("BFF_SCENARIO_CONTROL_TIMEOUT_S", str(cls.scenario_control_timeout_s)),
                "BFF_SCENARIO_CONTROL_TIMEOUT_S",
            ),
            log_level=os.getenv("BFF_LOG_LEVEL", cls.log_level).upper(),
        )
        if settings.reconnect_delay_ceiling_s < settings.reconnect_delay_floor_s:
            raise ValueError("BFF_RECONNECT_DELAY_CEILING_S must be greater than or equal to BFF_RECONNECT_DELAY_FLOOR_S")
        return settings


def _validate_url(raw_value: str, schemes: tuple[str, ...], env_name: str) -> str:
    parsed = urlparse(raw_value)
    if parsed.scheme not in schemes or not parsed.netloc:
        raise ValueError(f"{env_name} must be a valid {'/'.join(schemes)} URL")
    return raw_value


def _validate_optional_url(raw_value: str | None, schemes: tuple[str, ...], env_name: str) -> str | None:
    if raw_value is None or raw_value == "":
        return None
    return _validate_url(raw_value, schemes, env_name)


def _derive_scenario_control_url(simulator_http_url: str) -> str:
    return urljoin(f"{simulator_http_url.rstrip('/')}/", "scenario/control")


def _parse_positive_float(raw_value: str, env_name: str) -> float:
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{env_name} must be a number") from exc
    if value <= 0:
        raise ValueError(f"{env_name} must be greater than 0")
    return value


def _parse_positive_int(raw_value: str, env_name: str) -> int:
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{env_name} must be an integer") from exc
    if value <= 0:
        raise ValueError(f"{env_name} must be greater than 0")
    return value
