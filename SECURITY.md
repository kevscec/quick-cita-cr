# Security Policy

## Supported versions

Only the `main` branch is maintained.

## Reporting sensitive issues

Do not open public issues containing credentials, screenshots from authenticated sessions, browser profile contents, or receipt/identity numbers.

For private operational issues, rotate any exposed credential immediately and remove the secret from the affected machine/history.

## Secret handling

This project expects secrets in local environment variables or `~/.config/quick-cita-cr/secrets.env`. Never store real values in repository files.
