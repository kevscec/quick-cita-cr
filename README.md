# quick-cita-cr

Personal monitor for Costa Rica Educación Vial appointment openings.

`quick-cita-cr` logs in with your own Educación Vial credentials, checks the configured practical-test branches, stores previous results locally, and notifies you when new or earlier dates appear.

The current implementation uses Selenium with `undetected_chromedriver`, a persistent Chrome profile, human-like interactions, and Cloudflare challenge handling for the portal flow.

## Status

Validated locally against the live portal:

- Cloudflare challenge resolved in headed mode.
- Login works with a persistent profile.
- Practical-test flow reaches branch availability.
- Appointment dates are extracted and compared with SQLite state.
- Email notification formatting works.

Known limitation: Cloudflare did not resolve reliably in pure headless mode during validation. Use headed mode, a virtual display, or a warmed persistent profile for unattended deployments.

## Features

- Branch-by-branch appointment monitoring.
- New-date, earlier-best, and configurable quick-window alerts.
- SQLite state so repeated runs only alert on meaningful changes.
- Gmail SMTP notifications using app passwords.
- Persistent browser profile for cookies/session state.
- Human-like typing, clicks, delays, and scroll behavior.
- Chrome anti-detection flags through `undetected_chromedriver`.
- `uv` based Python project with tests, linting, and type checks.
- systemd user timer templates for Linux / Oracle Cloud.

## Requirements

- Python 3.12 or 3.13.
- `uv`.
- Chrome or Chrome for Testing.
- Educación Vial account credentials.
- Receipt number for the practical-test flow.
- Optional Gmail app password for email notifications.

## Quick start

```bash
git clone https://github.com/kevscec/quick-cita-cr.git
cd quick-cita-cr
uv sync
uv run quick-cita init
```

Configure secrets:

```bash
nano ~/.config/quick-cita-cr/secrets.env
chmod 600 ~/.config/quick-cita-cr/secrets.env
```

Configure branches/browser:

```bash
nano ~/.config/quick-cita-cr/config.yaml
```

Run diagnostics:

```bash
uv run quick-cita doctor
```

Run one visible check:

```bash
uv run quick-cita check --headed
```

Run a visual demo for screen recording:

```bash
uv run quick-cita-cr demo
```

The demo command opens the browser visibly, uses the persistent profile, checks the configured branches, and prints the appointment summary even when there are no new alert events.

Run continuously:

```bash
uv run quick-cita watch --headed
```

## Configuration

Default config path:

```text
~/.config/quick-cita-cr/config.yaml
```

Example:

```yaml
appointment:
  license_class: B1
  branches:
    - ALAJUELA
    - SAN RAMON
  quick_window_days: 14
  notify_on_first_run: true
  notify_on_new_dates: true
  notify_on_earlier_best: true
  notify_on_within_window: true

schedule:
  interval_minutes: 12
  jitter_percent: 20
  max_failures_before_pause: 3
  pause_minutes_after_failures: 60

browser:
  headless: false
  executable_path: /home/kev/.local/share/quick-cita-cr/chrome-for-testing/chrome-linux64/chrome
  profile_dir: ~/.local/share/quick-cita-cr/browser-profile
  timeout_seconds: 45

notifications:
  email:
    enabled: true
    smtp_host: smtp.gmail.com
    smtp_port: 587
    from_address: your.gmail@gmail.com
    to_addresses:
      - your.gmail@gmail.com
```

Secrets are read from environment variables or `~/.config/quick-cita-cr/secrets.env`:

```dotenv
QUICK_CITA_ID_TYPE=CI
QUICK_CITA_IDENTIFICATION=123456789
QUICK_CITA_PASSWORD=your-educacion-vial-password
QUICK_CITA_RECEIPT_NUMBER=1234567890
QUICK_CITA_EMAIL_USERNAME=your.gmail@gmail.com
QUICK_CITA_EMAIL_PASSWORD=gmail-app-password
```

Use a Gmail App Password, not your normal Gmail password.

## Chrome for Testing without sudo

If the machine does not have Linux Chrome installed and `sudo` is unavailable:

```bash
mkdir -p ~/.local/share/quick-cita-cr/chrome-for-testing
cd ~/.local/share/quick-cita-cr/chrome-for-testing
curl -fsSL -o chrome-linux64.zip \
  https://storage.googleapis.com/chrome-for-testing-public/153.0.8010.36/linux64/chrome-linux64.zip
python3 - <<'PY'
from zipfile import ZipFile
from pathlib import Path
base = Path.home() / '.local/share/quick-cita-cr/chrome-for-testing'
with ZipFile(base / 'chrome-linux64.zip') as archive:
    archive.extractall(base)
for path in [base / 'chrome-linux64/chrome', base / 'chrome-linux64/chrome_crashpad_handler']:
    path.chmod(0o755)
PY
```

Then set:

```yaml
browser:
  executable_path: ~/.local/share/quick-cita-cr/chrome-for-testing/chrome-linux64/chrome
  headless: false
```

## Development

```bash
uv sync --all-groups
uv run ruff format .
uv run ruff check .
uv run mypy src/quick_cita_cr
uv run pytest
```

## Repository layout

```text
src/quick_cita_cr/
  browser/              # Chrome driver, Cloudflare solver, human behavior helpers
  notifications/        # Notification backends
  cli.py                # Typer CLI
  config.py             # Config/secrets models
  cosevi_client.py      # Portal automation client
  parser.py             # Appointment-date parsing
  storage.py            # SQLite persistence
  watcher.py            # Snapshot comparison and event detection

tests/                  # Unit tests
.github/workflows/      # CI
deploy/systemd/         # Linux user service/timer templates
docs/                   # Deployment and security docs
```

## Security

Never commit credentials, `.env`, SQLite state, browser profiles, cookies, screenshots, logs, or authenticated HTML. See `docs/security.md`.

## License

MIT. See `LICENSE`.
