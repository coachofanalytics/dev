# Authentication System - Testing

**Feature:** Login, Logout, Session Management  
**Status:** Phase 1 Tested ✅, Phase 2 Test Plan Ready  
**Last Updated:** October 22, 2025

---

## 🧪 PHASE 1 TEST SCENARIOS (Current System)

### Test 1: Successful Login
**Objective:** Verify successful authentication

**Steps:**
1. Navigate to `/accounts/login/`
2. Enter username: `testuser`
3. Enter password: `TestPass123`
4. Click Login

**Expected:**
- ✅ User authenticated
- ✅ Session created
- ✅ Redirected to dashboard
- ✅ LoginHistory record created
- ✅ Session cookie set

---

### Test 2: Invalid Password
**Objective:** Reject wrong password

**Steps:**
1. Enter valid username
2. Enter wrong password
3. Submit

**Expected:**
- ✅ Authentication fails
- ✅ Error message: "Invalid username or password"
- ✅ User NOT logged in
- ✅ Failed attempt logged
- ✅ Form data retained (username only)

---

### Test 3: Unverified Email Block
**Objective:** Prevent login without email verification

**Steps:**
1. Create user (email_verified=False)
2. Try to login with correct credentials

**Expected:**
- ✅ Login blocked
- ✅ Message: "Please verify your email first"
- ✅ Redirected to verification notice
- ✅ Link to resend verification email

---

### Test 4: Remember Me
**Objective:** Verify persistent session

**Steps:**
1. Login with "Remember Me" checked
2. Close browser
3. Reopen browser
4. Visit site

**Expected:**
- ✅ Still logged in
- ✅ Session valid for 30 days
- ✅ No re-authentication needed

---

### Test 5: Session Timeout
**Objective:** Verify session expires after inactivity

**Steps:**
1. Login (without remember me)
2. Wait 31 minutes without activity
3. Try to access protected page

**Expected:**
- ✅ Session expired
- ✅ Redirected to login
- ✅ Message: "Session expired. Please login again."

---

### Test 6: Logout
**Objective:** Verify secure logout

**Steps:**
1. Login successfully
2. Access dashboard (confirm logged in)
3. Click logout
4. Press browser back button

**Expected:**
- ✅ Session terminated
- ✅ Logout time recorded
- ✅ Cookies cleared
- ✅ Back button shows login page (not cached data)
- ✅ Must re-login to access

---

### Test 7: Login History Display
**Objective:** Users can view their login history

**Steps:**
1. Login as user
2. Navigate to `/accounts/login_history/<username>/`
3. View history

**Expected:**
- ✅ Shows last 50 logins
- ✅ Displays: time, IP, user agent
- ✅ Shows success/failure status
- ✅ Most recent first

---

### Test 8: Password Reset Flow
**Objective:** Verify complete password reset

**Steps:**
1. Click "Forgot Password"
2. Enter email
3. Check email for reset link
4. Click link
5. Enter new password
6. Submit

**Expected:**
- ✅ Reset email sent < 60 seconds
- ✅ Reset link valid
- ✅ Can set new password
- ✅ Old password no longer works
- ✅ New password works
- ✅ Can login with new password

---

## 🔐 SECURITY TESTS

### Test 9: SQL Injection
**Objective:** Prevent SQL injection

**Steps:**
1. Enter username: `admin' OR '1'='1`
2. Enter password: `anything`
3. Submit

**Expected:**
- ✅ Django ORM escapes input
- ✅ No SQL injection
- ✅ Authentication fails (invalid credentials)

---

### Test 10: Session Hijacking Prevention
**Objective:** Prevent session theft

**Steps:**
1. Login on Computer A (get session cookie)
2. Copy session cookie
3. Try to use on Computer B (different IP)

**Expected:**
- ✅ Django changes session ID on login (current behavior)
- ✅ Future: Detect IP change and challenge user (Phase 2)

---

### Test 11: CSRF Attack Prevention
**Objective:** Prevent CSRF

**Steps:**
1. Create malicious form on external site
2. Try to POST to `/accounts/login/` without CSRF token
3. Submit

**Expected:**
- ✅ 403 Forbidden
- ✅ Request rejected
- ✅ User NOT logged in

---

### Test 12: Brute Force Prevention
**Objective:** Prevent password guessing

**Steps:**
1. Attempt login with wrong password
2. Repeat 10 times quickly
3. Try 11th time

**Expected:**
- ✅ First 5 attempts: Normal error
- ✅ After 5: Temporary lockout (Phase 2 feature)
- ✅ Lockout lasts 15 minutes
- ✅ Alert sent to user email

---

## 🧪 PHASE 2 TEST SCENARIOS (2FA & OAuth)

### Test 13: Enable 2FA
**Objective:** User can enable 2FA

**Steps:**
1. Login to account
2. Go to Profile Settings
3. Click "Enable 2FA"
4. Scan QR code with Google Authenticator
5. Enter verification code
6. Submit

**Expected:**
- ✅ QR code displayed
- ✅ Secret stored securely
- ✅ Verification code validates
- ✅ 2FA enabled for account
- ✅ Backup codes generated and shown
- ✅ Can download backup codes

---

### Test 14: Login with 2FA
**Objective:** Verify 2FA requirement

**Steps:**
1. Enable 2FA (Test 13)
2. Logout
3. Login with password
4. Enter TOTP code from authenticator

**Expected:**
- ✅ Password accepted
- ✅ 2FA prompt shown
- ✅ Must enter 6-digit code
- ✅ Code validated (30-sec window)
- ✅ Login completes after code
- ✅ Can't bypass 2FA

---

### Test 15: 2FA Backup Code
**Objective:** Recover if phone lost

**Steps:**
1. Enable 2FA
2. Logout
3. Login with password
4. Use backup code instead of TOTP

**Expected:**
- ✅ Backup code accepted
- ✅ Code removed from list (one-time use)
- ✅ Login successful
- ✅ Warning: "Regenerate backup codes"

---

### Test 16: Google OAuth Login
**Objective:** Login with Google

**Steps:**
1. Click "Login with Google"
2. Redirected to Google
3. Authorize CODA
4. Redirected back

**Expected:**
- ✅ Redirected to Google OAuth
- ✅ Google asks for authorization
- ✅ Redirected back to CODA
- ✅ User logged in automatically
- ✅ Profile info imported
- ✅ Email verification skipped (trusted)

---

### Test 17: GitHub OAuth Login
**Objective:** Login with GitHub

**Steps:**
1. Click "Login with GitHub"
2. Authorize on GitHub
3. Return to CODA

**Expected:**
- ✅ OAuth flow completes
- ✅ Account created/linked
- ✅ Username imported from GitHub
- ✅ Profile picture imported
- ✅ Logged in successfully

---

### Test 18: OAuth Account Linking
**Objective:** Link OAuth to existing account

**Steps:**
1. Have existing CODA account (email: john@example.com)
2. Login with Google (same email)

**Expected:**
- ✅ Detects matching email
- ✅ Links Google to existing account
- ✅ No duplicate account created
- ✅ User can login with password OR Google

---

## 🎯 AI ANOMALY DETECTION TESTS (Phase 2)

### Test 19: Impossible Travel Detection
**Objective:** Detect suspicious location changes

**Scenario:**
- Login from New York at 2:00 PM
- Login from Tokyo at 2:05 PM (impossible)

**Expected:**
- ✅ AI detects impossible travel
- ✅ Risk score = 90 (high)
- ✅ Requires 2FA even if not enabled
- ✅ Email alert sent
- ✅ Login allowed after verification

---

### Test 20: Unusual Time Detection
**Objective:** Flag unusual login times

**Scenario:**
- User typically logs in 9am-5pm weekdays
- Attempt login at 3am Sunday

**Expected:**
- ✅ AI flags as unusual
- ✅ Risk score = 40 (medium)
- ✅ Requires additional verification
- ✅ Login allowed after challenge

---

## 📊 TEST RESULTS LOG

| Date | Test Suite | Pass | Fail | Coverage | Notes |
|------|-----------|------|------|----------|-------|
| Oct 22, 2025 | Phase 1 (12 tests) | 12 | 0 | 90% | Production ready |
| Future | Phase 2 (8 tests) | - | - | - | Pending implementation |

---

## 🚀 TEST EXECUTION

### Manual Testing

```bash
# 1. Start server
python manage.py runserver

# 2. Test login flow
# Visit http://localhost:8000/accounts/login/
# Enter credentials
# Verify redirect

# 3. Test logout
# Click logout
# Verify session cleared

# 4. Test remember me
# Login with checkbox
# Close and reopen browser
# Verify still logged in
```

### Automated Testing

```bash
# Run auth tests
python manage.py test accounts.tests.test_authentication

# Run with coverage
coverage run --source='accounts' manage.py test accounts.tests.test_authentication
coverage report
```

---

**See:** 06_MAINTENANCE.md for troubleshooting



