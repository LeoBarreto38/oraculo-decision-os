# Contributing to Oráculo

Thank you for helping improve Oráculo. Contributions may include bug fixes, documentation, accessibility, tests, provider integrations, evidence provenance, calibration, performance and cross-platform support.

## Principles

Contributions should preserve these properties:

1. Evidence and uncertainty remain explicit.
2. Heuristic scores are not presented as calibrated probabilities.
3. AI recommendations remain auditable and human authority is final.
4. Consequential external actions require explicit human confirmation.
5. Local-first, privacy-preserving defaults are preferred.
6. Predictions should be compared with observed outcomes.

Open an Issue or Discussion before major changes to persistence, ontology, scoring, authentication, cloud infrastructure or autonomous actions. Small fixes do not require prior discussion.

## Development setup

Requirements: Python 3.12+, Node.js 20+ and Git.

```bash
git clone https://github.com/LeoBarreto38/oraculo-decision-os.git
cd oraculo-decision-os/backend
python -m venv .venv
```

Activate the virtual environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Or on Linux/macOS:

```bash
source .venv/bin/activate
```

Then install and initialize:

```bash
python -m pip install -r requirements.txt
python -m app.cli init-db
```

For the frontend:

```bash
cd ../frontend
corepack enable
pnpm install --frozen-lockfile
pnpm run dev
```

Copy `.env.example` to `.env.local` when local configuration is needed. Never commit API keys, personal databases, exports or backups.

## Tests

```bash
cd backend
python -m pytest -q

cd ../frontend
pnpm run typecheck
pnpm run build
```

New behavior should include tests whenever practical. Decision-engine changes should document assumptions, mathematical rationale, failure modes and how the result can be validated.

## Pull requests

Keep pull requests focused and explain:

- the problem and why the change is needed;
- the implementation and important trade-offs;
- security or privacy implications;
- how the change was tested.

AI-assisted code is welcome, but contributors remain responsible for understanding, testing and licensing their submission. By contributing, you agree that your contribution will be distributed under AGPL-3.0.

Never place real personal data in fixtures, screenshots, logs, Issues or pull requests. Report vulnerabilities according to [SECURITY.md](SECURITY.md).
