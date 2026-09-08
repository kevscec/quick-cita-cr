from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import UTC, date, datetime
from pathlib import Path

from .models import AppointmentSlot, BranchSnapshot, EventType, WatchEvent

SCHEMA = """
CREATE TABLE IF NOT EXISTS slots (
  branch TEXT NOT NULL,
  slot_date TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  raw_text TEXT NOT NULL,
  PRIMARY KEY (branch, slot_date)
);
CREATE TABLE IF NOT EXISTS checks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  checked_at TEXT NOT NULL,
  branch TEXT NOT NULL,
  best_date TEXT,
  slot_count INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  event_type TEXT NOT NULL,
  branch TEXT NOT NULL,
  slot_date TEXT,
  message TEXT NOT NULL
);
"""


class Storage:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        return con

    def _init_schema(self) -> None:
        with self._connect() as con:
            con.executescript(SCHEMA)

    def get_known_dates(self, branch: str) -> set[date]:
        with self._connect() as con:
            rows = con.execute("SELECT slot_date FROM slots WHERE branch = ?", (branch,)).fetchall()
        return {date.fromisoformat(row["slot_date"]) for row in rows}

    def get_previous_best(self, branch: str) -> date | None:
        with self._connect() as con:
            row = con.execute("SELECT MIN(slot_date) AS best FROM slots WHERE branch = ?", (branch,)).fetchone()
        if row is None or row["best"] is None:
            return None
        return date.fromisoformat(row["best"])

    def has_any_history(self, branch: str) -> bool:
        with self._connect() as con:
            row = con.execute("SELECT 1 FROM checks WHERE branch = ? LIMIT 1", (branch,)).fetchone()
        return row is not None

    def record_snapshot(self, snapshot: BranchSnapshot) -> None:
        with self._connect() as con:
            con.execute(
                "INSERT INTO checks(checked_at, branch, best_date, slot_count) VALUES (?, ?, ?, ?)",
                (
                    snapshot.checked_at.isoformat(),
                    snapshot.branch,
                    snapshot.best_date.isoformat() if snapshot.best_date else None,
                    len(snapshot.slots),
                ),
            )
            for slot in snapshot.slots:
                con.execute(
                    """
                    INSERT INTO slots(branch, slot_date, first_seen_at, last_seen_at, raw_text)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(branch, slot_date) DO UPDATE SET
                      last_seen_at = excluded.last_seen_at,
                      raw_text = excluded.raw_text
                    """,
                    (
                        slot.branch,
                        slot.date.isoformat(),
                        snapshot.checked_at.isoformat(),
                        snapshot.checked_at.isoformat(),
                        slot.raw_text,
                    ),
                )

    def record_events(self, events: Iterable[WatchEvent]) -> None:
        now = datetime.now(UTC).isoformat()
        with self._connect() as con:
            con.executemany(
                "INSERT INTO events(created_at, event_type, branch, slot_date, message) VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        now,
                        event.event_type.value,
                        event.branch,
                        event.slot_date.isoformat() if event.slot_date else None,
                        event.message,
                    )
                    for event in events
                ],
            )

    def recent_events(self, limit: int = 20) -> list[WatchEvent]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT event_type, branch, slot_date, message FROM events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            WatchEvent(
                event_type=EventType(row["event_type"]),
                branch=row["branch"],
                slot_date=date.fromisoformat(row["slot_date"]) if row["slot_date"] else None,
                message=row["message"],
            )
            for row in rows
        ]
