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

## 📋 Pre-Deployment Checklist

- [ ] All regression tests pass
- [ ] Documentation updated
- [ ] Known issues reviewed
- [ ] UAT tested (if production deploy)
- [ ] User permission (if production)

---

**Last Updated:** October 13, 2025

