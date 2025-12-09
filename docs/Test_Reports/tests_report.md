# Test Report — Payments & Wallets

**Summary:**
- **Scope:** Unit tests and Django TestCase suites for payment gateways (Stripe, PayPal, M-Pesa), wallet service, and transaction model.
- **Location of tests:** `Tests/` subfolders (see below for exact files).
- **Total tests executed in this session:** 12

**Results (per suite)**
- **WalletService (Django TestCase):** `Tests.Testing_Wallet.test_wallet_service`
  - Tests found: 4
  - Ran: 4 — Result: OK
  - Duration: ~4.5s
- **Transaction model (Django TestCase):** `Tests.Testing_Transactions.test_transaction_model`
  - Tests found: 2
  - Ran: 2 — Result: OK
  - Duration: ~2.3s
- **Stripe gateway (unit tests):** `Tests.Tetsing_Stripe.test_stripe_gateway`
  - Tests found: 2
  - Ran: 2 — Result: OK
  - Duration: ~0.10s
- **PayPal gateway (unit tests):** `Tests.Testing_Paypal.test_paypal_gateway`
  - Tests found: 2
  - Ran: 2 — Result: OK
  - Duration: ~0.01s
- **M-Pesa gateway (unit tests):** `Tests/Testing_M-Pessa/test_mpesa_gateway.py`
  - Tests found: 2
  - Ran: 2 — Result: OK
  - Duration: ~0.14s

**Commands used (copy-paste)**
PowerShell (activate venv):
```powershell
& C:/Users/Fadhiri/Desktop/Work/BB/dev/venv/Scripts/Activate.ps1
```

Run individual Django test module (example):
```powershell
python manage.py test Tests.Testing_Wallet.test_wallet_service -v 2
python manage.py test Tests.Testing_Transactions.test_transaction_model -v 2
python manage.py test Tests.Tetsing_Stripe.test_stripe_gateway -v 2
python manage.py test Tests.Testing_Paypal.test_paypal_gateway -v 2
python manage.py test "Tests/Testing_M-Pessa" -v 2
```

Notes about an alternative that initially failed:
- Running `python -m unittest discover -s Tests/Tetsing_Stripe -p "test_*.py" -v` failed at import time because Django settings were not configured for plain `unittest` discovery. Use `manage.py test` for Django-aware tests, or set `DJANGO_SETTINGS_MODULE=config.settings` before running `python -m unittest`.

**Fixes & repository changes made to get tests passing**
- Added test modules:
  - `Tests/Testing_Wallet/test_wallet_service.py` — WalletService credit/debit/balance tests (Django TestCase).
  - `Tests/Testing_Transactions/test_transaction_model.py` — `Transaction` model tests for `transaction_id`, `mark_as_completed`, `mark_as_failed`.
- Created package markers to enable discovery via dotted module names:
  - `Tests/__init__.py`
  - `Tests/Testing_Wallet/__init__.py`
  - `Tests/Testing_Transactions/__init__.py`
  - `Tests/Tetsing_Stripe/__init__.py` (preserved existing folder name)
  - `Tests/Testing_Paypal/__init__.py`
  - `Tests/Testing_M-Pessa/__init__.py`
- Test robustness improvement: `Wallet` objects may be auto-created by project signals. To avoid UNIQUE constraint errors the new tests use `Wallet.objects.get_or_create(...)` in `setUp()` instead of always calling `create()`.

**Files added or modified (high level)**
- New test files:
  - `Tests/Testing_Wallet/test_wallet_service.py`
  - `Tests/Testing_Transactions/test_transaction_model.py`
- New package markers (see list above).
- Settings: `config/settings.py` updated to accept `STRIPE_TEST_*` fallbacks for local development.
- Management command: `payments/management/commands/seed_payment_gateways.py` added to create `PaymentGatewayConfig` rows from `.env`.

**Pass rates & behavior summary**
- Overall pass rate across all executed tests: **100%** (12/12).
- WalletService behaviors observed during testing:
  - Deposits (credit): passed (transaction created, wallet balance updated) — 100% success in tests.
  - Withdrawals (debit): passed (transaction created, balance decremented; insufficient-funds raises) — 100% success in tests.
  - Balance queries and sufficient-balance checks: passed — 100% success in tests.
- Transaction model behaviors observed during testing:
  - Transaction ID generation on save: passed — 100%.
  - Status transitions (`mark_as_completed`, `mark_as_failed` and metadata update): passed — 100%.
- Gateway unit tests behaviors observed (Stripe, PayPal, M-Pesa):
  - Payment processing flow: mocked success responses asserted and mapped to success — 100%.
  - Payment verification flow: mocked verification responses asserted and mapped to completed status — 100%.

These pass rates reflect the implemented automated tests that run in isolation (unit tests) and Django TestCases that exercise DB-backed models. They do not reflect external networks or live gateway behavior because external calls are mocked in gateway tests.

**Local run status — what will and won't work (and missing credentials)**

What will work locally right now (after seeding configs):
- Wallet features: wallet dashboard, deposit/withdrawal logic via wallet, balance queries, transaction history, and subscription purchases using wallet funds — all operate fully in-process and require no external credentials.
- PayPal server-side flows (sandbox): the PayPal SDK is configured from `.env` (`PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET`) and `PaymentGatewayConfig` was created; the standard redirect/execute flow for deposits should work locally because the browser-based redirect returns to your app. IPN/webhook notifications are optional for the redirect flow.
- Stripe server-side API calls: a Stripe test secret key was found in `.env` and was used to seed the DB, so server-side calls that rely only on the secret key (creating PaymentIntents, refunds, server-side verification) can be performed.

What will NOT work (or will be limited) until you provide extra values or publicly reachable endpoints:
- Stripe client-side flows (tokenization / Elements): missing publishable key — the app needs `STRIPE_PUBLIC_KEY` (or `STRIPE_TEST_PUBLISHABLE_KEY`) in env so the frontend can obtain `stripe_token`/`payment_method`. Without this, the deposit page cannot collect payment details from the browser.
- Stripe webhooks: although `STRIPE_TEST_WEBHOOK_SECRET` is present in `.env` (and seeded into settings), Stripe cannot deliver webhook events to your local server unless you expose it publicly or use the Stripe CLI to forward events. You must run `stripe listen` or use `ngrok` and register the public webhook endpoint.
- M-Pesa (STK Push) flows: incomplete credentials in `.env` (the seed command skipped M-Pesa). Missing keys include `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_SHORTCODE` (or `MPESA_BUSINESS_SHORTCODE`), `MPESA_PASSKEY`, and `MPESA_CALLBACK_URL`. Without these, the M-Pesa gateway will not initialize and M-Pesa-related deposit views will be unavailable.
- PayPal IPN/webhooks: while the redirect/execute flow will work (browser returns to your site), server-to-server IPN/webhook style notifications require public endpoints or PayPal sandbox webhook configuration pointing to a reachable URL. If you rely on IPN for async confirmation, set up a public URL or use ngrok.

Exact missing environment keys (from `config/settings.py` and what's present in `.env`):
- `STRIPE_PUBLIC_KEY` or `STRIPE_TEST_PUBLISHABLE_KEY` — not present in `.env` (required for Stripe Elements/client tokenization).
- `MPESA_CONSUMER_KEY` — missing
- `MPESA_CONSUMER_SECRET` — missing
- `MPESA_SHORTCODE` / `MPESA_BUSINESS_SHORTCODE` — missing
- `MPESA_PASSKEY` — missing
- `MPESA_CALLBACK_URL` — missing (needed for M-Pesa callbacks)

Other notes and recommendations to get everything fully functional locally:
- If you want quick Stripe webhook handling locally, install the Stripe CLI and run:
```powershell
stripe login
stripe listen --forward-to localhost:8000/webhooks/stripe/
```
Then copy the `whsec_...` webhook secret from the CLI output into your `.env` as `STRIPE_TEST_WEBHOOK_SECRET` or `STRIPE_WEBHOOK_SECRET` (we already pick up the test webhook secret when present).
- For PayPal testing, your current `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` are set to sandbox; you can use the normal PayPal redirect flow without extra tunneling. If you want IPN/webhook verification, use a public URL.
- For M-Pesa, supply the missing credentials and a callback URL that Safaricom can reach (ngrok or a hosted dev URL), then re-run `python manage.py seed_payment_gateways` to update DB config.



# Test Report — Payments & Wallets

**Summary:**
- **Scope:** Unit tests and Django TestCase suites for payment gateways (Stripe, PayPal, M-Pesa), wallet service, and transaction model.
- **Location of tests:** `Tests/` subfolders (see below for exact files).
- **Total tests executed in this session:** 12

**Results (per suite)**
- **WalletService (Django TestCase):** `Tests.Testing_Wallet.test_wallet_service`
  - Tests found: 4
  - Ran: 4 — Result: OK
  - Duration: ~4.5s
- **Transaction model (Django TestCase):** `Tests.Testing_Transactions.test_transaction_model`
  - Tests found: 2 
  - Ran: 2 — Result: OK
  - Duration: ~2.3s
- **Stripe gateway (unit tests):** `Tests.Tetsing_Stripe.test_stripe_gateway`
  - Tests found: 2
  - Ran: 2 — Result: OK
  - Duration: ~0.10s
- **PayPal gateway (unit tests):** `Tests.Testing_Paypal.test_paypal_gateway`
  - Tests found: 2
  - Ran: 2 — Result: OK
  - Duration: ~0.01s
- **M-Pesa gateway (unit tests):** `Tests/Testing_M-Pessa/test_mpesa_gateway.py`
  - Tests found: 2
  - Ran: 2 — Result: OK
  - Duration: ~0.14s

**Pass rates & behavior summary**
- Overall pass rate across all executed tests: **100%** (12/12).
- WalletService behaviors observed during testing:
  - Deposits (credit): passed (transaction created, wallet balance updated) — 100% success in tests.
  - Withdrawals (debit): passed (transaction created, balance decremented; insufficient-funds raises) — 100% success in tests.
  - Balance queries and sufficient-balance checks: passed — 100% success in tests.
- Transaction model behaviors observed during testing:
  - Transaction ID generation on save: passed — 100%.
  - Status transitions (`mark_as_completed`, `mark_as_failed` and metadata update): passed — 100%.
- Gateway unit tests behaviors observed (Stripe, PayPal, M-Pesa):
  - Payment processing flow: mocked success responses asserted and mapped to success — 100%.
  - Payment verification flow: mocked verification responses asserted and mapped to completed status — 100%.

Notes:
- These pass rates reflect the implemented automated tests that run in isolation (unit tests) and Django TestCases that exercise DB-backed models. They do not reflect external networks or live gateway behavior because external calls are mocked in gateway tests.
- If you want measured reliability against actual sandbox/live gateways, we should add integration tests that hit sandbox endpoints with test credentials (requires wiring `.env` and careful secrets management).

**Commands used (copy-paste)**
PowerShell (activate venv):
```powershell
& C:/Users/Fadhiri/Desktop/Work/BB/dev/venv/Scripts/Activate.ps1
```

Run individual Django test module (example):
```powershell
python manage.py test Tests.Testing_Wallet.test_wallet_service -v 2
python manage.py test Tests.Testing_Transactions.test_transaction_model -v 2
python manage.py test Tests.Tetsing_Stripe.test_stripe_gateway -v 2
python manage.py test Tests.Testing_Paypal.test_paypal_gateway -v 2
python manage.py test "Tests/Testing_M-Pessa" -v 2
```

Notes about an alternative that initially failed:
- Running `python -m unittest discover -s Tests/Tetsing_Stripe -p "test_*.py" -v` failed at import time because Django settings were not configured for plain `unittest` discovery. Use `manage.py test` for Django-aware tests, or set `DJANGO_SETTINGS_MODULE=config.settings` before running `python -m unittest`.

**Fixes & repository changes made to get tests passing**
- Added test modules:
  - `Tests/Testing_Wallet/test_wallet_service.py` — WalletService credit/debit/balance tests (Django TestCase).
  - `Tests/Testing_Transactions/test_transaction_model.py` — `Transaction` model tests for `transaction_id`, `mark_as_completed`, `mark_as_failed`.
- Created package markers to enable discovery via dotted module names:
  - `Tests/__init__.py`
  - `Tests/Testing_Wallet/__init__.py`
  - `Tests/Testing_Transactions/__init__.py`
  - `Tests/Tetsing_Stripe/__init__.py` (preserved existing folder name)
  - `Tests/Testing_Paypal/__init__.py`
  - `Tests/Testing_M-Pessa/__init__.py`
- Test robustness improvement: `Wallet` objects may be auto-created by project signals. To avoid UNIQUE constraint errors the new tests use `Wallet.objects.get_or_create(...)` in `setUp()` instead of always calling `create()`.

**Files added or modified (high level)**
- New test files:
  - `Tests/Testing_Wallet/test_wallet_service.py`
  - `Tests/Testing_Transactions/test_transaction_model.py`
- New package markers (see list above).

**Why those changes were necessary**
- Django projects sometimes create related objects via signals (for example, creating a `Wallet` when a `User` is created). Tests that unconditionally create the same related object (with a unique constraint) will fail on insertion; using `get_or_create` makes tests resilient to project behavior and isolates test intent.
- Using `manage.py test` ensures Django's app registry and settings are loaded, which prevents import-time errors when test modules import project models/services.

**Recommendations & next steps**
- Add CI: Create a GitHub Actions workflow to run `python manage.py test` for the repository on push/PR. I can scaffold the workflow for you.
- Extend integration tests: The gateway unit tests currently mock external SDKs/APIs and verify gateway logic. If you want to assert that high-level orchestration creates `Transaction` records, I can add small integration tests that exercise the orchestration layer (or a thin helper) linking a gateway result to `Transaction` creation.
- Normalize test folder names: consider renaming `Tetsing_Stripe` → `Testing_Stripe` and `Testing_M-Pessa` → `Testing_Mpesa` (no hyphen) for consistency.
- Consider adding a `Makefile` or npm-style `scripts` entries in repository README to standardize running tests locally.

**Where I saved this report**
- `doc/tests_report.md` — this file (inside the repository). Open it with your editor to review or commit to the repo.


