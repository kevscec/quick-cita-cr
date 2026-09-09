# Contributing

This is a personal automation project, but changes should still be easy to review and safe to run.

## Development setup

```bash
uv sync --all-groups
uv run quick-cita doctor
```

## Quality checks

Run before committing:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy src/quick_cita_cr
uv run pytest
```

## Safety rules

- Do not commit secrets, cookies, browser profiles, screenshots, logs, SQLite databases, or authenticated HTML.
- Keep operational data under `~/.config/quick-cita-cr` or `~/.local/share/quick-cita-cr`.
- Prefer tests around parser, watcher, storage, and browser helper seams.
- Validate portal-facing changes locally before relying on unattended runs.
