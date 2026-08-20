# Installation Guide

This guide installs Oráculo locally without Docker or a cloud database.

## Requirements

- Python 3.12 or newer, 64-bit;
- Node.js 20 or newer;
- Git;
- Windows 11, a current Linux distribution or macOS;
- approximately 2 GB free during installation.

AI analysis is optional. Local CRUD and deterministic scoring work without an API key.

## Clone

```bash
git clone https://github.com/LeoBarreto38/oraculo-decision-os.git
cd oraculo-decision-os
```

## Windows assisted installation

Run `install-oraculo.bat` from the repository root. It creates `backend/.venv`, installs backend/frontend dependencies, builds the frontend and initializes SQLite. Then run `start-oraculo.bat`.

Open <http://127.0.0.1:8000>. Keep the application terminal open. Press `Ctrl+C` there to stop it.

The installer is idempotent: rerunning it preserves an existing database. If it reports that the virtual environment uses an incompatible Python, rename `backend/.venv`, rerun the installer and remove the old environment only after validation.

## Manual installation on Windows

```powershell
Set-Location backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.cli init-db

Set-Location ..\frontend
corepack enable
pnpm install --frozen-lockfile
pnpm run build

Set-Location ..\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Linux and macOS

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m app.cli init-db

cd ../frontend
corepack enable
pnpm install --frozen-lockfile
pnpm run build

cd ../backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Configuration

Copy `.env.example` to `.env.local` in the project root. Useful variables:

```dotenv
OPENAI_API_KEY=
ORACULO_DATA_DIR=./data
ORACULO_TIMEZONE=UTC
ORACULO_SCHEDULER_ENABLED=true
```

`ORACULO_ENV_FILE` can select a different env file. `ORACULO_DATABASE_URL` can replace the SQLite URL derived from `ORACULO_DATA_DIR`. Relative data paths resolve from the project root.

Never commit `.env.local`. Do not expose the server on `0.0.0.0` without authentication, TLS and a threat review.

## Verify

```bash
curl http://127.0.0.1:8000/api/health
```

The response should report `ok`. A new empty database receives clearly labelled DEMO records. An existing non-empty database is never reseeded.

Continue with the [user guide](USER-GUIDE.md). For failures, see [troubleshooting](TROUBLESHOOTING.md).
