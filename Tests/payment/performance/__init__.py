"""Performance and load/stress tests for payment gateways.

These tests are intentionally heavy and are skipped unless environment
variable `RUN_LOAD_TESTS` is set to a truthy value. For full load testing
use dedicated tools (Locust, JMeter, k6) wired to the deployed sandbox endpoints.
"""

__all__ = []
