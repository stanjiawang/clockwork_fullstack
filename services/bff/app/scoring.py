from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from math import sqrt
from statistics import mean
from typing import Deque, Iterable


WINDOW_SIZE = 24
STRAGGLER_Z_THRESHOLD = 2.5
WARN_Z_THRESHOLD = 1.5
PACKET_LOSS_STRAGGLER_THRESHOLD = 0.5


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def rolling_mean(values: Iterable[float]) -> float:
    samples = list(values)
    return mean(samples) if samples else 0.0


def rolling_stddev(values: Iterable[float]) -> float:
    samples = list(values)
    if len(samples) < 2:
        return 0.0
    avg = mean(samples)
    variance = sum((value - avg) ** 2 for value in samples) / len(samples)
    return sqrt(variance)


def z_score(value: float, history: Iterable[float]) -> float:
    samples = list(history)
    if not samples:
        return 0.0
    avg = rolling_mean(samples)
    stddev = rolling_stddev(samples)
    if stddev == 0.0:
        return 0.0
    return (value - avg) / stddev


def percentile(values: Iterable[float], ratio: float) -> float:
    samples = sorted(values)
    if not samples:
        return 0.0
    if ratio <= 0:
        return samples[0]
    if ratio >= 1:
        return samples[-1]

    index = (len(samples) - 1) * ratio
    lower = int(index)
    upper = min(len(samples) - 1, lower + 1)
    if lower == upper:
        return samples[lower]
    return samples[lower] + (samples[upper] - samples[lower]) * (index - lower)


def classify_severity(offset_z: float, latency_z: float, packet_loss_pct: float) -> str:
    signal = max(abs(offset_z), abs(latency_z))
    if signal >= STRAGGLER_Z_THRESHOLD or packet_loss_pct >= PACKET_LOSS_STRAGGLER_THRESHOLD:
        return "critical"
    if signal >= WARN_Z_THRESHOLD or packet_loss_pct >= 0.1:
        return "warn"
    return "healthy"


def should_flag_straggler(offset_z: float, latency_z: float, packet_loss_pct: float) -> bool:
    return (
        abs(offset_z) >= STRAGGLER_Z_THRESHOLD
        or abs(latency_z) >= STRAGGLER_Z_THRESHOLD
        or packet_loss_pct >= PACKET_LOSS_STRAGGLER_THRESHOLD
    )


def recommendation_for(offset_z: float, latency_z: float, packet_loss_pct: float) -> str:
    if packet_loss_pct >= PACKET_LOSS_STRAGGLER_THRESHOLD:
        return "Inspect the fabric path for packet loss and reroute or isolate the affected workload."
    if offset_z >= latency_z and offset_z >= STRAGGLER_Z_THRESHOLD:
        return "Re-sync node clock to reduce drift before the next training step barrier."
    if latency_z >= STRAGGLER_Z_THRESHOLD:
        return "Consider migrating the training shard if latency remains elevated after sync stabilizes."
    if offset_z >= WARN_Z_THRESHOLD or latency_z >= WARN_Z_THRESHOLD:
        return "Monitor the node closely and verify sync stability before the drift widens."
    return "Continue monitoring. No immediate operator action required."


def health_score(
    *,
    straggler_count: int,
    mean_offset_ns: float,
    p95_latency_us: float,
    mean_packet_loss_pct: float,
    stale_ratio: float,
) -> float:
    penalties = (
        min(30.0, straggler_count * 4.0)
        + min(22.0, p95_latency_us * 3.0)
        + min(18.0, abs(mean_offset_ns) / 40.0)
        + min(18.0, mean_packet_loss_pct * 20.0)
        + min(20.0, stale_ratio * 40.0)
    )
    return round(clamp(100.0 - penalties, 0.0, 100.0), 2)


def stability_index(health: float) -> float:
    return round(clamp(health / 100.0, 0.0, 1.0), 3)


@dataclass
class RollingNodeState:
    metrics: Deque[dict] = field(default_factory=lambda: deque(maxlen=WINDOW_SIZE))
    offsets: Deque[float] = field(default_factory=lambda: deque(maxlen=WINDOW_SIZE))
    latencies: Deque[float] = field(default_factory=lambda: deque(maxlen=WINDOW_SIZE))
    packet_losses: Deque[float] = field(default_factory=lambda: deque(maxlen=WINDOW_SIZE))
    last_seen_ms: int = 0
