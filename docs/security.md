# Security model

`quick-cita-cr` is public-source software for personal monitoring with your own credentials.

## Secrets

Never commit:

- `.env`
- `~/.config/quick-cita-cr/secrets.env`
- SQLite state databases
- browser profiles
- cookies or Playwright storage state
- screenshots/logs from authenticated sessions
- receipt numbers, IDs, passwords, or email app passwords

Use Gmail App Passwords for SMTP. Do not use your normal Google password.

## Browser automation boundaries

This project intentionally does not implement CAPTCHA bypass, proxy rotation, fingerprint spoofing, or access-control evasion. If the portal asks for verification or denies access, the run fails closed and asks for human intervention.

## Logging

Logs should describe branches, dates, and tool state only. Do not log form inputs, cookies, local storage, full authenticated HTML, or screenshots by default.
