# Authentication System - Deployment

**Feature:** Login, Logout, Session Management  
**Status:** Phase 1 Deployed ✅, Phase 2 Pending  
**Last Updated:** October 22, 2025

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### Phase 1 (Current) - DEPLOYED ✅
- [x] Password hashing configured
- [x] Session security enabled
- [x] HTTPS enforced
- [x] CSRF protection active
- [x] Email verification enforced
- [x] Login history tracking
- [x] Tests passing (12/12)

### Phase 2 (2FA + OAuth) - PENDING
- [ ] django-otp installed
- [ ] django-allauth installed
- [ ] OAuth apps registered (Google, GitHub)
- [ ] 2FA QR code generation tested
- [ ] Backup codes system tested
- [ ] OAuth callbacks working
- [ ] Security review complete
- [ ] Tests passing (20/20)

---

## ⚙️ ENVIRONMENT VARIABLES

### Current Configuration (Phase 1)

**Session Security:**
```bash
# Already in settings.py (no env vars needed)
SESSION_COOKIE_SECURE=True  # HTTPS only
SESSION_COOKIE_HTTPONLY=True  # No JavaScript access
SESSION_COOKIE_SAMESITE='Lax'  # CSRF protection
SESSION_COOKIE_AGE=1800  # 30 minutes
```

**Password Hashing:**
```bash
# Already in settings.py
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]
```

---

### Phase 2 Configuration (OAuth + 2FA)

**Google OAuth:**
```bash
# UAT
heroku config:set GOOGLE_OAUTH_CLIENT_ID="xxx.apps.googleusercontent.com" --app codamakutano
heroku config:set GOOGLE_OAUTH_CLIENT_SECRET="GOCSPX-xxx" --app codamakutano
heroku config:set GOOGLE_OAUTH_REDIRECT_URI="https://codamakutano.herokuapp.com/accounts/oauth/google/callback/" --app codamakutano

# Production
heroku config:set GOOGLE_OAUTH_CLIENT_ID="xxx.apps.googleusercontent.com" --app codatrainingapp
heroku config:set GOOGLE_OAUTH_CLIENT_SECRET="GOCSPX-xxx" --app codatrainingapp
heroku config:set GOOGLE_OAUTH_REDIRECT_URI="https://codatrainingapp.herokuapp.com/accounts/oauth/google/callback/" --app codatrainingapp
```

**GitHub OAuth:**
```bash
# UAT
heroku config:set GITHUB_OAUTH_CLIENT_ID="Iv1.xxx" --app codamakutano
heroku config:set GITHUB_OAUTH_CLIENT_SECRET="xxx" --app codamakutano
heroku config:set GITHUB_OAUTH_REDIRECT_URI="https://codamakutano.herokuapp.com/accounts/oauth/github/callback/" --app codamakutano
```

**2FA Settings:**
```bash
# 2FA issuer name (shows in Google Authenticator)
heroku config:set OTP_TOTP_ISSUER="CODA" --app codamakutano

# Backup code count
heroku config:set BACKUP_CODE_COUNT="10" --app codamakutano
```

---

## 🚀 DEPLOYMENT PROCEDURE

### Phase 1 (Already Deployed) ✅

**Initial Deployment:**
```bash
# 1. Push code
git push heroku main --app codamakutano

# 2. Run migrations
heroku run "cd coda && python manage.py migrate accounts" --app codamakutano

# 3. Verify authentication works
curl -I https://codamakutano.herokuapp.com/accounts/login/
# Expected: 200 OK

# 4. Test login
# Manual: Login via browser
# Verify: Session created, redirect works
```

---

### Phase 2 Deployment (2FA + OAuth) - FUTURE

**Step 1: Install Dependencies**
```bash
# Add to requirements.txt
django-otp==1.2.0
qrcode==7.4.2
pyotp==2.9.0
django-allauth==0.57.0

# Deploy with new requirements
git add requirements.txt
git commit -m "Add 2FA and OAuth dependencies"
git push heroku phase2-auth:main --app codamakutano
```

**Step 2: Database Migrations**
```bash
# Create migrations
python manage.py makemigrations accounts

# Apply migrations in UAT
heroku run "cd coda && python manage.py migrate accounts" --app codamakutano

# Verify
heroku run "cd coda && python manage.py shell" --app codamakutano
>>> from accounts.models import TwoFactorAuth, OAuthConnection
>>> TwoFactorAuth.objects.count()
>>> OAuthConnection.objects.count()
```

**Step 3: Configure OAuth Providers**

**Google OAuth Setup:**
1. Go to https://console.cloud.google.com/
2. Create new project "CODA UAT"
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI
6. Copy Client ID and Secret
7. Set environment variables (see above)

**GitHub OAuth Setup:**
1. Go to https://github.com/settings/developers
2. Click "New OAuth App"
3. Application name: "CODA UAT"
4. Homepage URL: https://codamakutano.herokuapp.com
5. Authorization callback URL: https://codamakutano.herokuapp.com/accounts/oauth/github/callback/
6. Register application
7. Copy Client ID and Secret
8. Set environment variables

**Step 4: Deploy Code**
```bash
git push heroku phase2-auth:main --app codamakutano
```

**Step 5: Test in UAT**
- Test password login (existing users)
- Test 2FA enrollment
- Test 2FA login
- Test Google OAuth login
- Test GitHub OAuth login
- Test account linking
- Test backup codes

---

## ✅ POST-DEPLOYMENT VERIFICATION

### Phase 1 Verification (Current)

```bash
# 1. Login page accessible
curl -I https://codamakutano.herokuapp.com/accounts/login/
# Expected: HTTP/1.1 200 OK

# 2. Test authentication
# Manual browser test:
# - Login with valid credentials → Success
# - Login with invalid → Error message
# - Unverified email → Blocked

# 3. Check session creation
heroku run "cd coda && python manage.py shell" --app codamakutano
>>> from django.contrib.sessions.models import Session
>>> Session.objects.count()  # Should have active sessions

# 4. Verify login history
>>> from accounts.models import LoginHistory
>>> LoginHistory.objects.filter(success=True).count()
```

---

### Phase 2 Verification (Future)

**2FA Testing:**
```bash
# 1. Enable 2FA for test user
# Visit /accounts/2fa/enable/
# Scan QR code
# Verify setup

# 2. Logout and login again
# Should prompt for TOTP code

# 3. Test backup code
# Use one backup code
# Verify it's removed from list
```

**OAuth Testing:**
```bash
# 1. Test Google login
# Click "Login with Google"
# Authorize on Google
# Verify returned to CODA logged in

# 2. Check OAuth connection created
heroku run "cd coda && python manage.py shell" --app codamakutano
>>> from accounts.models import OAuthConnection
>>> OAuthConnection.objects.filter(provider='google').count()

# 3. Test GitHub login similarly
```

---

## 🔄 ROLLBACK PROCEDURE

### If Critical Auth Issue:

```bash
# 1. Check recent releases
heroku releases --app codamakutano

# 2. Rollback to previous version
heroku rollback v<previous> --app codamakutano

# 3. If database changes, rollback migrations
heroku run "cd coda && python manage.py migrate accounts 0015_previous" --app codamakutano

# 4. Verify authentication works
curl -I https://codamakutano.herokuapp.com/accounts/login/

# 5. Test login manually
```

**Emergency:** If complete auth failure, enable maintenance mode:
```bash
heroku maintenance:on --app codamakutano
# Fix issue
heroku maintenance:off --app codamakutano
```

---

## 📊 DEPLOYMENT HISTORY

| Date | Version | Changes | Status | Notes |
|------|---------|---------|--------|-------|
| Oct 22, 2025 | v125 | 7-doc structure | ✅ Docs | No code changes |
| Earlier 2025 | v100 | Email verification check | ✅ Deployed | Stable |
| Earlier 2025 | v95 | Login history tracking | ✅ Deployed | Working well |
| Earlier 2025 | v90 | Initial auth system | ✅ Deployed | Foundation |
| Future | v130 | 2FA + OAuth (Phase 2) | ⏳ Planned | 6-8 weeks |

---

## 🌍 ENVIRONMENT-SPECIFIC CONFIG

### Local Development

**Session Settings:**
```python
# local_settings.py
SESSION_COOKIE_SECURE = False  # Allow HTTP for local
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 1800
```

**Testing:**
```bash
python manage.py runserver
# Visit http://localhost:8000/accounts/login/
# Test login/logout flows
```

---

### UAT (codamakutano.herokuapp.com)

**Configuration:**
- HTTPS enforced
- Real session security
- Test OAuth apps (sandbox)
- Test 2FA setup

**Purpose:**
- User acceptance testing
- Security testing
- Performance testing
- Pre-production validation

---

### Production (codatrainingapp.herokuapp.com)

**Configuration:**
- Production OAuth apps (live)
- Enhanced monitoring
- Real user data
- Strict security

**Deployment:**
- Only after UAT approval
- During low-traffic window
- Rollback ready
- Support team on standby

---

## 🔐 SECURITY CHECKLIST

### Pre-Deployment Security Review:

- [x] HTTPS enforced (SECURE_SSL_REDIRECT=True)
- [x] Session cookies secure
- [x] CSRF protection enabled
- [x] Password hashing strong (PBKDF2, 260K iterations)
- [x] XSS protection enabled
- [x] Clickjacking protection enabled
- [ ] 2FA available (Phase 2)
- [ ] OAuth secure implementation (Phase 2)
- [ ] Rate limiting active (Phase 2)
- [ ] Security headers configured

---

## 📞 DEPLOYMENT SUPPORT

**Deploy Team:** DevOps + Backend  
**Testing:** QA Team  
**Approver:** CTO

**Deployment Window:**
- Phase 1: Anytime (low risk)
- Phase 2: Off-peak hours
- Rollback: < 5 minutes

**On-Call:** Backend engineer during Phase 2 deployment

---

## 🎯 SUCCESS CRITERIA

**Deployment Successful When:**
- ✅ Login page loads
- ✅ Authentication works
- ✅ Sessions created properly
- ✅ Logout works
- ✅ Password reset functional
- ✅ No errors in logs
- ✅ Login history tracking
- ✅ Performance acceptable (< 1 sec)

**Phase 2 Additional:**
- 2FA enrollment works
- 2FA login verified
- OAuth providers connected
- Google login functional
- GitHub login functional
- No security issues

---

**Status:** Phase 1 deployed and stable ✅  
**Next:** Phase 2 deployment (2FA + OAuth) pending development



