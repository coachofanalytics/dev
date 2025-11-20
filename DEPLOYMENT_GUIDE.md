# Biashara Bridges - Comprehensive Upgrade & Deployment Guide

## 🎉 What's Been Implemented

### ✅ Phase 1: Critical Bug Fixes
- Fixed Transaction.user FK issue - all transactions now properly linked to users
- Fixed gateway_transaction_id field inconsistency (was external_reference)
- Fixed Stripe form field mismatch (payment_method_id vs stripe_token)
- Fixed PayPal method calls (create_payment → process_payment)
- Fixed M-Pesa method calls (stk_push → process_payment)
- Added PAYPAL_IPN_URL setting for webhook verification
- Removed dead code (Wallet.get_features_list, views_backup.py)

### ✅ Phase 2: Security Enhancements
- Removed insecure default SECRET_KEY (now required in .env)
- Changed DEBUG default to False (safer for production)
- Added rate limiting:
  - Login: 10 attempts/hour per IP
  - Registration: 5 attempts/hour per IP
  - Payment endpoints: 20 attempts/hour per user
- Added file upload validation:
  - Documents: 5MB max, PDF/DOC/DOCX only, MIME type verification
  - Images: 2MB max, JPG/PNG/GIF only, MIME type verification
- Added production security settings:
  - SSL redirect
  - HSTS headers (1 year)
  - Secure cookies
  - Content type nosniff
  - XSS filter

### ✅ Phase 3: Code Refactoring
- Created TransactionService for business logic
- Created SubscriptionService for subscription management
- Added custom exception classes for better error handling
- Improved code organization and maintainability

### ✅ Phase 4: Payment Retry Logic
- Installed and configured Celery + Redis
- Added retry_count field to Transaction model
- Created PaymentRetryService with exponential backoff (1h, 4h, 24h)
- Created Celery tasks:
  - `retry_failed_payment` - Retry individual failed payments
  - `check_pending_transactions_task` - Check for transactions to retry (runs every 30 min)
  - `expire_subscriptions_task` - Expire old subscriptions (runs daily at 2 AM)
  - `cancel_old_pending_transactions` - Cancel stuck pending transactions

### ✅ Phase 5: Subscription Auto-Renewal
- Created management commands:
  - `process_renewals` - Process subscription auto-renewals
  - `expire_subscriptions` - Expire subscriptions past end date
- Implemented renewal logic with wallet payment support
- Added scheduled downgrade functionality

---

## 📋 Pre-Deployment Checklist

### 1. Local Testing (IMPORTANT!)

Before deploying, test locally:

```bash
# 1. Create database migrations
cd C:\Users\Mwongela\projects\biashara_bridges
python manage.py makemigrations
python manage.py migrate

# 2. Install new dependencies
pip install -r requirements.txt

# 3. Verify SECRET_KEY is set in .env
# Make sure .env has: SECRET_KEY=your-actual-secret-key

# 4. Test critical flows
python manage.py runserver
# Test: login, registration, deposit initiation (don't complete payment)

# 5. Test management commands
python manage.py expire_subscriptions --dry-run
python manage.py process_renewals --dry-run
```

### 2. Commit Changes to Git

```bash
git add .
git status  # Review changes
git commit -m "Major upgrade: bug fixes, security, Celery, auto-renewals

- Fixed all 7 critical bugs (transaction fields, payment gateway methods)
- Added security: rate limiting, file validation, production settings
- Added Celery + Redis for background tasks
- Implemented payment retry logic with exponential backoff
- Added subscription auto-renewal management commands
- Created transaction and subscription services
- Added custom exceptions for better error handling

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 🚀 Heroku Deployment Steps

### 1. Ensure Heroku CLI is Installed and Logged In

```bash
heroku --version
heroku auth:whoami
```

### 2. Verify Heroku App Info

```bash
heroku apps:info --app codadev
```

### 3. Add Redis Addon (Required for Celery)

```bash
# Essential tier ($5/month) - required for production
heroku addons:create heroku-redis:mini --app codadev

# Verify Redis was added
heroku addons --app codadev
heroku config:get REDIS_URL --app codadev
```

### 4. Add Heroku Scheduler Addon (For Management Commands)

```bash
# Free tier
heroku addons:create scheduler:standard --app codadev
```

### 5. Set Environment Variables

```bash
# CRITICAL: Set a strong SECRET_KEY
heroku config:set SECRET_KEY="your-strong-random-secret-key-here" --app codadev

# Set DEBUG to False for production
heroku config:set DEBUG=False --app codadev

# Verify settings
heroku config --app codadev
```

### 6. Scale Celery Worker

```bash
# This will cost extra - worker dyno ($7/month for hobby tier)
heroku ps:scale worker=1 --app codadev

# For free tier, keep worker=0 and use only Heroku Scheduler
# heroku ps:scale worker=0 --app codadev
```

### 7. Push to Heroku

```bash
# Make sure you're on the right branch
git branch

# Push to Heroku (migrations run automatically via release phase)
git push heroku Main:main
```

### 8. Verify Deployment

```bash
# Check logs
heroku logs --tail --app codadev

# Check dyno status
heroku ps --app codadev

# Open app
heroku open --app codadev
```

### 9. Configure Heroku Scheduler

```bash
# Open scheduler dashboard
heroku addons:open scheduler --app codadev
```

In the Heroku Scheduler web interface, add these jobs:

**Job 1: Expire Subscriptions**
- Command: `python manage.py expire_subscriptions`
- Frequency: Daily at 2:00 AM (UTC)

**Job 2: Process Renewals**
- Command: `python manage.py process_renewals --days-before=1`
- Frequency: Daily at 1:00 AM (UTC)

### 10. Test on Heroku

```bash
# Test management commands manually
heroku run python manage.py expire_subscriptions --dry-run --app codadev
heroku run python manage.py process_renewals --dry-run --app codadev

# Check Celery worker logs (if running)
heroku logs --tail --ps worker --app codadev
```

---

## 🔧 Post-Deployment Configuration

### 1. Database Considerations

The `retry_count` field was added to the Transaction model. The migration should handle this automatically, but verify:

```bash
heroku run python manage.py showmigrations --app codadev
```

### 2. Monitor Application

```bash
# Watch logs for errors
heroku logs --tail --app codadev

# Check for failed transactions
heroku run python manage.py shell --app codadev
# In shell: Transaction.objects.filter(status='failed').count()
```

### 3. Test Payment Flows

- Test user registration with document upload
- Test login (rate limiting)
- Test deposit initiation (Stripe, PayPal, M-Pesa)
- Verify transactions are created correctly

---

## 🎯 Heroku Addons Summary

| Addon | Tier | Cost | Purpose |
|-------|------|------|---------|
| heroku-postgresql | essential-0 | ~$5/month | Database |
| heroku-redis | mini | ~$3/month | Celery broker |
| scheduler | standard | Free | Cron jobs |
| Worker dyno | hobby | $7/month | Celery worker (optional) |

**Total Monthly Cost**: ~$15/month (with worker) or ~$8/month (without worker, Scheduler only)

---

## ⚠️ Important Notes

### Celery Worker vs Heroku Scheduler

**Option A: Use Celery Worker (Recommended for production)**
- Pros: Real-time payment retries, faster processing
- Cons: Costs $7/month extra
- Setup: `heroku ps:scale worker=1 --app codadev`

**Option B: Use Only Heroku Scheduler (Budget option)**
- Pros: Free, sufficient for daily tasks
- Cons: No real-time retries, relies on scheduled runs
- Setup: `heroku ps:scale worker=0 --app codadev`

### Payment Gateway Configuration

Make sure these are set on Heroku:
```bash
heroku config:set STRIPE_PUBLIC_KEY="pk_live_..." --app codadev
heroku config:set STRIPE_SECRET_KEY="sk_live_..." --app codadev
# etc for PayPal and M-Pesa
```

### Database Backups

```bash
# Create backup
heroku pg:backups:capture --app codadev

# Download backup
heroku pg:backups:download --app codadev
```

---

## 🐛 Troubleshooting

### Deployment Fails

```bash
# Check build logs
heroku logs --tail --app codadev

# Check recent releases
heroku releases --app codadev

# Rollback if needed
heroku rollback --app codadev
```

### Migrations Fail

```bash
# Run migrations manually
heroku run python manage.py migrate --app codadev

# Check migration status
heroku run python manage.py showmigrations --app codadev
```

### Celery Worker Issues

```bash
# Check worker logs
heroku logs --tail --ps worker --app codadev

# Restart worker
heroku ps:restart worker --app codadev

# Test Celery connection
heroku run python -c "from config.celery import app; print(app.control.inspect().active())" --app codadev
```

---

## 📊 Monitoring After Deployment

### Key Metrics to Watch

1. **Transaction Success Rate**
   ```bash
   heroku run python manage.py shell --app codadev
   # Transaction.objects.filter(status='completed').count() / Transaction.objects.count()
   ```

2. **Failed Payments**
   ```bash
   # Check for failed transactions needing retry
   heroku run python manage.py shell --app codadev
   # Transaction.objects.filter(status='failed', retry_count__lt=3).count()
   ```

3. **Subscription Status**
   ```bash
   # Check active vs expired subscriptions
   heroku run python manage.py shell --app codadev
   # UserSubscription.objects.filter(status='active').count()
   ```

---

## ✅ Success Criteria

After deployment, verify:
- [ ] App loads without errors
- [ ] Users can register (with file upload)
- [ ] Users can login (rate limiting works)
- [ ] Deposit forms load correctly
- [ ] Transactions are created with proper user FK
- [ ] Heroku Scheduler jobs are configured
- [ ] Redis is connected
- [ ] No errors in logs

---

## 🎓 For Future Reference

### Adding More Celery Tasks

1. Define task in `payments/tasks.py`
2. Import and use: `from payments.tasks import my_task`
3. Call with: `my_task.delay(args)`

### Running Management Commands

```bash
# Locally
python manage.py process_renewals --days-before=7

# On Heroku
heroku run python manage.py process_renewals --days-before=7 --app codadev
```

---

🎉 **Deployment Complete!** Your application now has robust payment processing, auto-renewals, and enhanced security.
