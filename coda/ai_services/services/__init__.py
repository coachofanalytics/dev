"""
AI Services Package

This package contains service layer classes for the AI & Analytics bounded context.
Following the modular monolith architecture plan, these services encapsulate business logic
and provide clean interfaces for views and other components.
"""

from .ai_analytics_service import AIAnalyticsService

__all__ = [
    'AIAnalyticsService',
]