"""
AI Services Package

This package contains service layer classes for the AI & Analytics bounded context.
To avoid expensive import-time side effects (e.g., accessing the auth user model
before Django apps finish loading), modules are imported lazily.
"""

__all__ = ["AIAnalyticsService"]


def __getattr__(name):
    if name == "AIAnalyticsService":
        from .ai_analytics_service import AIAnalyticsService

        return AIAnalyticsService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")