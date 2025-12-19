# Registration System - Deployment

**Feature:** User Registration & Onboarding  
**Status:** ✅ Deployed to Production  
**Last Updated:** October 22, 2025

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### Code Ready:
- [x] All models migrated
- [x] Forms validated
- [x] Templates tested
- [x] Email templates professional
- [x] Error handling complete
- [x] Security reviewed
- [x] Tests passing (18/18)

### Configuration Ready:
- [x] Email service configured
- [x] MEDIA_ROOT set for resume uploads
- [x] ALLOWED_HOSTS configured
- [x] CSRF settings correct
- [x] Password hashers configured

### Infrastructure Ready:
- [x] Database migrations applied
- [x] Static files collected
- [x] Media storage configured
- [x] Email service credentials set

---

## ⚙️ ENVIRONMENT VARIABLES

### Required Configuration

**Email Service:**
```bash
# Heroku UAT
heroku config:set EMAIL_HOST_USER="noreply@codanalytics.net" --app codamakutano
heroku config:set EMAIL_HOST_PASSWORD="your_app_password" --app codamakutano
heroku config:set DEFAULT_FROM_EMAIL="noreply@codanalytics.net" --app codamakutano

# Heroku Production
heroku config:set EMAIL_HOST_USER="noreply@codanalytics.net" --app codatrainingapp
heroku config:set EMAIL_HOST_PASSWORD="your_app_password" --app codatrainingapp
heroku config:set DEFAULT_FROM_EMAIL="noreply@codanalytics.net" --app codatrainingapp
```

**Site URL (for verification links):**
```bash
# UAT
heroku config:set SITE_URL="https://codamakutano.herokuapp.com" --app codamakutano

# Production
heroku config:set SITE_URL="https://codatrainingapp.herokuapp.com" --app codatrainingapp
```

**File Upload:**
```bash
# Max upload size (5MB for resumes)
heroku config:set DATA_UPLOAD_MAX_MEMORY_SIZE="5242880" --app codamakutano
```

---

## 🚀 DEPLOYMENT PROCEDURE

### Step 1: Database Migrations

**UAT Deployment:**
```bash
# Push code
git push heroku feature/registration:main --app codamakutano

# Run migrations
heroku run "cd coda && python manage.py migrate accounts" --app codamakutano

# Verify migrations
heroku run "cd coda && python manage.py showmigrations accounts" --app codamakutano
```

**Expected Output:**
```
accounts
 [X] 0001_initial
 [X] 0002_add_email_verification
 [X] 0003_add_verification_token
 ...
```

---

### Step 2: Static Files Collection

```bash
# Collect static files
heroku run "cd coda && python manage.py collectstatic --noinput" --app codamakutano

# Verify
heroku run "cd coda && ls -la staticfiles/" --app codamakutano
```

---

### Step 3: Test Email Configuration

```bash
# Test email sending
heroku run "cd coda && python manage.py shell" --app codamakutano

# In shell:
>>> from accounts.utils import send_verification_email
>>> from accounts.models import CustomerUser
>>> user = CustomerUser.objects.first()
>>> send_verification_email(user)
```

**Expected:**
- Email sent successfully
- No errors
- Email received in inbox

---

### Step 4: Create Test User

```bash
# Create test user to verify flow
heroku run "cd coda && python manage.py shell" --app codamakutano

>>> from accounts.models import CustomerUser
>>> import uuid
>>> user = CustomerUser.objects.create(
...     username='testuser_reg',
...     first_name='Test',
...     last_name='User',
...     email='test@codanalytics.net',
...     category=1,  # Employee
...     verification_token=uuid.uuid4(),
...     email_verified=False
... )
>>> user.set_password('TestPass123')
>>> user.save()
```

Then test:
1. Visit `/accounts/join/` - form loads
2. Submit registration - user created
3. Check email - verification link received
4. Click link - email verified
5. Login - successful

---

## ✅ POST-DEPLOYMENT VERIFICATION

### Smoke Tests (UAT)

```bash
# 1. Registration form loads
curl -I https://codamakutano.herokuapp.com/accounts/join/
# Expected: HTTP/1.1 200 OK

# 2. Check database
heroku run "cd coda && python manage.py shell" --app codamakutano
>>> from accounts.models import CustomerUser
>>> CustomerUser.objects.count()  # Should return user count

# 3. Verify URLs work
heroku run "cd coda && python manage.py show_urls | grep accounts" --app codamakutano
```

---

### Manual UAT Testing

**Test Checklist:**
- [ ] Navigate to registration page
- [ ] Fill form with valid data
- [ ] Submit form
- [ ] Verify success message
- [ ] Check email received (< 60 seconds)
- [ ] Click verification link
- [ ] Verify email marked verified
- [ ] Login with new account
- [ ] Access dashboard successfully

**If any fail:** ROLLBACK immediately

---

## 🔄 ROLLBACK PROCEDURE

### If Critical Issue Found:

```bash
# 1. Check recent deployments
heroku releases --app codamakutano

# Output:
# v123  Deploy abc1234  user@email.com  2025/10/22 20:00:00
# v122  Deploy def5678  user@email.com  2025/10/21 15:30:00

# 2. Rollback to previous version
heroku rollback v122 --app codamakutano

# 3. Verify rollback successful
curl -I https://codamakutano.herokuapp.com/accounts/join/

# 4. If database migration issue, rollback migration
heroku run "cd coda && python manage.py migrate accounts 0010_previous" --app codamakutano
```

---

## 📊 DEPLOYMENT HISTORY

| Date | Version | Changes | Status | Notes |
|------|---------|---------|--------|-------|
| Oct 22, 2025 | v125 | 7-doc structure | ✅ Docs only | No code changes |
| Earlier 2025 | v100 | Email verification | ✅ Deployed | Production stable |
| Earlier 2025 | v95 | Resume upload | ✅ Deployed | Working well |
| Earlier 2025 | v90 | Initial registration | ✅ Deployed | Foundation |

---

## 🌍 ENVIRONMENT-SPECIFIC CONFIG

### Local Development

**Email Backend:**
```python
# local_settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Emails print to console instead of sending
```

**Test Registration:**
```bash
python manage.py runserver
# Visit http://localhost:8000/accounts/join/
# Check console for verification email
```

---

### UAT (codamakutano.herokuapp.com)

**Configuration:**
- Real email sending (SMTP)
- Test email addresses recommended
- Database: Heroku PostgreSQL
- File storage: Heroku ephemeral (warning: resumes lost on restart)

**Recommendation:** Configure AWS S3 for resume storage

---

### Production (codatrainingapp.herokuapp.com)

**Configuration:**
- Production email settings
- Real users, real data
- Persistent file storage required
- Enhanced monitoring

**Critical:** Test thoroughly in UAT first!

---

## 🔐 SECURITY DEPLOYMENT

### SSL/HTTPS Configuration

```python
# settings.py
SECURE_SSL_REDIRECT = True  # Force HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

**Verify:**
```bash
curl -I http://codamakutano.herokuapp.com/accounts/join/
# Should redirect to https://
```

---

### CORS Configuration (if API used)

```python
# Not needed for registration (form-based)
# Required only if API registration added in Phase 2
```

---

## 📈 MONITORING POST-DEPLOYMENT

### Week 1 After Deployment:
- [ ] Monitor registration rate (should be normal)
- [ ] Check email delivery (> 95%)
- [ ] Watch for errors (should be < 1%)
- [ ] User feedback (collect via support)

### Week 2-4:
- [ ] Analyze completion rate
- [ ] Identify drop-off points
- [ ] Plan improvements based on data

---

## 🎯 SUCCESS CRITERIA

**Deployment Successful When:**
- ✅ Registration form accessible
- ✅ Users can register successfully
- ✅ Verification emails deliver > 95%
- ✅ Email verification works
- ✅ No critical errors in logs
- ✅ Performance acceptable (< 3 sec)
- ✅ Zero security incidents

---

## 📞 DEPLOYMENT SUPPORT

**Deploy Team:** DevOps + Development  
**Support Team:** Customer Success  
**Escalation:** CTO if critical issue

**Deployment Window:** Anytime (low-risk, existing feature)  
**Rollback Ready:** Yes (< 5 minutes)

---

**Status:** ✅ Production Ready  
**Risk Level:** LOW (stable feature)  
**Recommended:** Deploy anytime



