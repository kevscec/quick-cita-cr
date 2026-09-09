# Deployment

`quick-cita-cr` can run locally, on WSL, or on a Linux VM. The safest production pattern is a short-lived scheduled run using a persistent browser profile and SQLite state.

## Runtime requirements

- Python 3.12 or 3.13
- `uv`
- Chrome or Chrome for Testing
- A persistent profile directory
- Educación Vial credentials in `~/.config/quick-cita-cr/secrets.env`

## Install

```bash
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv git curl
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/kevscec/quick-cita-cr.git ~/quick-cita-cr
cd ~/quick-cita-cr
uv sync --frozen
uv run quick-cita init
```

If `sudo` is unavailable or you do not want to install system Chrome, use Chrome for Testing under your home directory. See the README for the no-sudo install command.

## Configure

Edit:

```text
~/.config/quick-cita-cr/config.yaml
~/.config/quick-cita-cr/secrets.env
```

Recommended browser settings after live validation:

```yaml
browser:
  headless: false
  executable_path: /home/USER/.local/share/quick-cita-cr/chrome-for-testing/chrome-linux64/chrome
  profile_dir: ~/.local/share/quick-cita-cr/browser-profile
  timeout_seconds: 45
```

Protect secrets:

```bash
chmod 600 ~/.config/quick-cita-cr/secrets.env
```

## First run

Run visibly once so Cloudflare can validate the browser/profile:

```bash
cd ~/quick-cita-cr
uv run quick-cita check --headed
```

If the portal asks for manual verification, complete it in the visible browser. The persistent profile should retain cookies/state for later runs.

## systemd user timer

Copy templates:

```bash
mkdir -p ~/.config/systemd/user
cp deploy/systemd/quick-cita-cr.service ~/.config/systemd/user/
cp deploy/systemd/quick-cita-cr.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now quick-cita-cr.timer
loginctl enable-linger "$USER"
```

Check status:

```bash
systemctl --user list-timers quick-cita-cr.timer
systemctl --user status quick-cita-cr.service
journalctl --user -u quick-cita-cr.service -f
```

## Notes for Oracle Cloud

Headed browser automation on a headless VM may require a virtual display such as Xvfb or a desktop session. Do not assume pure Chrome headless will pass Cloudflare; validate with the real VM before relying on unattended monitoring.
