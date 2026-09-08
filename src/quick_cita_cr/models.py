from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class EventType(StrEnum):
    FIRST_RUN_SUMMARY = "first_run_summary"
    NEW_DATE = "new_date"
    EARLIER_BEST = "earlier_best"
    WITHIN_WINDOW = "within_window"


@dataclass(frozen=True, slots=True)
class AppointmentSlot:
    branch: str
    date: date
    raw_text: str


@dataclass(frozen=True, slots=True)
class BranchSnapshot:
    branch: str
    checked_at: datetime
    slots: tuple[AppointmentSlot, ...]

    @property
    def best_date(self) -> date | None:
        if not self.slots:
            return None
        return min(slot.date for slot in self.slots)


@dataclass(frozen=True, slots=True)
class WatchEvent:
    event_type: EventType
    branch: str
    slot_date: date | None
    message: str


@dataclass(frozen=True, slots=True)
class WatchResult:
    checked_at: datetime
    snapshots: tuple[BranchSnapshot, ...]
    events: tuple[WatchEvent, ...]
