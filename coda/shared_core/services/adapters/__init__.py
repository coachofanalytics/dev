"""
No-Op Adapters

Fallback implementations of interfaces that provide safe default behavior
when provider apps are not installed or unavailable.
"""

from shared_core.services.adapters.noop_ai_adapter import NoOpAIServiceAdapter
from shared_core.services.adapters.noop_meeting_adapter import NoOpMeetingServiceAdapter
from shared_core.services.adapters.noop_finance_task_adapter import NoOpFinanceTaskServiceAdapter

__all__ = [
    'NoOpAIServiceAdapter',
    'NoOpMeetingServiceAdapter',
    'NoOpFinanceTaskServiceAdapter',
]

