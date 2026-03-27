from __future__ import annotations

import pytest

from app.config import Settings


def test_settings_from_env_overrides_defaults(monkeypatch) -> None:
    monkeypatch.setenv("SIMULATOR_HTTP_URL", "http://simulator.internal:18080")
    monkeypatch.setenv("SIMULATOR_WS_URL", "ws://simulator.internal:18080/stream")
    monkeypatch.setenv("SIMULATOR_SCENARIO_CONTROL_URL", "http://simulator.internal:18080/scenario/control")
    monkeypatch.setenv("BFF_CLIENT_QUEUE_SIZE", "4")
    monkeypatch.setenv("BFF_LOG_LEVEL", "debug")

    settings = Settings.from_env()

    assert settings.simulator_http_url == "http://simulator.internal:18080"
    assert settings.simulator_ws_url == "ws://simulator.internal:18080/stream"
    assert settings.simulator_scenario_control_url == "http://simulator.internal:18080/scenario/control"
    assert settings.client_queue_size == 4
    assert settings.log_level == "DEBUG"


def test_settings_from_env_derives_scenario_control_url_from_simulator_http_url(monkeypatch) -> None:
    monkeypatch.setenv("SIMULATOR_HTTP_URL", "http://simulator.internal:18080")

    settings = Settings.from_env()

    assert settings.simulator_scenario_control_url == "http://simulator.internal:18080/scenario/control"


@pytest.mark.parametrize(
    "env_name,value,message",
    [
        ("SIMULATOR_HTTP_URL", "ftp://bad", "must be a valid http/https URL"),
        ("SIMULATOR_WS_URL", "http://bad", "must be a valid ws/wss URL"),
        ("SIMULATOR_SCENARIO_CONTROL_URL", "ws://bad", "must be a valid http/https URL"),
        ("BFF_BOOTSTRAP_MAX_ATTEMPTS", "0", "must be greater than 0"),
        ("BFF_BOOTSTRAP_RETRY_DELAY_S", "0", "must be greater than 0"),
        ("BFF_BOOTSTRAP_RETRY_DELAY_CAP_S", "0", "must be greater than 0"),
        ("BFF_CLIENT_QUEUE_SIZE", "0", "must be greater than 0"),
        ("BFF_RECONNECT_DELAY_FLOOR_S", "0", "must be greater than 0"),
        ("BFF_RECONNECT_DELAY_CEILING_S", "-1", "must be greater than 0"),
        ("BFF_SCENARIO_CONTROL_TIMEOUT_S", "0", "must be greater than 0"),
    ],
)
def test_settings_from_env_rejects_invalid_values(monkeypatch, env_name: str, value: str, message: str) -> None:
    monkeypatch.setenv(env_name, value)

    with pytest.raises(ValueError, match=message):
        Settings.from_env()


def test_settings_from_env_rejects_invalid_delay_window(monkeypatch) -> None:
    monkeypatch.setenv("BFF_RECONNECT_DELAY_FLOOR_S", "5")
    monkeypatch.setenv("BFF_RECONNECT_DELAY_CEILING_S", "2")

    with pytest.raises(ValueError, match="BFF_RECONNECT_DELAY_CEILING_S must be greater than or equal to BFF_RECONNECT_DELAY_FLOOR_S"):
        Settings.from_env()
