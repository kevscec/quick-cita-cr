# Security model

`quick-cita-cr` is personal automation that uses your own Educación Vial and email credentials. Treat the local machine and browser profile as sensitive.

## Never commit

- `.env` or `.env.*` files, except `.env.example`
- `~/.config/quick-cita-cr/secrets.env`
- SQLite state databases
- browser profiles, cookies, local storage, or Chrome user data
- screenshots/logs from authenticated sessions
- raw authenticated HTML
- receipt numbers, IDs, passwords, Gmail app passwords, or tokens

## Secrets

Secrets are loaded from environment variables or `~/.config/quick-cita-cr/secrets.env`.

Use:

```bash
chmod 600 ~/.config/quick-cita-cr/secrets.env
```

Use a Gmail App Password for SMTP. Do not use your normal Google password.

## Browser profile

The browser profile may contain authenticated cookies and Cloudflare/session state. Keep it local and excluded from git:

```text
~/.local/share/quick-cita-cr/browser-profile
```

## Logging

Logs should include only branch names, dates, event types, and high-level tool state. Do not log form inputs, cookies, full page HTML, screenshots, or secret values.

## Public repository posture

This repository should contain reusable code, docs, tests, service templates, and examples only. Operational state belongs on the host machine, not in git.
