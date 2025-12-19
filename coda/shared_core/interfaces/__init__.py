"""
Shared Core Interfaces

Abstract interfaces (ports) that define contracts for cross-app communication.
These interfaces live in shared_core to avoid circular dependencies.
"""

from shared_core.interfaces.ai_service import AIServiceInterface
from shared_core.interfaces.meeting_service import MeetingServiceInterface
from shared_core.interfaces.finance_task_service import FinanceTaskServiceInterface

__all__ = [
    'AIServiceInterface',
    'MeetingServiceInterface',
    'FinanceTaskServiceInterface',
]

