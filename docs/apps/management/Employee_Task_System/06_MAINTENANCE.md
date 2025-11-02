# Employee Activity System (Management) – 06_MAINTENANCE.md

## Operations (How to maintain)
- Monitor background jobs and AI health via `AIHealthChecker` logs.
- Review activity linking accuracy weekly; tune heuristics/keywords.
- Keep `deprecated/` clean; remove once safely unused.

## Runbooks
### Re‑index TaskHistory
```bash
python manage.py shell -c "from management.services import maintenance; maintenance.rebuild_indexes()"
```

### Reprocess Links for a Date Range
```bash
python manage.py reprocess_links --from 2025-10-01 --to 2025-10-31
```

## Known Issues
- Meeting vendor rate limits can delay evidence ingestion → batch + backoff.
- Historical gaps from manual entries → run backfill job before analytics.

## Backups & Data Safety
- Never run experiments on production DB. Use cloned DB per CURSOR_AI_GUIDE.
- Ensure env vars for vendor APIs are present in UAT/Prod before enabling jobs.

## Upgrade Notes
- When updating AI providers, validate through `AIConfigurationService` staging keys first.
