# Linux / Oracle Cloud deployment

This project is designed to run either as a long-running CLI process or as a scheduled systemd user timer.

Recommended production mode is the timer because every run is short-lived and state is persisted in SQLite.

## Install

```bash
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv git
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/kevscec/quick-cita-cr.git ~/quick-cita-cr
cd ~/quick-cita-cr
uv sync --frozen
uv run playwright install --with-deps chromium
uv run quick-cita init
```

## Configure

Edit:

```text
~/.config/quick-cita-cr/config.yaml
~/.config/quick-cita-cr/secrets.env
```

Protect secrets:

```bash
chmod 600 ~/.config/quick-cita-cr/secrets.env
```

## systemd user timer

```bash
mkdir -p ~/.config/systemd/user
cp deploy/systemd/quick-cita-cr.service ~/.config/systemd/user/
cp deploy/systemd/quick-cita-cr.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now quick-cita-cr.timer
loginctl enable-linger "$USER"
```

## Logs

```bash
journalctl --user -u quick-cita-cr.service -f
```
