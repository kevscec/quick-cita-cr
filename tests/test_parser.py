from datetime import date

from quick_cita_cr.parser import parse_appointment_dates


def test_parse_numeric_spanish_weekday_dates() -> None:
    slots = parse_appointment_dates("Lunes 12/02/2026 Martes 03/03/2026", "ALAJUELA")

    assert [slot.date for slot in slots] == [date(2026, 2, 12), date(2026, 3, 3)]
    assert all(slot.branch == "ALAJUELA" for slot in slots)


def test_parse_textual_spanish_dates_and_deduplicates() -> None:
    slots = parse_appointment_dates("12 de marzo de 2026 otra vez 12/03/2026", "HEREDIA")

    assert [slot.date for slot in slots] == [date(2026, 3, 12)]
