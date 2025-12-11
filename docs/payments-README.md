# Payments README

How to run payment tests locally

1. Activate venv and install deps:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run full payment suite (sandbox keys required for integration tests):

```powershell
python scripts/run_payment_tests_with_env.py --all
```

3. Playwright (browser) tests:

```bash
./scripts/setup_playwright.sh
./scripts/run_playwright.sh
```

Notes:
- Keep sandbox keys in environment variables or CI secrets. Do NOT commit secrets.
- To enable load tests set `RUN_LOAD_TESTS=1` in environment.
