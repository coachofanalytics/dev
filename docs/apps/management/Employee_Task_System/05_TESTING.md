# Employee Activity System (Management) – 05_TESTING.md

## Test Strategy (How to verify)
Follow CODA Testing Strategy: unit, integration, and regression tests with real data (cloned DB where applicable).

## Environments
- Local: `python manage.py runserver`
- UAT: https://codamakutano.herokuapp.com

## Smoke Tests (Phase‑0 – DRY)
1. Utilities service imports and functions return expected values.
2. Base views enforce auth and department scoping.
3. Templates render without N+1 DB queries.

## Phase‑1 Tests – Data & Automation
- Ingestion
  - Import TaskHistory and meeting metadata successfully.
  - Validate normalization (Dept→Category→Task exists).
- Auto‑linking
  - ≥80% of meetings auto‑linked (target) in sampled week.
  - Manual override UI updates links; audit log written.
- Analytics
  - Category totals by month return within expected ranges.

## API Contract Tests (for Finance)
- GET /management/api/activity/summary?window=month
  - 200 OK, JSON `{ data: {...}, meta: {...} }`.
  - Includes `department_id`, `category_id`, `total_minutes`, `evidence_count`.

## Performance
- Dashboard loads < 2s for 10k TaskHistory rows (with indexes).

## Run Tests
```bash
pytest -q
python manage.py test management
```

## Regression Checklist
- No new duplicated modules.
- Legacy code remains isolated under `deprecated/`.
