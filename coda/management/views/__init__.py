"""
Management Views Package

This package contains view modules for the management app.
Since there's both a views.py module and a views/ package, this __init__.py
re-exports everything from views.py to maintain backward compatibility.
"""

import os
# Import everything from the views.py module to maintain backward compatibility
# This allows existing imports like "from management.views import policies" to work
# We use a lazy import approach to avoid circular dependencies
import sys

# Store reference to views.py module for lazy loading
_views_module = None
_views_py_path = None


def _get_views_module():
    """Lazy load views.py module to avoid circular imports."""
    global _views_module, _views_py_path

    if _views_module is None:
        import importlib.util

        # Get the parent directory (management app directory)
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _views_py_path = os.path.join(parent_dir, "views.py")

        if os.path.exists(_views_py_path):
            spec = importlib.util.spec_from_file_location(
                "management.views_module", _views_py_path
            )
            if spec and spec.loader:
                _views_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(_views_module)

    return _views_module


# Use __getattr__ to lazily import from views.py when needed
def __getattr__(name):
    """Lazy import from views.py module."""
    views_module = _get_views_module()
    if views_module and hasattr(views_module, name):
        return getattr(views_module, name)
    raise AttributeError(f"module 'management.views' has no attribute '{name}'")


from .analytics_dashboard_views import (activity_forecast_dashboard,
                                        analytics_dashboard,
                                        anomaly_detection_dashboard,
                                        compliance_dashboard,
                                        trend_analysis_dashboard)
from .anomaly_detection_views import anomaly_detection_api
# Import Phase 1 views from submodules
from .api_views import activity_analytics_api, activity_summary_api
# Import Phase 2 views from submodules
from .budget_integration_views import (budget_activity_totals_api,
                                       budget_evidence_validation_api)
from .compliance_kpi_views import compliance_history_api, compliance_kpis_api
# Import Phase 3 views from submodules
from .forecasting_views import activity_forecast_api, budget_forecast_api
from .meeting_review_views import (approve_meeting_link,
                                   get_meeting_link_suggestions,
                                   meeting_link_review_dashboard,
                                   override_meeting_link, reject_meeting_link)
from .task_assignment_views import get_intelligent_assignment_suggestions
from .trend_analysis_views import (employee_trend_analysis_api,
                                   trend_analysis_api)

# Import Activity Catalog and Coverage views (optional - may not exist)
try:
    from .activity_catalog_views import activity_catalog_view
except ImportError:

    def activity_catalog_view(*args, **kwargs):
        from django.http import HttpResponse

        return HttpResponse("Activity catalog view not available", status=503)


try:
    from .activity_coverage_views import activity_coverage_view
except ImportError:

    def activity_coverage_view(*args, **kwargs):
        from django.http import HttpResponse

        return HttpResponse("Activity coverage view not available", status=503)


# Import DAF v2 and Approval Views from legacy_views.py
try:
    from ..legacy_views import (approve_task, daf_review_ai_generate,
                                daf_review_comment_view, daf_review_view,
                                daf_v2_view, reject_task)
except ImportError:
    # Fallback if legacy_views.py doesn't exist
    def daf_v2_view(*args, **kwargs):
        from django.http import HttpResponse

        return HttpResponse("DAF v2 view not available", status=503)

    daf_review_view = daf_v2_view
    daf_review_comment_view = daf_v2_view
    daf_review_ai_generate = daf_v2_view
    approve_task = daf_v2_view
    reject_task = daf_v2_view

# Add Phase 1, Phase 2, and Phase 3 views to exports
__all__ = [
    "BackgroundCheckListView",
    # Phase 1
    "activity_summary_api",
    "activity_analytics_api",
    "get_intelligent_assignment_suggestions",
    "meeting_link_review_dashboard",
    "approve_meeting_link",
    "override_meeting_link",
    "reject_meeting_link",
    "get_meeting_link_suggestions",
    # Phase 2
    "budget_activity_totals_api",
    "budget_evidence_validation_api",
    # Phase 3
    "activity_forecast_api",
    "budget_forecast_api",
    "trend_analysis_api",
    "employee_trend_analysis_api",
    "compliance_kpis_api",
    "compliance_history_api",
    "anomaly_detection_api",
    # Analytics Dashboard Views
    "analytics_dashboard",
    "activity_forecast_dashboard",
    "trend_analysis_dashboard",
    "compliance_dashboard",
    "anomaly_detection_dashboard",
    # Activity Catalog and Coverage Views
    "activity_catalog_view",
    "activity_coverage_view",
    # DAF v2 and Approval Views (from legacy_views.py)
    "daf_v2_view",
    "daf_review_view",
    "daf_review_comment_view",
    "daf_review_ai_generate",
    "approve_task",
    "reject_task",
]
