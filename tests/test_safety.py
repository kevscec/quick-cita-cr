from quick_cita_cr.config import ScheduleConfig
from quick_cita_cr.safety import next_sleep_seconds


def test_next_sleep_seconds_respects_jitter_bounds() -> None:
    config = ScheduleConfig(interval_minutes=10, jitter_percent=20)

    values = [next_sleep_seconds(config) for _ in range(50)]

    assert all(480 <= value <= 720 for value in values)
