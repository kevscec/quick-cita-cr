from __future__ import annotations

import random
from datetime import timedelta

from .config import ScheduleConfig


def next_sleep_seconds(config: ScheduleConfig) -> float:
    base = config.interval_minutes * 60
    spread = base * (config.jitter_percent / 100)
    return max(60.0, base + random.uniform(-spread, spread))


def pause_after_failures(config: ScheduleConfig) -> timedelta:
    return timedelta(minutes=config.pause_minutes_after_failures)
