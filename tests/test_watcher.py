from datetime import UTC, date, datetime

from quick_cita_cr.config import AppointmentConfig
from quick_cita_cr.models import AppointmentSlot, BranchSnapshot, EventType
from quick_cita_cr.storage import Storage
from quick_cita_cr.watcher import detect_events


def snapshot(branch: str, *dates: date) -> BranchSnapshot:
    return BranchSnapshot(
        branch=branch,
        checked_at=datetime(2026, 9, 8, tzinfo=UTC),
        slots=tuple(AppointmentSlot(branch, d, d.isoformat()) for d in dates),
    )


def test_first_run_emits_summary(tmp_path) -> None:
    storage = Storage(tmp_path / "state.sqlite3")
    events = detect_events(
        snapshot("ALAJUELA", date(2026, 9, 20)),
        storage,
        AppointmentConfig(branches=["ALAJUELA"], quick_window_days=21),
        today=date(2026, 9, 8),
    )

    assert any(event.event_type == EventType.FIRST_RUN_SUMMARY for event in events)


def test_new_fast_branch_date_emits_within_window(tmp_path) -> None:
    storage = Storage(tmp_path / "state.sqlite3")
    old = snapshot("ALAJUELA", date(2026, 9, 29))
    storage.record_snapshot(old)

    events = detect_events(
        snapshot("ALAJUELA", date(2026, 9, 9), date(2026, 9, 29)),
        storage,
        AppointmentConfig(branches=["ALAJUELA"], quick_window_days=3),
        today=date(2026, 9, 8),
    )

    assert {event.event_type for event in events} >= {
        EventType.NEW_DATE,
        EventType.WITHIN_WINDOW,
        EventType.EARLIER_BEST,
    }


def test_existing_far_dates_do_not_alert_after_first_run(tmp_path) -> None:
    storage = Storage(tmp_path / "state.sqlite3")
    old = snapshot("HEREDIA", date(2026, 10, 15))
    storage.record_snapshot(old)

    events = detect_events(
        snapshot("HEREDIA", date(2026, 10, 15)),
        storage,
        AppointmentConfig(branches=["HEREDIA"], quick_window_days=21),
        today=date(2026, 9, 8),
    )

    assert events == ()
