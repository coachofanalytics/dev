"""
Finance Analytics Package
Provides specialized analytics services that work with our service layer architecture
"""

from .loan_performance import LoanPerformanceAnalytics
from .kcc_optimization import KCCOptimizationAnalytics
from .dashboard import AnalyticsDashboard

def get_all_analytics_services():
    """
    Service factory - provides access to all analytics services
    Returns a dictionary of analytics services
    """
    return {
        'loan_analytics': LoanPerformanceAnalytics(),
        'kcc_analytics': KCCOptimizationAnalytics(),
        'dashboard': AnalyticsDashboard(),
    }

__all__ = [
    'LoanPerformanceAnalytics',
    'KCCOptimizationAnalytics', 
    'AnalyticsDashboard',
    'get_all_analytics_services'
] 