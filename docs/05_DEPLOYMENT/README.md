# 05 - Deployment

**Purpose:** Deployment procedures, status, and known issues

---

## 📚 Documents in This Section

### ⭐ [READY_TO_DEPLOY.md](READY_TO_DEPLOY.md)
**Current deployment status and checklist**

### [KNOWN_ISSUES.md](KNOWN_ISSUES.md)
**Current known issues and workarounds** - READ BEFORE DEPLOYING

### [PRODUCTION_DEPLOYMENT_STRATEGY.md](PRODUCTION_DEPLOYMENT_STRATEGY.md)
**Production deployment strategy and guidelines**

### Session Summaries:
- [DOCUMENTATION_COMPLETE.md](DOCUMENTATION_COMPLETE.md)
- [FINAL_INTEGRATION_STATUS.md](FINAL_INTEGRATION_STATUS.md)
- [INTEGRATION_COMPLETE_SUMMARY.md](INTEGRATION_COMPLETE_SUMMARY.md)
- [OCT13_SESSION_SUMMARY.md](OCT13_SESSION_SUMMARY.md)

---

## 🚀 Quick Deployment Guide

### UAT Deployment (Allowed):
```bash
# 1. Run tests
./tests/run_tests.sh --regression

# 2. Push to GitHub
git push uat 25.10_UAT_DEPLOYMENT_FIX_CM

# 3. Deploy to Heroku
git push heroku 25.10_UAT_DEPLOYMENT_FIX_CM:main --force

# 4. Monitor
heroku logs --tail --app codamakutano

# 5. Verify
./tests/test_uat_urls.sh
```

### Production Deployment (REQUIRES USER PERMISSION):
⚠️ **NEVER deploy to production without explicit user permission!**

```bash
# ASK USER FIRST: "Ready to deploy to production?"

# If YES:
git push production 25.10_UAT_DEPLOYMENT_FIX_CM:main --force
heroku logs --tail --app codatrainingapp
```

---

## 🔄 Runtime & Stack Maintenance (November 8, 2025)

### Python Runtime
- ✅ Replaced `runtime.txt` with `.python-version` to align with Heroku’s new requirement.
- ✅ `.python-version` now pins only the major version (`3.12`) so patch-level security updates are applied automatically on rebuild.
- 📌 **Reminder:** any new deployment branch must keep `.python-version` at the repo root before pushing to Heroku.

### Heroku-24 Stack Upgrade Checklist
| Step | Owner | Status |
|------|-------|--------|
| Inventory add-ons/buildpacks for stack compatibility | DevOps | ✅ Automated via `scripts/production/create_heroku24_clone.sh` (Nov 8) |
| Clone UAT to a Heroku-24 staging app and run smoke tests | DevOps | 🟡 Ready (run clone script + smoke tests) |
| Capture database/app backups & schedule maintenance window | DevOps | 🔄 Pending |
| `heroku stack:set heroku-24` (UAT → Production rollout) | DevOps | 🔄 Pending (documented rollout plan below) |
| Post-upgrade verification (web, worker, beat dynos) | DevOps | 🔄 Pending |

> **Recommendation:** target the stack migration during the next release cycle so Heroku-22 deprecation warnings are cleared before year end.

### 🎯 Heroku-24 Staging Clone Checklist

Follow this sequence to stand up `codamakutano-24` and validate on the new stack:

1. **Provision clone + copy config**
   ```bash
   cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV
   ./scripts/production/create_heroku24_clone.sh
   ```
   - Script verifies CLI auth, recreates buildpacks/add-ons, and force-pushes `25.11_CODA_UAT_CM`.
2. **Smoke tests (automated)**
   ```bash
   BASE_URL=https://codamakutano-24.herokuapp.com ./tests/test_uat_urls.sh
   ```
   - `tests/test_uat_urls.sh` now accepts `BASE_URL` to re-use the existing URL coverage.
3. **Manual UI sweep**
   - Log in as managed client; confirm dashboard widgets (income gauge, UW timeline, scenario explorer) render.
   - Trigger staff risk guardrail modal to ensure assets load (collectstatic verification).
4. **Document results**
   - Capture observations + pass/fail notes in this README checklist and in `docs/apps/investing/ManagedOptionsTrading/07_DEPLOYMENT.md` change history.

### 🚀 Production Stack Swap Outline

Once `codamakutano-24` passes smoke tests:

1. **Freeze deploys** – coordinate maintenance window; capture Heroku + database backups.
2. **Promote clone** – either promote `codamakutano-24` through pipeline or rebuild original `codamakutano` after setting stack:
   ```bash
   heroku stack:set heroku-24 --app codamakutano
   git push heroku 25.11_CODA_PROD_CM:main --force
   heroku run "cd coda && python manage.py migrate" --app codamakutano
   heroku run "cd coda && python manage.py collectstatic --noinput" --app codamakutano
   ```
3. **Post-swap validation**
   - Re-run `tests/test_uat_urls.sh` with production base URL.
   - Check dyno health, worker logs, and scheduled jobs.
4. **Rollback plan**
   - Keep `codamakutano-24` online as hot standby until production passes 24-hour monitoring.
   - Use `heroku rollback` to revert to previous slug if issues detected.

---

## 📋 Pre-Deployment Checklist

- [ ] All regression tests pass
- [ ] Documentation updated
- [ ] Known issues reviewed
- [ ] UAT tested (if production deploy)
- [ ] User permission (if production)

---

**Last Updated:** November 8, 2025

