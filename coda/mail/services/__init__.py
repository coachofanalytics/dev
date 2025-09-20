"""
Mail Services Package

Centralized email services for the CODA application.
All email functionality is consolidated here to eliminate duplication.
"""

from .email_service import EmailService

__all__ = [
    'EmailService'
]


