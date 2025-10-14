# -*- coding: utf-8 -*-
"""
Finance Legacy Views Package

Contains legacy views that are being phased out or consolidated:
- Legacy dashboard views
- Unified department views (backup versions)
- Other legacy functionality
"""

# Import legacy modules
from . import views_legacy_dashboard
from . import views_unified_department
from . import views_unified_department_backup
from . import views_unified_department_fixed

__all__ = [
    'views_legacy_dashboard',
    'views_unified_department',
    'views_unified_department_backup',
    'views_unified_department_fixed',
]



