# Payments Runbook

This runbook provides emergency and routine steps for payments operations, smoke tests, and key rotation.

1) Emergency steps for failed transactions
- Check system alerts and recent logs (use `payments` logger). Look for `REDACTED` placeholders in logs.
- Reconcile: Run `python manage.py dbshell` or use admin to inspect `payments_transaction` entries.
- If a transaction is pending and payment gateway shows success, mark transaction as completed via admin or run a management command (not included) to replay webhook processing using recorded payload.
- If a transaction is charged twice, follow refund procedure documented below and open a support ticket with gateway provider.

2) How to perform a safe production smoke test
- Only run smoke tests with sandbox/test credentials or on a dedicated production test account.
- Steps:
  - Obtain rotation-approved test API keys and set them in host environment temporarily.
  - Run quick smoke: `python scripts/run_payment_tests_with_env.py tests/payment/integration/test_stripe_integration.py`
  - Verify created PaymentIntent on gateway dashboard and confirm cancellation occurred.

3) How to revoke or rotate gateway keys
- Rotate secret in gateway dashboard (Stripe/PayPal/MPesa).
- Update secrets in CI (GitHub Actions Secrets).
- Update `.env` on any staging servers.
- Restart services that cache keys.

4) Contact & escalation
- Primary: payments@company.example
- Secondary: infra@company.example
- Pager: on-call engineer via PagerDuty

5) Useful commands
- Run full payment suite locally (sanbox credentials required):

```powershell
python scripts/run_payment_tests_with_env.py --all
```

- Run Playwright smoke (local server must be running on port 8000):

```bash
./scripts/setup_playwright.sh
./scripts/run_playwright.sh
```
