"""
Managed Trading Views Subpackage
"""

# Import all managed trading view modules
from . import accounts
from . import positions
from . import monitoring
from . import sessions
from . import api
from . import client
from . import onboarding  # Phase 6: Client onboarding & compliance

__all__ = [
    'accounts',
    'positions',
    'monitoring',
    'sessions',
    'api',
    'client',
    'onboarding',
]

