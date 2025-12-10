"""Minimal shim for `paypalrestsdk` used in integration tests.

This lightweight stub lets unit tests import project modules that reference
`paypalrestsdk`. It is NOT a replacement for the real SDK. Install the real
`paypalrestsdk` in CI or development environments when running integration tests.
"""

_CONFIG = {}


def configure(conf):
    _CONFIG.update(conf)


class Payment:
    def __init__(self, data):
        self.data = data
        self.id = None

    def create(self):
        # Simulate a successful creation in sandbox
        self.id = 'PAYMENT-MOCK-1'
        return True
