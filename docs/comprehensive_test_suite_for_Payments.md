# Comprehensive Test Suite — Payments

Version: 2025-12-10
Author: Ndegeya Fadhiri
Target audience: Senior Engineer, QA Lead, CTO, Auditor (ISO/SOC2/PCI-DSS)

Purpose: This document is the authoritative, auditor-ready test report for the `payments` test suite in the Biashara Bridges codebase. It summarizes the testing architecture, environment, execution, detailed results, risk assessment, and remediation recommendations.

Contents
1. Executive summary
2. Full project testing architecture
3. Test environment overview
4. Focused project tree (relevant folders)
5. Types of tests and coverage explanation
6. Commands to run each test type
7. Deep explanation of `scripts/run_payment_tests_with_env.py`
8. Results (detailed, per-file)
9. Risk assessment & test gaps
10. Recommendations & best practices
11. Appendices: `.env` example and troubleshooting

---

## Test environment and configuration

- OS: Windows (as used by the run)
- Python: project `venv` (local virtual environment in repo root)
- Django: project settings loaded via `DJANGO_SETTINGS_MODULE=config.settings` by the runner script
- Environment variables: `.env` loaded by `scripts/run_payment_tests_with_env.py` (in-memory only — not committed)
- External services accessed: Stripe and PayPal sandbox endpoints for integration tests (the tests use sandbox/test keys from `.env` and avoid permanent side-effects by cancelling created intents where applicable)
- Browser tests: Playwright installed and browsers downloaded with `npx playwright install` (Chromium, Firefox, WebKit installed)

Security note: Integration tests that call external sandbox endpoints require valid sandbox credentials. The runner reads `.env` but does not commit or leak values; ensure your `.env` is not stored in version control.

---

## Test inventory (what was added / tested)

New and run test files (path → short description):

- `tests/payment/e2e/test_checkout_flow.py` — Model-level E2E: deposit flows using Stripe and M-Pesa (2 tests)
- `tests/payment/integration/test_mpesa_stk_callback.py` — Posts a sample STK callback payload to `mpesa_webhook` and asserts handler invocation (1 test)
- `tests/payment/integration/test_paypal_integration.py` — PayPal sandbox create-payment integration smoke (1 test)
- `tests/payment/integration/test_stripe_integration.py` — Stripe PaymentIntent create + cancel (1 test)
- `tests/payment/lifecycle/test_refunds_and_chargebacks.py` — Refund lifecycle tests for PayPal and Stripe (2 tests)
- `tests/payment/performance/test_concurrent_payments.py` — Thread-based concurrency smoke (skipped by default) (1 test, skipped)
- `tests/payment/resilience/test_gateway_failures.py` — Gateway failure mode tests (2 tests)
- `tests/payment/security/test_sensitive_data_handling.py` — Ensures no PAN leakage and resilient PayPal IPN network handling (2 tests)
- `tests/payment/unit/test_card_validation.py` — Pure unit tests for Luhn/CVV/expiry (4 tests)
- `tests/payment/unit/test_forms_validation.py` — Deposit and M-Pesa phone form validations (4 tests)
- `tests/payment/unit/test_webhook_handlers.py` — Unit tests for webhook handler logic (6 tests)
- `tests/payment/ux/test_forms_rendering.py` — Template/form rendering smoke checks (2 tests)

# Comprehensive Test Suite — Payments

Version: 2025-12-10
Author: Test Automation & QA (repo tooling)
Target audience: Senior Engineer, QA Lead, CTO, Auditor (ISO/SOC2/PCI-DSS)

Purpose
-------
This document is an auditor-grade, enterprise-level test report for the `payments` test suite in the Biashara Bridges repository. It documents test architecture, environment, execution details, results, risk assessment, and prescriptive remediation recommendations to reach production-grade testing maturity.

Scope
-----
- Tests covered: unit, integration (sandbox), model-level E2E, browser smoke (Playwright), resilience/security checks, performance scaffolds (Locust).
- Focus: payments-related code under `payments/` and `tests/payment/` including webhook handlers, gateway integrations (Stripe, PayPal, M-Pesa), refund flows, and UX rendering.

Audience note: This report excludes unrelated functional areas and focuses strictly on testing and testability of payment components.

1. Executive summary
--------------------

- Run summary: 12 test files executed, 28 tests run, 1 test skipped (performance guard), 27 passed, 0 failed.
- Environment: tests executed in repository-local `venv`; external sandbox credentials loaded from a local `.env` file (in-memory only).
- Primary test orchestration: `scripts/run_payment_tests_with_env.py` — this runner executed each `test_*.py` file in isolation, creating and tearing down a Django test DB per file for deterministic behavior.
- Playwright: browser smoke test passed after installing browser binaries via `npx playwright install`.
- Locust: load-test scaffold included; not executed as part of normal functional runs.

Top-level recommendations (executive)
- Add automated code coverage reporting (coverage.py → CI), enforce minimum threshold (e.g., 80%) for `payments`.
- Add CI jobs that separate fast unit tests (PR gates) from longer-running integration and E2E jobs.
- Expand E2E Playwright flows to cover payment tokenization and server-side settlement (or mock tokenization to reduce scope of PCI exposure in test runs).

2. Full project testing architecture
----------------------------------

Architecture diagram (textual)

```
Developer/CI
  ├─> venv (python deps)
  ├─> scripts/run_payment_tests_with_env.py  -- per-file, isolated Django DB runs
  ├─> tests/payment/* (unit/integration/e2e/resilience/security/ux)
  ├─> playwright/* (browser smoke / E2E)
  └─> tests/payment/performance/locustfile.py  -- load tests (run against staging)

External services: Stripe sandbox, PayPal sandbox, M-Pesa sandbox/simulator
```

Components
- Django core: `config/` (settings, wsgi, asgi)
- Payments app: `payments/` (models, webhooks.py, forms, views, signals)
- Test runner scripts: `scripts/run_payment_tests_with_env.py`, `scripts/run_single_django_test.py`
- Test suites: `tests/payment/{unit,integration,e2e,performance,resilience,security,ux}`
- Browser tests: `playwright/` (Node-based Playwright harness)
- Load tests: `tests/payment/performance/locustfile.py`

Dependency structure
- Python packages (examples): Django, stripe, paypalrestsdk, requests, locust (dev), coverage (dev)
- Node: `@playwright/test` (dev)
- Secrets: Sandbox credentials are provided through `.env` or CI secret store.

3. Test environment overview
----------------------------

Platform & runtime
- OS: Windows (test runs executed on Windows during this audit)
- Python: 3.11 (recommendation: use the project's virtualenv; confirm exact version with `python --version` inside `venv`)
- Django: the project version is pinned in `requirements.txt` — verify in your environment using `pip show Django` or `pip freeze`.

Virtual environment
- Use repository-local `venv` to ensure tests use project-approved dependency versions.

Installed dependencies (representative)
- `pip install -r requirements.txt` installs server and test SDKs (Stripe, PayPal SDK). For load testing and coverage: `locust`, `coverage`.
- Playwright: install Node deps via `npm install` in `playwright/` and browser binaries via `npx playwright install`.

External services & credentials
- Stripe sandbox: `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET` (sandbox keys only)
- PayPal sandbox: `PAYPAL_CLIENT_ID`, `PAYPAL_SECRET`
- M-Pesa sandbox: API key or callback simulator credentials if applicable
- Credentials must be stored in CI secret stores and not in VCS. The runner loads `.env` into memory only.

Database strategy
- Test DB(s): Django test runner creates ephemeral test databases for each test file run. The runner tears down DBs after each file to ensure isolation.
- Dev DB: do not run tests against the development database.

4. Complete project tree (relevant folders)
-----------------------------------------

Only the parts relevant to testing are shown:

```
config/
payments/
scripts/
  ├─ run_payment_tests_with_env.py
  └─ run_single_django_test.py
tests/
  └─ payment/
     ├─ unit/
     ├─ integration/
     ├─ e2e/
     ├─ performance/
     ├─ resilience/
     ├─ lifecycle/
     ├─ security/
     └─ ux/
playwright/
  ├─ package.json
  ├─ playwright.config.ts
  └─ tests/
```

Where to find the key test runners
- `scripts/run_payment_tests_with_env.py` — recommended orchestrator for deterministic runs.
- `playwright/` — browser tests and CI workflow for E2E.
- `tests/payment/performance/locustfile.py` — Locust load script.

5. Types of tests & coverage explanation
--------------------------------------

Unit tests
- Purpose: exercise pure logic (validation, helpers, small handler functions) without network or DB dependencies where possible. Example: `tests/payment/unit/test_card_validation.py`.

Integration tests
- Purpose: verify interactions with the Django ORM and external sandbox endpoints. These may perform limited network calls to sandbox services and clean up after themselves. Example: `tests/payment/integration/test_stripe_integration.py`.

End-to-end (E2E) browser tests
- Purpose: verify UI surfaces and client-side integration points. Current scaffold verifies page load and content; extend to checkout flows and tokenization.

Performance/load tests
- Purpose: simulate concurrent users or high request volumes. Locust script is provided for dedicated performance environments.

Resilience & security tests
- Purpose: verify handling of gateway timeouts, malformed responses, and ensure sensitive data (PAN) is never persisted. Example: `tests/payment/resilience/` and `tests/payment/security/`.

UX/template rendering
- Purpose: lightweight checks that templates render expected controls and help text.

Coverage guidance
- Unit coverage goal: 80%+ for payments business logic.
- Integration: focused smoke tests to validate major external interactions.
- E2E: selective flows covering critical user paths.

6. Commands to run each test type (operational)
---------------------------------------------

Prerequisites
- Activate `venv` (PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run full test suite (per-file isolated runner)

```powershell
python scripts/run_payment_tests_with_env.py --all
```

Run only unit tests (fast)

```powershell
python -m unittest discover -s tests/payment/unit -p "test_*.py"
```

Run a single test file (example)

```powershell
python scripts/run_payment_tests_with_env.py tests/payment/integration/test_stripe_integration.py
```

Run Playwright browser tests

```powershell
cd playwright
npm install
npx playwright install
npx playwright test --config=playwright.config.ts
```

Run Locust (performance) against a staging host

```powershell
pip install locust
locust -f tests/payment/performance/locustfile.py --host=http://staging.example.com
```

Enable guarded load tests
- Some performance/concurrency tests are intentionally skipped by default. To enable them set `RUN_LOAD_TESTS=1` in the environment for the runner.

7. Deep explanation: `scripts/run_payment_tests_with_env.py`
-------------------------------------------------------

Why it exists
- Historical test discovery and import issues across environments necessitated a robust runner that:
  - Loads sandbox credentials in-memory
  - Avoids global package import failures by injecting minimal `tests` package metadata
  - Ensures per-file database isolation for deterministic results

How it works (step-by-step)
1. Loads `.env` from the project root (simple KEY=VALUE parser). Values are set in `os.environ` only when not already present.
2. Ensures project root is on `sys.path` so test helpers are importable.
3. Creates minimal `tests` and `tests.payment` module entries in `sys.modules` (with `__path__` pointing to `tests/`) if they are not already importable.
4. Calls `django.setup()` after setting `DJANGO_SETTINGS_MODULE=config.settings`.
5. Discovers `test_*.py` files under `tests/payment` and for each file:
   - Instantiates Django `DiscoverRunner`, calls `setup_test_environment()` and `setup_databases()`.
   - Loads the module from the file path using `importlib` and collects tests with `unittest.TestLoader`.
   - Runs the collected tests using `unittest.TextTestRunner`.
   - Tears down the test DB and test environment.

Isolation model and rationale
- Each file gets a fresh test database and environment, which prevents cross-file contamination and flaky tests due to shared state. This trade-off increases runtime but drastically reduces nondeterministic failures and makes failures easier to debug.

Import resolution details
- Some tests import `tests.payment.helpers` using package-style imports. When executing modules by file path, Python's import machinery may not find `tests` on `sys.path`. The runner injects lightweight `tests` / `tests.payment` package modules into `sys.modules` and sets their `__path__` to the relevant directories so those imports succeed when the file module executes.

.env handling
- The runner reads `.env` into `os.environ` (does not write to disk) and preserves existing env vars if set. This avoids accidental override of developer or CI-level variables.

When to use the runner vs `manage.py test`
- Use the runner for deterministic per-file runs and for CI where sandbox credentials are required. `manage.py test` is acceptable when the tests are fully importable and a single test DB run is desired.

8. Complete results section (full detail)
-------------------------------------

Top-level summary (executed run)

- Files executed: 12
- Tests executed: 28
- Skipped: 1 (performance guard)
- Passed: 27
- Failed: 0

Per-file results (detailed)

| File | Tests | Result | Key assertions |
|---|---:|---:|---|
| `tests/payment/e2e/test_checkout_flow.py` | 2 | PASS | Deposit flows for Stripe & M-Pesa executed at model level |
| `tests/payment/integration/test_mpesa_stk_callback.py` | 1 | PASS | STK JSON parsed; `handle_mpesa_payment_success` called with expected args |
| `tests/payment/integration/test_paypal_integration.py` | 1 | PASS | PayPal create payment flow used sandbox endpoints |
| `tests/payment/integration/test_stripe_integration.py` | 1 | PASS | Created PaymentIntent, then cancelled (confirmed sandbox interaction) |
| `tests/payment/lifecycle/test_refunds_and_chargebacks.py` | 2 | PASS | Refund transactions created and wallet credited accordingly |
| `tests/payment/performance/test_concurrent_payments.py` | 1 | SKIPPED | Guarded; set `RUN_LOAD_TESTS=1` to enable |
| `tests/payment/resilience/test_gateway_failures.py` | 2 | PASS | Simulated timeouts and incorrect responses handled gracefully |
| `tests/payment/security/test_sensitive_data_handling.py` | 2 | PASS | No PAN persisted; PayPal IPN retries/network failure handled |
| `tests/payment/unit/test_card_validation.py` | 4 | PASS | Luhn/CVV/expiry validation unit tests |
| `tests/payment/unit/test_forms_validation.py` | 4 | PASS | Deposit form bounds and MPesa phone validation |
| `tests/payment/unit/test_webhook_handlers.py` | 6 | PASS | Webhook handlers mark transactions correctly and update metadata |
| `tests/payment/ux/test_forms_rendering.py` | 2 | PASS | Forms render expected labels and help texts |

Artifacts and logs
- The runner outputs test logs to stdout. Integration tests also emit sanitized HTTP request logs when contacting sandbox APIs (useful for auditing network behavior).
- Playwright generated test artifacts (results, traces, screenshots) if configured — check `playwright/test-results/` when running locally.

Skipped tests explanation
- `performance/test_concurrent_payments.py` is intentionally skipped by default to avoid accidental load tests. Set `RUN_LOAD_TESTS=1` to run it.

External API behaviour and cleanup
- Stripe flows create PaymentIntents in sandbox and cancel them in the test where applicable to avoid persistent test artifacts. PayPal flows are limited to sandbox interactions. M-Pesa tests post synthetic callbacks rather than contacting remote M-Pesa APIs.

9. Risk assessment & test gaps
------------------------------

Covered confidence areas
- Core validation logic (card/CVV/expiry) — high confidence (unit tests).
- Webhook parsing and handler invocation — verified for M-Pesa, Stripe, PayPal pathways.
- Integration smoke-level verification for Stripe and PayPal.
- Resilience to malformed gateway responses and network errors.

Gaps & limitations
- UI-level tokenization and full browser-driven checkout flows are not yet covered (Playwright scaffold is present but needs targeted flows to exercise Stripe Elements and PayPal redirects).
- M-Pesa end-to-end DB-backed flow (create transaction → post callback → assert DB state) is currently a recommended enhancement.
- No automated coverage threshold enforcement or coverage reporting configured in CI.
- Locust performance testing not run against dedicated staging environment during this audit.

Risk priority and mitigation
- Medium risk: lack of full E2E tokenization coverage could allow client-side integration regressions to slip through. Mitigation: expand Playwright tests with network request mocks and controlled tokenization simulation.
- Low risk: sandbox-only integration tests are safe but do not prove production behaviour; plan a production smoke plan with careful approvals and isolated accounts before any live-run.

10. Recommendations & best practices
----------------------------------

Immediate (0–2 weeks)
- Add coverage.py and publish coverage reports on CI. Set an initial payments coverage gate (e.g., 70–80%).
- Add CI job matrix:
  - `unit-tests` (fast, on PR)
  - `integration-sandbox` (runs on merge or nightly)
  - `e2e-browser` (runs on merge/nightly; uses Playwright)

Short-term (2–8 weeks)
- Expand Playwright tests to include:
  - Checkout page navigation
  - Stripe Elements presence and simulated tokenization (mock network tokenization or use test hooks)
  - PayPal redirect and return flow using sandbox
- Implement DB-backed M-Pesa end-to-end test that creates a Transaction and posts a real-looking callback to `payments.webhooks.mpesa_webhook` and asserts DB state transitions.

Medium-term (2–6 months)
- Introduce contract tests for gateway integrations (pact-like or recorded VCR fixtures) to reduce reliance on live sandbox for every run.
- Add performance pipelines using Locust against a staging environment with results retention and graphing.

Security & compliance suggestions
- Ensure no test logs or test fixtures include full PANs. Use tokenized card numbers or test numbers only.
- Store sandbox credentials in a secrets manager (GitHub Actions Secrets, Azure Key Vault, etc.) and inject at runtime.

11. Appendices
-------------

A. Safe `.env` example (sandbox only)

```
# Stripe sandbox
STRIPE_API_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# PayPal sandbox
PAYPAL_CLIENT_ID=AbcTestClientId
PAYPAL_SECRET=TestSecret

# M-Pesa sandbox simulator
MPESA_API_KEY=test_mpesa_key

# Optional: enable load tests
# RUN_LOAD_TESTS=1
```

B. Troubleshooting

Playwright common problems
- "Executable doesn't exist" → run `npx playwright install` to download browser binaries.
- Page not reachable → ensure the site under test is running and accessible on the expected host/port.

Django test problems
- "settings are not configured" or `ImproperlyConfigured` → set `DJANGO_SETTINGS_MODULE=config.settings` and use the runner which calls `django.setup()`.
- ImportError: No module named `tests` → ensure `tests/__init__.py` exists or use the runner which injects a synthetic `tests` package.

C. Run commands quick reference

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Install Python deps
pip install -r requirements.txt

# Run full payment suite (recommended)
python scripts/run_payment_tests_with_env.py --all

# Run a single file
python scripts/run_payment_tests_with_env.py tests/payment/integration/test_stripe_integration.py

# Playwright
cd playwright
npm install
npx playwright install
npx playwright test --config=playwright.config.ts

# Locust (staging)
pip install locust
locust -f tests/payment/performance/locustfile.py --host=http://staging.example.com
```


