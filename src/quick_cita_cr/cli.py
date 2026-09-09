from __future__ import annotations

import time
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .config import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_SECRETS_PATH,
    load_config,
    load_secrets,
    write_default_config,
)
from .cosevi_client import CoseviBrowserClient, HumanInterventionRequired
from .models import WatchResult
from .notifications import EmailNotifier, Notifier, format_events
from .safety import next_sleep_seconds
from .storage import Storage
from .watcher import Watcher

app = typer.Typer(help="Monitor fast Costa Rica Educación Vial appointment openings.")
console = Console()


def _build_notifiers(config_path: Path) -> tuple[Notifier, ...]:
    config = load_config(config_path)
    secrets = load_secrets()
    notifiers: list[Notifier] = []
    email = config.notifications.email
    if email.enabled:
        if not secrets.email_username or secrets.email_password is None:
            raise typer.BadParameter(
                "Email is enabled but QUICK_CITA_EMAIL_USERNAME/PASSWORD are missing."
            )
        notifiers.append(EmailNotifier(email, secrets.email_username, secrets.email_password))
    return tuple(notifiers)


def _send_notifications(result: WatchResult, config_path: Path, force: bool = False) -> None:
    if not result.events and not force:
        return
    subject, body = format_events(result)
    for notifier in _build_notifiers(config_path):
        notifier.send(subject, body)
    console.print(body)


@app.command()
def init(config_path: Path = typer.Option(DEFAULT_CONFIG_PATH, help="Config file path.")) -> None:
    path = write_default_config(config_path)
    DEFAULT_SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DEFAULT_SECRETS_PATH.exists():
        DEFAULT_SECRETS_PATH.write_text(
            "QUICK_CITA_ID_TYPE=CI\n"
            "QUICK_CITA_IDENTIFICATION=\n"
            "QUICK_CITA_PASSWORD=\n"
            "QUICK_CITA_RECEIPT_NUMBER=\n"
            "QUICK_CITA_EMAIL_USERNAME=\n"
            "QUICK_CITA_EMAIL_PASSWORD=\n",
            encoding="utf-8",
        )
        DEFAULT_SECRETS_PATH.chmod(0o600)
    console.print(f"Config: {path}")
    console.print(f"Secrets: {DEFAULT_SECRETS_PATH}")


@app.command()
def doctor(config_path: Path = typer.Option(DEFAULT_CONFIG_PATH, help="Config file path.")) -> None:
    config = load_config(config_path)
    table = Table("Check", "Status")
    table.add_row("config", f"ok: {config_path}")
    try:
        load_secrets()
        table.add_row("secrets", "ok")
    except Exception as exc:
        table.add_row("secrets", f"missing: {exc}")
    table.add_row("database", str(config.database_path.expanduser()))
    table.add_row("browser profile", str(config.browser.profile_dir.expanduser()))
    console.print(table)


@app.command("notify-test")
def notify_test(
    config_path: Path = typer.Option(DEFAULT_CONFIG_PATH, help="Config file path."),
) -> None:
    for notifier in _build_notifiers(config_path):
        notifier.send("quick-cita-cr: test", "This is a quick-cita-cr notification test.")
    console.print("Notification test sent.")


@app.command()
def check(
    config_path: Path = typer.Option(DEFAULT_CONFIG_PATH, help="Config file path."),
    once: bool = typer.Option(True, "--once", help="Run one check and exit."),
    headed: bool = typer.Option(False, "--headed", help="Show browser window."),
    notify_without_events: bool = typer.Option(
        False, help="Send summary even if there are no alerts."
    ),
) -> None:
    del once
    config = load_config(config_path)
    secrets = load_secrets()
    storage = Storage(config.database_path.expanduser())
    with CoseviBrowserClient(config, secrets, headed=headed) as client:
        watcher = Watcher(client, storage, config.appointment)
        result = watcher.check_once()
    _send_notifications(result, config_path, force=notify_without_events)
    if not result.events:
        console.print("No alert-worthy changes detected.")


@app.command()
def watch(
    config_path: Path = typer.Option(DEFAULT_CONFIG_PATH, help="Config file path."),
    headed: bool = typer.Option(False, "--headed", help="Show browser window."),
) -> None:
    config = load_config(config_path)
    failures = 0
    while True:
        try:
            check(config_path=config_path, headed=headed, notify_without_events=False)
            failures = 0
        except HumanInterventionRequired:
            raise
        except Exception as exc:
            failures += 1
            console.print(f"Check failed ({failures}): {exc}")
            if failures >= config.schedule.max_failures_before_pause:
                sleep_for = float(config.schedule.pause_minutes_after_failures * 60)
            else:
                sleep_for = next_sleep_seconds(config.schedule)
            time.sleep(sleep_for)
            continue
        time.sleep(next_sleep_seconds(config.schedule))


if __name__ == "__main__":
    app()
