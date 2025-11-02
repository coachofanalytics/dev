# Scripts Index

This folder contains development, deployment, database, and maintenance helpers. Safe‑by‑default, non‑interactive.

## Quick Start
- Start dev server (clone DB settings):
  - `scripts/dev/dev_server.sh --port 8000`
  - HTTPS (requires django-extensions): `scripts/dev/dev_server.sh --https`
- Deploy to UAT: `make deploy-uat`
- Clone production DB (see dedicated script under database/)

## Structure (target)
- `dev/` – local development helpers
- `deploy/` – CI/CD scripts (Heroku)
- `management/db/` – database scripts
- `maintenance/` – one-off validation/backfill
- `tests/` – scripted test runners
- `windows/` – PowerShell wrappers

## Conventions
- Bash scripts are idempotent; use `set -euo pipefail`.
- All scripts accept `--help` and print usage.
- Never operate on production unless `ENVIRONMENT=production` is explicitly set (guardrails recommended).

## Deprecations (removed)
The following duplicates were removed and replaced by `dev/dev_server.sh`:
- `scripts/run_local.sh`
- `scripts/run_https_local.sh`
- `scripts/runserver_local.sh`
- `scripts/runserver_local_https.sh`
- `scripts/runserver_port8080.sh`
- `scripts/START_HTTPS.sh`

Use `scripts/dev/dev_server.sh` instead.
