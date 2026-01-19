"""Compatibility shim: re-export tests from the newer module so this
module's tests run as well.
"""
from .test_accounts_models import TestAccountsModels as TestAccountsModels_copy
