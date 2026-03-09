"""Compatibility shim: re-export tests from the newer module so this
module's tests run as well.
"""
from .test_accounts_views import TestAccountsViews as TestAccountsViews_copy
