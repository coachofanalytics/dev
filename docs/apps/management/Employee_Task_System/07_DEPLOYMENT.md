# Employee Activity System (Management) – 07_DEPLOYMENT.md

## How to Deploy

### Pre‑Deployment Checklist
- [ ] All tests pass (`pytest` / `python manage.py test management`)
- [ ] UAT validation complete; dashboards render; no N+1
- [ ] .env configured for AI and meeting providers
- [ ] .slugignore excludes docs/tests/scripts

### Deploy to UAT
```bash
git push heroku 25.10_CODA_UAT_CM:main --force
heroku logs --tail --app codamakutano --num 100
```

### Smoke Verification (UAT)
- Open Management dashboard pages; confirm page load < 2s.
- Verify activity summary API returns 200 with non‑zero data.

### Deploy to Production (with approval)
```bash
git push production 25.10_CODA_PROD_v2_CM:main --force
heroku logs --tail --app codatrainingapp --num 100
```

### Rollback
```bash
heroku releases --app codatrainingapp
heroku rollback v<PREVIOUS> --app codatrainingapp
```

### Post‑Deployment
- Monitor logs for ingestion/linking jobs.
- Review weekly accuracy metrics and adjust heuristics.
