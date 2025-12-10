# Performance tests (Locust)

Run the Locust load test from the repo root (recommended inside a virtualenv):

```powershell
pip install locust
locust -f tests/payment/performance/locustfile.py --host=http://localhost:8000
```

Customize `CHECKOUT_PATH` at the top of `locustfile.py` to match your app.
