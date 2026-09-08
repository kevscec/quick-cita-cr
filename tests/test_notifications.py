from datetime import UTC, date, datetime

from quick_cita_cr.models import AppointmentSlot, BranchSnapshot, EventType, WatchEvent, WatchResult
from quick_cita_cr.notifications import format_events


def test_format_events_includes_branch_summary_and_portal() -> None:
    result = WatchResult(
        checked_at=datetime(2026, 9, 8, tzinfo=UTC),
        snapshots=(
            BranchSnapshot(
                branch="ALAJUELA",
                checked_at=datetime(2026, 9, 8, tzinfo=UTC),
                slots=(AppointmentSlot("ALAJUELA", date(2026, 9, 9), "09/09/2026"),),
            ),
        ),
        events=(WatchEvent(EventType.WITHIN_WINDOW, "ALAJUELA", date(2026, 9, 9), "Cita rápida"),),
    )

    subject, body = format_events(result)

    assert "1 alerta" in subject
    assert "ALAJUELA" in body
    assert "https://servicios.educacionvial.go.cr/Formularios/IngresarCuenta" in body
