"""Investing services exposed via lazy imports to avoid premature model loading."""

import importlib

__all__ = [
    'InvestmentService',
    'ManagedTradingService',
    'OptionsMonitoringService',
    'ApplicationReviewService',
    'BatchApprovalService',
    'NotificationService',
    'GoToMeetingService',
    'PerformanceReportingService',
    'PositionFetcherService',
    'CapitalAllocationService',
    'UnusualWhalesService',
    'BrokerAPIService',
    'PredictiveAnalyticsService',
]

_MODULE_MAP = {
    'InvestmentService': '.investment_service',
    'ManagedTradingService': '.managed_trading_service',
    'OptionsMonitoringService': '.options_monitoring_service',
    'ApplicationReviewService': '.application_approval_service',
    'BatchApprovalService': '.batch_approval_service',
    'NotificationService': '.notification_service',
    'GoToMeetingService': '.gotomeeting_service',
    'PerformanceReportingService': '.performance_reporting_service',
    'PositionFetcherService': '.position_fetcher_service',
    'CapitalAllocationService': '.capital_allocation_service',
    'UnusualWhalesService': '.unusual_whales_service',
    'BrokerAPIService': '.broker_api_service',
    'PredictiveAnalyticsService': '.predictive_analytics_service',
}


def __getattr__(name):
    if name in _MODULE_MAP:
        module = importlib.import_module(_MODULE_MAP[name], __name__)
        attr = getattr(module, name)
        globals()[name] = attr
        return attr
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")