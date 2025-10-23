# GoToMeeting Integration - Deployment

**Last Updated:** October 22, 2025  
**Status:** ✅ Deployed (needs improvements before wider use)

---

## ⚙️ ENVIRONMENT VARIABLES

### Required
```bash
API_CLIENT_ID=your_gotomeeting_client_id
API_CLIENT_SECRET=your_gotomeeting_client_secret
```

### Optional (Google Drive)
```bash
GOOGLE_ACCESS_TOKEN=your_token
GOOGLE_REFRESH_TOKEN=your_refresh_token
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

---

## 🚀 DEPLOYMENT COMMANDS

### Deploy to UAT
```bash
git push heroku [branch]:main
heroku config:set API_CLIENT_ID=xxxxx --app codamakutano
heroku config:set API_CLIENT_SECRET=xxxxx --app codamakutano
```

### Deploy to Production (REQUIRES PERMISSION)
```bash
# ASK USER FIRST!
git checkout 25.10_CODA_PROD_v2_CM
git push production 25.10_CODA_PROD_v2_CM:main
heroku config:set API_CLIENT_ID=xxxxx --app codatrainingapp
heroku config:set API_CLIENT_SECRET=xxxxx --app codatrainingapp
```

---

## ✅ POST-DEPLOYMENT VERIFICATION

```bash
# Test meeting form loads
curl -I https://codamakutano.herokuapp.com/getdata/meetingFormView/

# Test OAuth redirect
# Navigate to URL, should redirect to LogMeIn if no token
```

---

## ⚠️ DEPLOYMENT WARNINGS

**Before wider deployment:**
1. ⚠️ Fix 23 critical issues (see 06_MAINTENANCE.md)
2. ⚠️ Implement Phase 1 fixes (data model, security)
3. ⚠️ Add proper error handling
4. ⚠️ Test duplicate prevention

**Current state:** Works but not production-ready for scale

---

## 📊 DEPLOYMENT HISTORY

| Date | Version | Changes | Status |
|------|---------|---------|--------|
| Oct 22, 2025 | Current | 7-doc migration | ✅ Docs only |
| [Earlier] | Unknown | Initial implementation | ✅ Working |

---

**Recommendation:** Implement Phase 1 improvements before production deployment


