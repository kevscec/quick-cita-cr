from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Protocol

from .config import AppointmentConfig
from .models import BranchSnapshot, EventType, WatchEvent, WatchResult
from .storage import Storage


class CoseviClient(Protocol):
    def check_branch(self, branch: str) -> BranchSnapshot: ...


def detect_events(
    snapshot: BranchSnapshot,
    storage: Storage,
    appointment_config: AppointmentConfig,
    today: date | None = None,
) -> tuple[WatchEvent, ...]:
    today = today or datetime.now(UTC).date()
    quick_cutoff = today + timedelta(days=appointment_config.quick_window_days)
    known_dates = storage.get_known_dates(snapshot.branch)
    previous_best = storage.get_previous_best(snapshot.branch)
    has_history = storage.has_any_history(snapshot.branch)
    events: list[WatchEvent] = []

    if not has_history and appointment_config.notify_on_first_run:
        if snapshot.best_date:
            message = (
                f"Resumen inicial {snapshot.branch}: {len(snapshot.slots)} citas visibles; "
                f"mejor fecha {snapshot.best_date.isoformat()}."
            )
        else:
            message = f"Resumen inicial {snapshot.branch}: no se detectaron citas visibles."
        events.append(
            WatchEvent(EventType.FIRST_RUN_SUMMARY, snapshot.branch, snapshot.best_date, message)
        )

    new_slots = [slot for slot in snapshot.slots if slot.date not in known_dates]
    for slot in new_slots:
        if appointment_config.notify_on_new_dates:
            events.append(
                WatchEvent(
                    EventType.NEW_DATE,
                    snapshot.branch,
                    slot.date,
                    f"Nueva fecha visible en {snapshot.branch}: {slot.date.isoformat()}.",
                )
            )
        if appointment_config.notify_on_within_window and slot.date <= quick_cutoff:
            events.append(
                WatchEvent(
                    EventType.WITHIN_WINDOW,
                    snapshot.branch,
                    slot.date,
                    f"Cita rápida en {snapshot.branch}: {slot.date.isoformat()} "
                    f"(dentro de {appointment_config.quick_window_days} días).",
                )
            )

    if (
        appointment_config.notify_on_earlier_best
        and previous_best is not None
        and snapshot.best_date is not None
        and snapshot.best_date < previous_best
    ):
        events.append(
            WatchEvent(
                EventType.EARLIER_BEST,
                snapshot.branch,
                snapshot.best_date,
                f"Mejoró {snapshot.branch}: ahora {snapshot.best_date.isoformat()}, antes {previous_best.isoformat()}.",
            )
        )

    return tuple(events)


class Watcher:
    def __init__(
        self, client: CoseviClient, storage: Storage, appointment_config: AppointmentConfig
    ):
        self.client = client
        self.storage = storage
        self.appointment_config = appointment_config

    def check_once(self) -> WatchResult:
        snapshots: list[BranchSnapshot] = []
        events: list[WatchEvent] = []
        checked_at = datetime.now(UTC)
        for branch in self.appointment_config.branches:
            snapshot = self.client.check_branch(branch)
            branch_events = detect_events(snapshot, self.storage, self.appointment_config)
            self.storage.record_snapshot(snapshot)
            snapshots.append(snapshot)
            events.extend(branch_events)
        self.storage.record_events(events)
        return WatchResult(checked_at=checked_at, snapshots=tuple(snapshots), events=tuple(events))
