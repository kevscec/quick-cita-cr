from __future__ import annotations

from typing import Protocol

from quick_cita_cr.models import WatchResult


class Notifier(Protocol):
    def send(self, subject: str, body: str) -> None: ...


def format_events(result: WatchResult) -> tuple[str, str]:
    if result.events:
        subject = f"quick-cita-cr: {len(result.events)} alerta(s) de cita"
        lines = ["Se detectaron cambios relevantes:", ""]
        for event in result.events:
            date_text = f" — {event.slot_date.isoformat()}" if event.slot_date else ""
            lines.append(f"- {event.branch}{date_text}: {event.message}")
    else:
        subject = "quick-cita-cr: revisión sin alertas"
        lines = ["Revisión completada sin citas rápidas nuevas.", ""]
    lines.extend(["", "Resumen visible por sede:"])
    for snapshot in result.snapshots:
        best = snapshot.best_date.isoformat() if snapshot.best_date else "sin citas visibles"
        lines.append(f"- {snapshot.branch}: {len(snapshot.slots)} citas; mejor fecha: {best}")
    lines.extend(["", "Portal: https://servicios.educacionvial.go.cr/Formularios/IngresarCuenta"])
    return subject, "\n".join(lines)
