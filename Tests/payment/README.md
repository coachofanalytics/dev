Payment test suite overview
===========================

This folder contains unit, integration, E2E, performance, security and resilience
tests for payment flows (Stripe, PayPal, M-Pesa). Key files added by the test
scaffold include:

- `unit/test_card_validation.py` - pure unit tests for Luhn/CVV/expiry checks
- `integration/test_mpesa_stk_callback.py` - posts STK callback payload to webhook
- `performance/locustfile.py` - simple Locust load test scaffold

Playwright
----------
There is a Playwright scaffold under `playwright/` and a sample browser test
`playwright/tests/test_stripe_elements.spec.ts`. Install Playwright (Node) to
run these locally and CI via the included GitHub Action.
# Payment Test Suite

This folder contains a professional, modular, and CI-ready payment test suite.

- Run all tests: `python manage.py test tests.payment`
- Unit tests: fast, mocked, run in CI by default
- Integration tests: hit sandbox/test APIs; skipped unless sandbox keys set in environment
- E2E: simulate full user flows using Django TestCase and handlers
- Performance tests: heavy; skipped by default unless `RUN_LOAD_TESTS=1`
- Security tests: check configuration, sensitive-data handling, and common injection vectors

CI notes:
- Keep secrets in CI provider secrets (GH Actions/Heroku/GitLab) and do not commit `.env`.
- Enable integration tests by setting `STRIPE_TEST_SECRET_KEY`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, and `MPESA_TEST_*` as required.
