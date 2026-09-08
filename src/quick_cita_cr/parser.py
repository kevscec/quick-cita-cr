from __future__ import annotations

import re
from datetime import date
from html import unescape

from .models import AppointmentSlot

SPANISH_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

DATE_NUMERIC_RE = re.compile(
    r"(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)?\s*"
    r"(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4})",
    re.IGNORECASE,
)
DATE_TEXT_RE = re.compile(
    r"(?P<day>\d{1,2})\s+de\s+(?P<month>[a-záéíóúñ]+)\s+de\s+(?P<year>\d{4})",
    re.IGNORECASE,
)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    text = TAG_RE.sub(" ", unescape(value))
    return SPACE_RE.sub(" ", text).strip()


def parse_appointment_dates(text: str, branch: str) -> tuple[AppointmentSlot, ...]:
    clean = normalize_text(text)
    slots: list[AppointmentSlot] = []
    seen: set[date] = set()

    for match in DATE_NUMERIC_RE.finditer(clean):
        slot_date = date(
            int(match.group("year")), int(match.group("month")), int(match.group("day"))
        )
        if slot_date not in seen:
            slots.append(AppointmentSlot(branch=branch, date=slot_date, raw_text=match.group(0).strip()))
            seen.add(slot_date)

    for match in DATE_TEXT_RE.finditer(clean):
        month_name = match.group("month").lower()
        month = SPANISH_MONTHS.get(month_name)
        if month is None:
            continue
        slot_date = date(int(match.group("year")), month, int(match.group("day")))
        if slot_date not in seen:
            slots.append(AppointmentSlot(branch=branch, date=slot_date, raw_text=match.group(0).strip()))
            seen.add(slot_date)

    return tuple(sorted(slots, key=lambda slot: slot.date))
