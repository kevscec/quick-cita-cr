# quick-cita-cr

Polite local monitor for fast Costa Rica Educación Vial appointment openings.

`quick-cita-cr` signs in with your own Educación Vial credentials, checks the branches you choose, compares the visible appointment dates with previous runs, and sends a notification when a better or newly-fast appointment appears.

It is designed for personal use, public-source maintainability, and future deployment on a Linux VM such as Oracle Cloud.

## What it does

- Checks selected Educación Vial / COSEVI appointment branches on a schedule.
- Sends a first-run summary of the current appointment landscape.
- Detects fast openings relative to each branch, not only globally.
- Notifies when a date is new, earlier than the previous best for that branch, or inside your configured fast-window.
- Stores local state in SQLite so it only alerts on meaningful changes.
- Supports Gmail SMTP notifications out of the box.
- Uses Playwright with a persistent local browser profile for a maintainable browser automation flow.
- Includes systemd user timer templates for Oracle Cloud / Linux VM deployment.

## What it does not do

- It does not bypass CAPTCHA, access controls, rate limits, blocks, or anti-bot systems.
- It does not use proxies or fingerprint spoofing.
- It does not reserve appointments automatically in v0.1.
- It does not store your credentials in the repository.

If the portal asks for human verification or blocks access, the tool stops and tells you to intervene manually.

## Responsible-use model

This project uses “polite automation”: low-frequency checks, jitter, backoff after failures, one browser session, and no evasion. The goal is to notify you quickly when a legitimate appointment opening appears, not to overwhelm the public service or bypass its protections.

## Quick start

```bash
git clone https://github.com/kevscec/quick-cita-cr.git
cd quick-cita-cr
uv sync
uv run playwright install chromium
uv run quick-cita init
```

Edit the generated config:

```bash
nano ~/.config/quick-cita-cr/config.yaml
```

Create a local `.env` file or export the secrets in your shell:

```bash
cp .env.example .env
nano .env
```

Run diagnostics:

```bash
uv run quick-cita doctor
```

Send a test email:

```bash
uv run quick-cita notify-test
```

Run one check:

```bash
uv run quick-cita check --once --headed
```

Run continuously:

```bash
uv run quick-cita watch
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
    - HEREDIA
    - PASO ANCHO (EDUCACION VIAL)
  quick_window_days: 21
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
  headless: true
  # Prefer a real installed browser for production.
  # Use either channel or executable_path, not both.
  channel: chrome
  executable_path: null
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

Secrets are read from environment variables or `.env`:

```bash
QUICK_CITA_ID_TYPE=CI
QUICK_CITA_IDENTIFICATION=123456789
QUICK_CITA_PASSWORD='your-educacion-vial-password'
QUICK_CITA_RECEIPT_NUMBER=1234567890
QUICK_CITA_EMAIL_USERNAME=your.gmail@gmail.com
QUICK_CITA_EMAIL_PASSWORD='gmail-app-password'
```

Use a Gmail App Password, not your normal Gmail password.

## Oracle Cloud / Linux VM deployment

Install once on the VM:

```bash
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv git
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/kevscec/quick-cita-cr.git ~/quick-cita-cr
cd ~/quick-cita-cr
uv sync --frozen
uv run playwright install --with-deps chromium
uv run playwright install chrome
uv run quick-cita init
```

Configure secrets in `~/.config/quick-cita-cr/secrets.env` and config in `~/.config/quick-cita-cr/config.yaml`.

Install the user service/timer:

```bash
mkdir -p ~/.config/systemd/user
cp deploy/systemd/quick-cita-cr.service ~/.config/systemd/user/
cp deploy/systemd/quick-cita-cr.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now quick-cita-cr.timer
loginctl enable-linger "$USER"
```

Check status/logs:

```bash
systemctl --user list-timers quick-cita-cr.timer
journalctl --user -u quick-cita-cr.service -f
```

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy src/quick_cita_cr
```

## Security

See `docs/security.md`. Never commit `.env`, local SQLite databases, browser profiles, logs, screenshots, or authenticated HTML.
