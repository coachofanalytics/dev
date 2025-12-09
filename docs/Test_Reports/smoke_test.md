# Payments Smoke Test Report

Purpose
- Provide a compact, unambiguous smoke test plan that verifies Stripe (cards), PayPal (sandbox), and Wallet/Transaction flows work in a local developer environment.
- This file is a runnable guide — it contains the exact commands to run, the expected outcomes, and verification queries you can run against the Django DB.

Scope
- Gateways: Stripe (card payments / PaymentIntent), PayPal (redirect-based sandbox flow), Wallet (credit/debit, balance), Transaction lifecycle (pending → completed/failed), and webhook handling for Stripe/PayPal.
- Excludes: M-Pesa (not enabled in `.env`).

Prerequisites
- Project ready in a Python virtualenv; repository root is the Django project root.
- Database migrated and accessible.
- `.env` populated with the following keys (minimum):
  - `STRIPE_TEST_SECRET_KEY` (present)
  - `STRIPE_TEST_PUBLISHABLE_KEY` (required for client-side Stripe Elements)
  - `STRIPE_TEST_WEBHOOK_SECRET` (used by webhook verification; you may copy from stripe-cli)
  - `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` (sandbox)
  - `ENABLE_STRIPE=True`, `ENABLE_PAYPAL=True`, `ENABLE_WALLET_PAYMENTS=True`
- Tools: `stripe` CLI (recommended) and/or `ngrok` for exposing webhooks. `curl` and `httpie` are handy. PowerShell on Windows is used in examples.

Important files & code changes (what I added)
- `payments/context_processors.py` — exposes `STRIPE_PUBLIC_KEY` and `PAYPAL_CLIENT_ID` to templates.
- `config/settings.py` — reads test keys and picks fallbacks for `STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`, and `STRIPE_WEBHOOK_SECRET`.
- Management command: `python manage.py seed_payment_gateways` (already added) — seeds `PaymentGatewayConfig` DB rows from `.env`.

High-level smoke-test strategy
- Verify server-side capabilities against the secret keys (create PaymentIntent, check webhook handler).
- Verify client-side flows if publishable key present (Stripe Elements / confirm flow, PayPal redirect).
- Verify end-to-end behavior by observing DB state: `Transaction` status and `Wallet` balance changes.
- Where provider callbacks are required, use `stripe listen` or `ngrok` to forward events to your local `/webhooks/*` endpoints.

Smoke test checklist (pre-run)
1. Activate venv and install dependencies:
```powershell
& C:/Users/Fadhiri/Desktop/Work/BB/dev/venv/Scripts/Activate.ps1
pip install -r requirements.txt
```
2. Apply database migrations and create superuser (if not already):
```powershell
python manage.py migrate
python manage.py createsuperuser
```
3. Ensure `.env` contains the keys listed in Prerequisites.
4. Seed payment gateway configs from `.env` (so PaymentGatewayConfig rows exist):
```powershell
python manage.py seed_payment_gateways
```
5. Confirm DB entries:
```powershell
python manage.py shell
>>> from payments.models import PaymentGatewayConfig
>>> list(PaymentGatewayConfig.objects.values('name','active'))
```

Smoke tests — order and commands
Run tests in the order below. Each test case contains: Objective, Preconditions, Steps, Expected result, Verification.

1) Stripe — Server-side PaymentIntent creation (quick smoke)
- Objective: Ensure the server can create a PaymentIntent using `STRIPE_TEST_SECRET_KEY`.
- Preconditions: `STRIPE_TEST_SECRET_KEY` set in `.env` and loaded by settings.
- Steps:
  a) Start Django server:
```powershell
python manage.py runserver
```
  b) Open a Python shell and run the following snippet to create a PaymentIntent using your server-side helper or Stripe SDK (this uses stripe directly for a quick check):
```powershell
python - <<'PY'
import stripe
from decouple import config
stripe.api_key = config('STRIPE_TEST_SECRET_KEY')
pi = stripe.PaymentIntent.create(amount=5000, currency='usd', payment_method_types=['card'])
print(pi['id'], pi['status'])
PY
```
- Expected result: `pi['id']` printed and `pi['status']` is `requires_payment_method` or `requires_confirmation` depending on API parameters — creation succeeds (HTTP 200).
- Verification in app: Server-side code that calls `stripe.PaymentIntent.create(...)` should succeed. No DB side-effect unless your views create a `Transaction` — the next test covers the client + webhook flow.

2) Stripe — Client card flow + webhook (end-to-end)
- Objective: Perform a full card payment via Stripe Elements (or a Checkout Session) and ensure webhook updates `Transaction` and `Wallet`.
- Preconditions:
  - `STRIPE_TEST_PUBLISHABLE_KEY` present in `.env` (exposed to templates via the context processor).
  - `STRIPE_TEST_WEBHOOK_SECRET` present and/or `stripe listen` is running.
  - Django server running on `localhost:8000`.
- Steps:
  a) Start Stripe CLI and forward to your webhook URL (recommended):
```powershell
stripe login
stripe listen --forward-to localhost:8000/webhooks/stripe/
# Copy the `whsec_...` shown by stripe and ensure it's in .env as STRIPE_TEST_WEBHOOK_SECRET.
```
  b) Open the Stripe deposit page in the app (e.g., `/payments/deposit/stripe/` — replace with actual URL used in the project).
  c) Fill card details: `4242 4242 4242 4242`, any future expiry, `CVC 123`.
  d) Submit and wait for payment to complete.
- Expected result:
  - Browser-based payment completes (client receives confirmation) or the server redirects accordingly.
  - Stripe CLI forwards `payment_intent.succeeded` (or `checkout.session.completed`) to `/webhooks/stripe/`.
  - The `webhooks` handler verifies signature using `STRIPE_TEST_WEBHOOK_SECRET` and updates the corresponding `Transaction` to `completed` and credits `Wallet` balance.
- Verification (Django shell):
```powershell
python manage.py shell
>>> from payments.models import Transaction, Wallet
>>> tx = Transaction.objects.filter(user__email='your_test_user@example.com').order_by('-created').first()
>>> tx.status  # should be 'completed'
>>> Wallet.objects.get(user=tx.user).balance  # should reflect credited amount
```
- Common failure modes and fixes:
  - Webhook signature verification fails: ensure `STRIPE_TEST_WEBHOOK_SECRET` matches the CLI-provided value.
  - No webhook received: confirm `stripe listen` is running and forwarding to correct path, and firewall/ngrok not blocking.

3) Stripe — Simulated webhook (curl) — fast verification
- Objective: If you cannot run `stripe listen`, simulate a webhook to test your handler.
- Preconditions: You need the `STRIPE_TEST_WEBHOOK_SECRET` only for signature checking; for a quick function-level test, you may bypass signature checking (not recommended for production). Prefer using stripe-cli to generate signed events.
- Steps (using stripe-cli to trigger a sample event):
```powershell
stripe trigger payment_intent.succeeded --forward-to localhost:8000/webhooks/stripe/
```
- Expected result: Your webhook handler receives the event and marks a matching Transaction completed (if it can map by id). If your handler maps events to transactions by metadata (e.g., `metadata.transaction_id`) ensure the PaymentIntent metadata is set by your server when created.

4) PayPal — Redirect-based sandbox payment
- Objective: Verify the browser redirect flow for PayPal sandbox and server execute, then check DB updates.
- Preconditions: `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` set; `PAYPAL_MODE=sandbox`.
- Steps:
  a) Start Django server.
  b) Use the app's PayPal deposit page (e.g., `/payments/deposit/paypal/`). Initiate a deposit; you should be redirected to PayPal sandbox.
  c) Log in using PayPal sandbox buyer account (if required) and approve the payment.
  d) Return to the app's execute/return URL.
- Expected result: App receives return/execute request and finalizes payment — `Transaction` is created and eventually marked `completed` (either immediately on execute or after webhook/IPN).
- Verification (Django shell):
```powershell
python manage.py shell
>>> from payments.models import Transaction, Wallet
>>> tx = Transaction.objects.filter(user__email='your_test_user@example.com').order_by('-created').first()
>>> tx.status
>>> Wallet.objects.get(user=tx.user).balance
```
- Remarks:
  - PayPal IPN/webhooks are optional for immediate redirect flow; IPN is used for asynchronous confirmation if you rely on it. To test IPN/webhooks use ngrok or the PayPal sandbox webhook UI to configure a webhook URL pointing to your ngrok/host.

5) Wallet — Deposit using wallet, withdraw, and subscriptions
- Objective: Verify wallet credit/debit, balance reporting, and subscription payments via wallet.
- Preconditions: Wallet signals may auto-create a Wallet object for the user; ensure user exists.
- Steps:
  a) Credit wallet via Stripe/PayPal (use tests above) or create a manual credit via Django shell:
```powershell
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> from payments.models import Wallet, Transaction
>>> User = get_user_model()
>>> u = User.objects.get(email='your_test_user@example.com')
>>> w, _ = Wallet.objects.get_or_create(user=u)
>>> w.credit(100)  # if your Wallet model exposes credit() helper
```
  b) Perform a withdraw via application UI (withdraw flow) or simulate via management command / shell calling the withdraw helper.
  c) Purchase a subscription using wallet funds (if supported): run the subscription purchase page and select wallet as payment method.
- Expected result: Wallet balance decreases/increases correctly; `Transaction` rows created for each operation and statuses set correctly.
- Verification:
```powershell
python manage.py shell
>>> Wallet.objects.get(user=u).balance
>>> Transaction.objects.filter(user=u).order_by('-created')[:10].values('kind','amount','status')
```

Verification queries (common)
- Get last transaction for user:
```python
Transaction.objects.filter(user=the_user).order_by('-created').first()
```
- Wallet balance:
```python
Wallet.objects.get(user=the_user).balance
```
- PaymentGatewayConfig entries:
```python
PaymentGatewayConfig.objects.all().values('name','active','config')
```

Automated helper examples (optional)
- Use stripe-cli to trigger events (signed):
```powershell
# Trigger a PaymentIntent succeeded event (signed) and forward to your webhook
stripe trigger payment_intent.succeeded --forward-to localhost:8000/webhooks/stripe/
```
- Simulate PayPal webhook (manual curl) — PayPal requires signed notifications; best to use sandbox webhook UI or a webhook testing tool. As an alternative, test redirect/execute flow which does not require IPN for basic success.

Expected outcomes and pass criteria (smoke test)
- Each gateway smoke test is considered passed when:
  - Payment request returns success from the sandbox (or PaymentIntent is created) — server-side success.
  - Webhook (if used) is received and processed, resulting in a `Transaction` with status `completed` and the `Wallet` credited accordingly.
  - No uncaught exceptions in server logs for the tested endpoints.

Troubleshooting & common issues
- Missing publishable key: client-side Stripe will fail to initialize. Fix: add `STRIPE_TEST_PUBLISHABLE_KEY` to `.env` and restart server.
- Webhook signature errors: ensure `STRIPE_TEST_WEBHOOK_SECRET` matches the value printed by `stripe listen` or the webhook secret registered in Stripe dashboard.
- No webhook events delivered: check `stripe listen` status, ngrok forwarding, firewall, or PayPal sandbox webhook config.
- Duplicate Wallet creation: tests use `get_or_create`; in manual runs, inspect unique constraints if a Wallet is created by a signal.

Making smoke tests repeatable (recommendations)
- Use `stripe-cli` for signed webhook events in local dev — it provides realistic signed payloads.
- Add small integration scripts under `scripts/` that:
  - Create a PaymentIntent with metadata (e.g., transaction id),
  - Trigger webhook event via stripe-cli, and
  - Poll the DB for `Transaction` status change.
- Add a `smoke-tests` Makefile or an npm-style script entry to centralize commands.

CI / Automation suggestions
- Run unit tests in CI as you already do.
- Add a separate integration job that uses ephemeral public URL (ngrok or a hosted staging URL) to run the smoke tests against the sandbox keys. Steps:
  - Start server on runner (or in docker-compose),
  - Start `stripe listen` on runner or use `stripe trigger` to POST signed events to the webhook endpoint,
  - Assert DB state via Django management commands or a small verification script.

Appendix — Quick checklist you can copy
- [ ] `.env` has `STRIPE_TEST_SECRET_KEY`
- [ ] `.env` has `STRIPE_TEST_PUBLISHABLE_KEY`
- [ ] `.env` has `STRIPE_TEST_WEBHOOK_SECRET` (or you will run `stripe listen` and update it)
- [ ] `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` present and set to sandbox
- [ ] Ran `python manage.py migrate` and `python manage.py seed_payment_gateways`
- [ ] Django server running locally via `python manage.py runserver`
- [ ] `stripe listen --forward-to localhost:8000/webhooks/stripe/` running when testing Stripe webhooks
- [ ] If testing PayPal IPN/webhooks, have ngrok and a configured sandbox webhook URL


