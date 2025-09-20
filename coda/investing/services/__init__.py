"""
Investing Services Package

This package contains service layer classes for the Investment & Portfolio Management bounded context.
Following the modular monolith architecture plan, these services encapsulate business logic
and provide clean interfaces for views and other components.
"""

from .investment_service import InvestmentService

__all__ = [
    'InvestmentService',
]