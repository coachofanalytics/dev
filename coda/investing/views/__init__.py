"""
Investing Views Package

Combines legacy views (from views_legacy.py) with new organized views.
"""

# Import all legacy views
from ..views_legacy import *

# Import managed trading views (these will be available via views.managed_trading.X pattern)
from . import managed_trading

