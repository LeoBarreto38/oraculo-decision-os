# Troubleshooting

## API does not start

Confirm the complete terminal error, the virtual environment, write access to the configured data directory and whether port 8000 is occupied.

```bash
cd backend
python -m app.cli init-db
python -m pytest -q
```

On Windows, a venv may become incompatible after changing Python versions. Check `backend/.venv/pyvenv.cfg`. If its interpreter version does not match installed binary extensions, rename `.venv`, create a new one and reinstall `requirements.txt`.

## Frontend does not build

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm run typecheck
pnpm run build
```

If Vite reports a locked temporary file, close stale Node processes belonging to this project and retry. Do not terminate unrelated system processes.

## UI opens without API data

Check <http://127.0.0.1:8000/api/health>. Rebuild after source changes. Use the compiled app on port 8000 or the Vite development server on port 5173; do not open `index.html` directly.

## AI analysis is unavailable

Verify only that `OPENAI_API_KEY` is present in the selected local env file. Do not print it. Check provider access, quota, model configuration, network connectivity and the application's hard cost limit.

Local features should continue operating without AI.

## Database is locked

Stop duplicate backend instances and close SQLite tools that retain a write lock. Do not place the active database in a synchronized folder. Never restore over an open database.

## Notifications do not appear

Browser notifications require permission, an open application and a running scheduler. The internal alert list remains the source of record.

## Before opening an Issue

Collect operating system, Python/Node versions, exact reproduction steps and sanitized logs. Remove keys, personal paths, databases, decisions and private evidence. Then use the repository's structured Bug Report form.
