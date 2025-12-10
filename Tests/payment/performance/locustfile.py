"""
Simple Locust load test for payments checkout endpoint.

Customize `CHECKOUT_PATH` to match your application routes (default is
`/payments/checkout/`). This script performs a lightweight simulated checkout
POST with a minimal payload. Replace payload values with realistic fields
according to your application API.
"""
from locust import HttpUser, task, between

CHECKOUT_PATH = '/payments/checkout/'


class PaymentUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def checkout(self):
        payload = {
            'amount': '10.00',
            'currency': 'USD',
            'payment_method': 'stripe',
        }
        self.client.post(CHECKOUT_PATH, json=payload)
