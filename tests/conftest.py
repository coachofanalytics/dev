import pytest
from pathlib import Path


def pytest_ignore_collect(path, config):
    """Ignore legacy unit test files that were moved into app-specific
    subpackages to avoid duplicate collection.

    This deliberately excludes files directly under `tests/unit/` that
    follow the `test_*.py` pattern, while allowing files inside
    `tests/unit/<app>/` to be collected.
    """
    p = Path(str(path))
    try:
        # Ignore files like tests/unit/test_*.py (direct children)
        if p.parent.name == 'unit' and p.parent.parent.name == 'tests' and p.name.startswith('test_') and p.suffix == '.py':
            return True
    except Exception:
        return False
    return False
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
import accounts.models as accounts_models
import audit.signals as audit_signals
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save
from django.apps import apps


# Prevent automatic profile creation during tests to avoid schema drift
User = get_user_model()
try:
    post_save.disconnect(accounts_models.create_user_profile, sender=User)
except Exception:
    pass
try:
    post_save.disconnect(accounts_models.save_user_profile, sender=User)
except Exception:
    pass

# Disconnect audit signal handlers that create audit records during user actions
try:
    post_save.disconnect(audit_signals.log_user_changes, sender=User)
except Exception:
    pass
try:
    user_logged_in.disconnect(audit_signals.log_user_login)
except Exception:
    pass
try:
    user_logged_out.disconnect(audit_signals.log_user_logout)
except Exception:
    pass
try:
    user_login_failed.disconnect(audit_signals.log_failed_login)
except Exception:
    pass

# Disconnect payments/marketplace subscription and transaction logging
try:
    Transaction = apps.get_model('payments', 'Transaction')
    post_save.disconnect(audit_signals.log_transaction_created, sender=Transaction)
except Exception:
    pass
try:
    UserSubscription = apps.get_model('payments', 'UserSubscription')
    post_save.disconnect(audit_signals.log_subscription_created, sender=UserSubscription)
except Exception:
    pass
try:
    BusinessProfile = apps.get_model('marketplace', 'BusinessProfile')
    post_save.disconnect(audit_signals.log_business_profile_changes, sender=BusinessProfile)
except Exception:
    pass
try:
    InvestmentOpportunity = apps.get_model('marketplace', 'InvestmentOpportunity')
    post_save.disconnect(audit_signals.log_investment_opportunity, sender=InvestmentOpportunity)
except Exception:
    pass
try:
    JobApplication = apps.get_model('marketplace', 'JobApplication')
    post_save.disconnect(audit_signals.log_job_application, sender=JobApplication)
except Exception:
    pass
