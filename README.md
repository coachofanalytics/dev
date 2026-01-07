# Biashara Bridges - Investment & Marketplace Platform

**Last Updated:** January 2, 2026
**Platform:** Django 4.2+ / Python 3.11
**Live URL:** https://biasharadev-68034baaf749.herokuapp.com
**Repository:** https://github.com/pmzomo/biasharaBB

---

## Overview

Biashara Bridges is a comprehensive Django-based platform connecting **investors**, **businesses**, and **individuals** within the East African market. The platform serves as a multi-sided marketplace enabling investment opportunities, job placements, and professional networking with enterprise-grade security, compliance, and payment processing.

**Core Purpose:**
- **Investors** - Discover investment opportunities, manage portfolios
- **Businesses** - Seek funding, post jobs, find talent and partners
- **Individuals** - Apply for jobs, explore investment opportunities

---

## High-Level Architecture

```
+---------------------------------------------------------------------------+
|                           CLIENT LAYER                                     |
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  |  Web Portal   |  | Mobile Apps   |  | Admin Portal  |  |API Consumers  ||
|  |  (Bootstrap)  |  |  (Future)     |  | (Django Admin)|  |   (REST)      ||
|  +---------------+  +---------------+  +---------------+  +---------------+|
+---------------------------------------------------------------------------+
                                    |
                                    | HTTP/HTTPS
                                    v
+---------------------------------------------------------------------------+
|                        PRESENTATION LAYER                                  |
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  |   Templates   |  |  Static Files |  | Django Admin  |  |   Forms       ||
|  |  (HTML/JS)    |  | (WhiteNoise)  |  |  Interface    |  | (Validation)  ||
|  +---------------+  +---------------+  +---------------+  +---------------+|
+---------------------------------------------------------------------------+
                                    |
                                    v
+---------------------------------------------------------------------------+
|                     VIEW/CONTROLLER LAYER                                  |
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  |   views.py    |  |   urls.py     |  |  decorators   |  |  middleware   ||
|  | (Page Views)  |  |  (Routing)    |  | (@login_req)  |  | (Auth/GDPR)   ||
|  +---------------+  +---------------+  +---------------+  +---------------+|
+---------------------------------------------------------------------------+
                                    |
                                    | Calls
                                    v
+---------------------------------------------------------------------------+
|                          SERVICE LAYER                                     |
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  |   Payment     |  |    Wallet     |  |     KYC       |  |   Security    ||
|  |   Services    |  |   Service     |  |   Service     |  |   Service     ||
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  |  Analytics    |  | Notification  |  |    Funds      |  |   Currency    ||
|  |   Service     |  |   Service     |  | Segregation   |  |   Service     ||
|  +---------------+  +---------------+  +---------------+  +---------------+|
+---------------------------------------------------------------------------+
                                    |
                                    | Uses
                                    v
+---------------------------------------------------------------------------+
|                       DATA ACCESS LAYER                                    |
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  |   Managers    |  |  QuerySets    |  |    ORM        |  |    Redis      ||
|  | (Custom ORM)  |  | (Filtering)   |  |  (Models)     |  |   (Cache)     ||
|  +---------------+  +---------------+  +---------------+  +---------------+|
+---------------------------------------------------------------------------+
                                    |
                                    v
+---------------------------------------------------------------------------+
|                           MODEL LAYER                                      |
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  |    User       |  |    Wallet     |  |  Transaction  |  |   Business    ||
|  |  UserProfile  |  | SpendingLimit |  |   Invoice     |  |   Profile     ||
|  |   MFADevice   |  | ActivityLog   |  |  Subscription |  | Opportunity   ||
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  |  KYCDocument  |  |   AuditLog    |  | ConsentRecord |  |  FraudAlert   ||
|  |Verification   |  | LoginHistory  |  |   DataExport  |  |PaymentDispute ||
|  |    Level      |  |               |  |               |  |               ||
|  +---------------+  +---------------+  +---------------+  +---------------+|
+---------------------------------------------------------------------------+
                                    |
                                    v
+---------------------------------------------------------------------------+
|                          INTEGRATIONS                                      |
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  |    Stripe     |  |    PayPal     |  |    M-Pesa     |  |   CashApp     ||
|  |  (Cards/Intl) |  |   (Wallet)    |  | (Mobile Money)|  |   (Square)    ||
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  |    Venmo      |  |    Email      |  | Social Auth   |  |    Redis      ||
|  | (Braintree)   |  | (SendGrid)    |  |(Google/FB)    |  |   (Celery)    ||
|  +---------------+  +---------------+  +---------------+  +---------------+|
+---------------------------------------------------------------------------+
                                    |
                                    | Async
                                    v
+---------------------------------------------------------------------------+
|                       BACKGROUND JOBS                                      |
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  |   Celery      |  |   Webhooks    |  |Reconciliation |  |  Scheduled    ||
|  |   Workers     |  |  Processing   |  |    Tasks      |  |   Reports     ||
|  +---------------+  +---------------+  +---------------+  +---------------+|
+---------------------------------------------------------------------------+
                                    |
                                    v
+---------------------------------------------------------------------------+
|                        OBSERVABILITY                                       |
|  +---------------+  +---------------+  +---------------+  +---------------+|
|  |   Logging     |  |  Audit Trails |  |  FraudAlerts  |  |  Monitoring   ||
|  | (Django Log)  |  |  (AuditLog)   |  | (Detection)   |  |  (Anomaly)    ||
|  +---------------+  +---------------+  +---------------+  +---------------+|
+---------------------------------------------------------------------------+
```

---

## Directory / Module Structure

```
biashara_bridges/
|
+-- config/                          # Project configuration
|   +-- settings.py                  # Django settings
|   +-- urls.py                      # Root URL routing
|   +-- wsgi.py                      # WSGI entry point
|
+-- accounts/                        # User management & authentication
|   +-- models.py                    # User, UserProfile, Staff, Category
|   +-- views.py                     # Login, register, profile views
|   +-- forms.py                     # Authentication forms
|   +-- mfa/                         # Multi-factor authentication
|   |   +-- views.py                 # MFA setup, verify, backup codes
|   |   +-- models.py                # MFADevice, BackupCode
|   +-- templates/accounts/          # Auth templates
|
+-- marketplace/                     # Business & job marketplace
|   +-- models.py                    # BusinessProfile, Investment, Job
|   +-- views.py                     # Browse, detail, post views
|   +-- forms.py                     # Business, opportunity forms
|   +-- templates/marketplace/       # Marketplace templates
|
+-- payments/                        # Payment processing & wallets
|   +-- models.py                    # Wallet, Transaction, Subscription
|   +-- views.py                     # Deposit, withdraw, history
|   +-- webhooks.py                  # Payment gateway webhooks
|   +-- services/                    # Business logic services
|   |   +-- stripe_service.py        # Stripe integration
|   |   +-- paypal_service.py        # PayPal integration
|   |   +-- mpesa_service.py         # M-Pesa integration
|   |   +-- wallet_service.py        # Wallet operations
|   |   +-- security_service.py      # Fraud detection
|   |   +-- analytics_service.py     # Financial analytics
|   |   +-- funds_segregation_service.py  # Bankruptcy protection
|   +-- templates/payments/          # Payment templates
|
+-- onboarding/                      # User registration & verification
|   +-- models.py                    # OnboardingProgress, EmailToken
|   +-- views.py                     # Registration flow, email verify
|   +-- middleware.py                # Onboarding enforcement
|   +-- templates/onboarding/        # Onboarding templates
|
+-- kyc/                             # Know Your Customer compliance
|   +-- models.py                    # KYCDocument, VerificationLevel
|   +-- views.py                     # Document upload, status
|   +-- services.py                  # Verification logic
|   +-- templates/kyc/               # KYC templates
|
+-- audit/                           # Audit logging & compliance
|   +-- models.py                    # AuditLog, LoginHistory
|   +-- middleware.py                # Audit trail middleware
|   +-- services.py                  # Logging services
|
+-- gdpr/                            # Data privacy & protection
|   +-- models.py                    # ConsentRecord, DataExport
|   +-- views.py                     # Consent, export, delete
|   +-- middleware.py                # GDPR enforcement
|   +-- templates/gdpr/              # Privacy templates
|
+-- monitoring/                      # System health & alerts
|   +-- services.py                  # Alert, anomaly detection
|
+-- core/                            # Core utilities
|   +-- encryption.py                # Field encryption services
|   +-- views.py                     # Landing page, general views
|
+-- templates/                       # Global templates
|   +-- base.html                    # Base template
|   +-- components/                  # Reusable components
|
+-- static/                          # Static files (CSS, JS, images)
|
+-- requirements.txt                 # Python dependencies
+-- Procfile                         # Heroku deployment
+-- runtime.txt                      # Python version
+-- manage.py                        # Django CLI
```

---

## Flow Diagrams

### A) User Onboarding & Verification Flow

```
+----------------+
| New User       |
+-------+--------+
        | 1. Register
        |    POST /register/
        v
+-------------------+
| View: register    |  <- onboarding/views.py
+-------+-----------+
        | 2. Create User
        |    Validate form, hash password
        v
+-------------------+
| User Model        |  <- accounts/models.py
| .save()           |
+-------+-----------+
        | 3. Create Onboarding
        |    Set initial progress
        v
+-------------------+
| OnboardingProgress|  <- onboarding/models.py
| .create()         |
+-------+-----------+
        | 4. Send Verification Email
        |    Generate token
        v
+-------------------+
| EmailVerification |  <- onboarding/services.py
| Token.create()    |
+-------+-----------+
        | 5. User Clicks Link
        |    GET /verify-email/<token>/
        v
+-------------------+
| View: verify_email|  <- onboarding/views.py
+-------+-----------+
        | 6. Mark Verified
        |    Update progress
        v
+-------------------+
| Select Category   |  <- accounts/views.py
| (Investor/Biz/Ind)|
+-------+-----------+
        | 7. Complete Profile
        |    Required fields
        v
+-------------------+
| Profile Complete  |
| Dashboard Access  |
+-------------------+
```

### B) Payment Deposit & Webhook Flow

```
+-------------------+
| User (Logged In)  |
+-------+-----------+
        | 1. Initiate Deposit
        |    POST /payments/deposit/
        v
+-------------------+
| View: deposit     |  <- payments/views.py
+-------+-----------+
        | 2. Create Transaction
        |    Status: pending
        v
+-------------------+
| Transaction Model |  <- payments/models.py
| .save()           |
+-------+-----------+
        | 3. Call Payment Gateway
        |    Stripe/PayPal/M-Pesa
        v
+-------------------+
| PaymentGateway    |  <- payments/services/
| Factory.create()  |
+-------+-----------+
        | 4. Process Payment
        |    External API call
        v
+--------------------+
| Payment Provider   |  (Stripe/PayPal/M-Pesa)
| (External)         |
+--------+-----------+
         | 5. Webhook Callback
         |    POST /webhooks/stripe/
         v
+-------------------+
| Webhook Handler   |  <- payments/webhooks.py
+-------+-----------+
        | 6. Verify Signature
        |    Idempotency check
        v
+-------------------+
| Atomic Transaction|  <- db_transaction.atomic()
| with Row Locking  |
+-------+-----------+
        | 7. Update Transaction
        |    Status: completed
        v
+-------------------+
| Wallet.credit()   |  <- select_for_update()
| Balance Updated   |
+-------+-----------+
        | 8. Log Activity
        |    Audit trail
        v
+-------------------+
| WalletActivityLog |  <- payments/models.py
+-------------------+
```

### C) Investment Marketplace Flow

```
+-------------------+
| Business User     |
+-------+-----------+
        | 1. Post Opportunity
        |    POST /marketplace/opportunity/post/
        v
+---------------------+
| View: post_opportunity| <- marketplace/views.py
+-------+---------------+
        | 2. Validate Form
        |    Check permissions
        v
+---------------------+
| InvestmentOpportunity|  <- marketplace/models.py
| .save()              |
+-------+--------------+
        | 3. Available to Browse
        |
        v
+-------------------+
| Investor User     |
+-------+-----------+
        | 4. Browse Opportunities
        |    GET /marketplace/opportunities/
        v
+---------------------+
| View: browse        |  <- marketplace/views.py
+-------+-------------+
        | 5. View Detail
        |    GET /marketplace/opportunity/<slug>/
        v
+---------------------+
| View: detail        |  <- marketplace/views.py
+-------+-------------+
        | 6. Save/Bookmark
        |    POST /marketplace/save/
        v
+-------------------+
| SavedItem.create()|  <- marketplace/models.py
+-------------------+
```

---

## Key Entities (Core Models)

| Entity | Purpose | App | Business Rules Owner |
|--------|---------|-----|---------------------|
| **User** | Django user account | auth | Django Auth |
| **UserProfile** | Extended user info | accounts | Model Layer |
| **Staff** | Admin/staff users | accounts | Model Layer |
| **Category** | User type (Investor/Business/Individual) | accounts | Model Layer |
| **MFADevice** | 2FA TOTP device | accounts.mfa | Service Layer |
| **Wallet** | User balance holder | payments | Service Layer |
| **Transaction** | Payment record | payments | Model Layer |
| **Invoice** | Billing document | payments | Model Layer |
| **SubscriptionPlan** | Available plans | payments | Model Layer |
| **UserSubscription** | User's active plan | payments | Service Layer |
| **WalletActivityLog** | Wallet audit trail | payments | Model Layer |
| **WalletSpendingLimit** | Transaction limits | payments | Service Layer |
| **FraudAlert** | Suspicious activity | payments | Service Layer |
| **PaymentDispute** | Contested payments | payments | Service Layer |
| **SegregatedFundsLedger** | Customer fund tracking | payments | Service Layer |
| **FundsReconciliation** | Daily balance check | payments | Service Layer |
| **BusinessProfile** | Company information | marketplace | Model Layer |
| **InvestmentOpportunity** | Investment listing | marketplace | Model Layer |
| **JobOpportunity** | Job posting | marketplace | Model Layer |
| **JobApplication** | Job application | marketplace | Model Layer |
| **SavedItem** | Bookmarked items | marketplace | Model Layer |
| **OnboardingProgress** | Registration status | onboarding | Service Layer |
| **EmailVerificationToken** | Email verify token | onboarding | Model Layer |
| **KYCDocument** | ID/document upload | kyc | Service Layer |
| **KYCVerificationLevel** | Verification tier | kyc | Service Layer |
| **AuditLog** | Immutable audit entry | audit | Model Layer |
| **LoginHistory** | Login tracking | audit | Model Layer |
| **ConsentRecord** | GDPR consent | gdpr | Model Layer |
| **DataExportRequest** | Data export request | gdpr | Service Layer |

---

## Apps / Features

### Accounts System

**Location:** `accounts/`
**Status:** Production Ready

**Key Files:**
- `models.py` - User, UserProfile, Staff, Category models
- `views.py` - Login, register, profile, settings views
- `mfa/` - Multi-factor authentication module

**Features:**
- Email/password authentication
- Social login (Google, Facebook)
- Multi-factor authentication (TOTP)
- Backup codes for MFA recovery
- User profiles with avatars
- Staff/admin roles

---

### Marketplace System

**Location:** `marketplace/`
**Status:** Production Ready

**Key Files:**
- `models.py` - BusinessProfile, InvestmentOpportunity, JobOpportunity
- `views.py` - Browse, detail, post views
- `urls.py` - URL routing

**Features:**
- Business profiles with funding stages
- Investment opportunity listings
- Job postings with applications
- Save/bookmark functionality
- Search and filtering

---

### Payment System

**Location:** `payments/`
**Status:** Production Ready

**Key Files:**
- `models.py` - Wallet, Transaction, Subscription, FraudAlert
- `views.py` - Deposit, withdraw, history, insights
- `webhooks.py` - Payment gateway webhooks
- `services/` - Payment gateway integrations

**Features:**
- Multi-gateway payments (Stripe, PayPal, M-Pesa, CashApp, Venmo)
- Wallet system with real-time balance
- Subscription management
- Transaction history with export
- Financial insights with charts
- Atomic transactions with row locking
- Idempotency checks on webhooks
- Fraud detection and alerts
- Spending limits
- Funds segregation for bankruptcy protection

---

### Onboarding System

**Location:** `onboarding/`
**Status:** Production Ready

**Key Files:**
- `models.py` - OnboardingProgress, EmailVerificationToken
- `views.py` - Registration, verification flows
- `middleware.py` - Onboarding enforcement

**Features:**
- Multi-step registration
- Email verification
- Category selection
- Profile completion enforcement
- Social auth integration

---

### KYC System

**Location:** `kyc/`
**Status:** Production Ready

**Key Files:**
- `models.py` - KYCDocument, KYCVerificationLevel
- `views.py` - Document upload, status views
- `services.py` - Verification logic

**Features:**
- Document upload (ID, passport, business docs)
- Verification levels (Basic → Premium)
- Transaction limits by level
- Document encryption
- Admin review workflow

---

### Audit System

**Location:** `audit/`
**Status:** Production Ready

**Key Files:**
- `models.py` - AuditLog, LoginHistory
- `middleware.py` - Automatic logging

**Features:**
- Immutable audit logs
- 40+ event types
- Login history with device tracking
- Risk scoring
- ISO 27001 compliant

---

### GDPR System

**Location:** `gdpr/`
**Status:** Production Ready

**Key Files:**
- `models.py` - ConsentRecord, DataExportRequest
- `views.py` - Consent, export, delete views

**Features:**
- Consent management
- Right to access (data export)
- Right to erasure (data deletion)
- Consent version tracking

---

## Feature Status Summary

| Feature | Status | Critical Issues | Notes |
|---------|--------|-----------------|-------|
| **Accounts** | Production | 0 | MFA, social auth working |
| **Marketplace** | Production | 0 | Businesses, jobs, investments |
| **Payments** | Production | 0 | 5 gateways, atomic transactions |
| **Onboarding** | Production | 0 | Email verification working |
| **KYC** | Production | 0 | Document verification |
| **Audit** | Production | 0 | Immutable logging |
| **GDPR** | Production | 0 | Consent management |

**Overall Platform Health:** 95/100

---

## Tech Stack

### Backend
- **Django 4.2+** - Web framework
- **Python 3.11** - Runtime
- **Gunicorn** - WSGI server
- **Celery 5.4** - Task queue
- **Redis 5.0** - Cache & message broker

### Database
- **PostgreSQL** - Production database
- **SQLite** - Development

### Payment Gateways
- **Stripe** - Credit/debit cards
- **PayPal** - PayPal wallet
- **M-Pesa** - Mobile money (Kenya)
- **CashApp** - Square integration
- **Venmo** - Braintree integration

### Authentication & Security
- **Django Allauth** - Email/social auth
- **Social Auth** - OAuth2 (Google, Facebook)
- **PyOTP** - TOTP-based 2FA
- **Django Axes** - Brute-force protection
- **Cryptography** - Field encryption

### Code Quality
- **pytest** - Testing framework
- **black** - Code formatting
- **flake8** - Linting
- **mypy** - Type checking
- **bandit** - Security linting

---

## Navigation Guide

### "I need to understand user authentication"
Read `accounts/views.py` and `accounts/mfa/`

### "How do payments work?"
Read `payments/views.py` and `payments/services/`

### "How are webhooks handled?"
Read `payments/webhooks.py`

### "Where is the wallet logic?"
Read `payments/services/wallet_service.py`

### "How does fraud detection work?"
Read `payments/services/security_service.py`

### "How do I add a new payment gateway?"
Read `payments/services/base.py` and follow the pattern

### "Where are the marketplace views?"
Read `marketplace/views.py`

### "How does onboarding work?"
Read `onboarding/views.py` and `onboarding/middleware.py`

### "Where is KYC verification?"
Read `kyc/models.py` and `kyc/services.py`

### "How is audit logging done?"
Read `audit/models.py` and `audit/middleware.py`

---

## Quick Start by Role

### For Investors:
1. **Register:** `/register/` - Create account
2. **Verify Email:** Check inbox, click link
3. **Select Category:** Choose "Investor"
4. **Browse Investments:** `/marketplace/opportunities/`
5. **Deposit Funds:** `/payments/deposit/`

### For Businesses:
1. **Register:** `/register/` - Create account
2. **Complete Profile:** Business details
3. **Post Opportunity:** `/marketplace/opportunity/post/`
4. **Post Jobs:** `/marketplace/job/post/`
5. **Find Investors:** `/marketplace/investors/`

### For Individuals:
1. **Register:** `/register/` - Create account
2. **Complete Profile:** Personal details
3. **Browse Jobs:** `/marketplace/jobs/`
4. **Apply:** Click "Apply" on job listing

### For Developers:
1. **Clone Repo:** `git clone <repo-url>`
2. **Create Venv:** `python -m venv venv`
3. **Activate:** `venv\Scripts\activate` (Windows)
4. **Install:** `pip install -r requirements.txt`
5. **Configure:** Copy `.env.example` to `.env`
6. **Migrate:** `python manage.py migrate`
7. **Run:** `python manage.py runserver`

---

## Environment Setup

### Prerequisites
- Python 3.11+
- PostgreSQL (production) or SQLite (development)
- Redis (for Celery)

### Installation

```bash
# Clone repository
git clone https://github.com/pmzomo/biasharaBB.git
cd biashara_bridges

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver
```

### Environment Variables

Key variables to configure in `.env`:

```
# Database
DATABASE_URL=postgres://user:pass@host:5432/dbname

# Security
SECRET_KEY=your-secret-key
DEBUG=False

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=app-password

# Payment Gateways
STRIPE_PUBLISHABLE_KEY=pk_...
STRIPE_SECRET_KEY=sk_...
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
MPESA_CONSUMER_KEY=...
MPESA_CONSUMER_SECRET=...

# Social Auth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
FACEBOOK_APP_ID=...
FACEBOOK_APP_SECRET=...

# Redis/Celery
REDIS_URL=redis://localhost:6379/0
```

---

## Deployment

### Heroku Deployment

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set SECRET_KEY=...
heroku config:set DATABASE_URL=...
# ... other variables

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser
```

### Procfile Configuration

```
web: gunicorn config.wsgi --log-file -
worker: celery -A config worker -l info
release: python manage.py migrate
```

---

## API / URL Overview

### Accounts
- `/login/` - User login
- `/register/` - User registration
- `/logout/` - User logout
- `/profile/` - User profile
- `/edit-profile/` - Edit profile
- `/mfa/setup/` - MFA setup
- `/mfa/verify/` - MFA verification

### Marketplace
- `/marketplace/businesses/` - Browse businesses
- `/marketplace/opportunities/` - Investment opportunities
- `/marketplace/jobs/` - Job listings
- `/marketplace/business/<id>/` - Business detail
- `/marketplace/opportunity/<slug>/` - Opportunity detail
- `/marketplace/job/<slug>/` - Job detail

### Payments
- `/payments/wallet/` - Wallet dashboard
- `/payments/deposit/` - Initiate deposit
- `/payments/transactions/` - Transaction history
- `/payments/transactions/export/` - Export CSV
- `/payments/insights/` - Financial insights
- `/payments/activity/` - Activity log
- `/payments/limits/` - Spending limits
- `/payments/subscriptions/` - Subscription plans

### Onboarding
- `/onboarding/` - Onboarding flow
- `/verify-email/<token>/` - Email verification

### KYC
- `/kyc/` - KYC dashboard
- `/kyc/upload/` - Document upload
- `/kyc/status/` - Verification status

### Admin
- `/admin/` - Django admin panel

---

## Testing

```bash
# Run all tests
python manage.py test

# Run with pytest
pytest

# Run with coverage
pytest --cov=.

# Run specific app tests
pytest accounts/
pytest payments/
```

---

## Support

**Issues:** https://github.com/pmzomo/biasharaBB/issues
**Email:** support@biasharabridges.com

---

**Maintained by:** Development Team
**Last Updated:** December 31, 2025
**Version:** 1.0.0
