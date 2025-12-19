from dataclasses import dataclass, field
from typing import Iterable, List
from unittest.mock import patch

from django.conf import settings
from django.db.models import Q
from django.test import SimpleTestCase, override_settings

from coda.investing.services.notification_service import NotificationService, Group


@dataclass
class FakeUser:
    email: str
    is_active: bool = True
    is_superuser: bool = False
    is_staff: bool = False
    groups: Iterable = field(default_factory=list)


class FakeQuerySet:
    def __init__(self, users: List[FakeUser]):
        self._users = list(users)

    def _matches_kwargs(self, user: FakeUser, kwargs: dict) -> bool:
        for key, value in kwargs.items():
            if key == 'is_superuser':
                if user.is_superuser != value:
                    return False
            elif key == 'is_staff':
                if user.is_staff != value:
                    return False
            elif key == 'is_active':
                if user.is_active != value:
                    return False
            elif key == 'email__isnull':
                if (user.email is None) != value:
                    return False
            elif key == 'email':
                if user.email != value:
                    return False
            elif key == 'groups':
                if value not in getattr(user, 'groups', []):
                    return False
            else:  # pragma: no cover - helper completeness
                attr = getattr(user, key, None)
                if attr != value:
                    return False
        return True

    def _matches_q(self, user: FakeUser, expr: Q) -> bool:
        result = None
        for child in expr.children:
            if isinstance(child, Q):
                child_result = self._matches_q(user, child)
            else:
                key, value = child
                child_result = self._matches_kwargs(user, {key: value})

            if result is None:
                result = child_result
            elif expr.connector == Q.AND:
                result = result and child_result
            else:  # OR
                result = result or child_result

        if result is None:
            result = True

        if expr.negated:
            result = not result
        return result

    def filter(self, *args, **kwargs):
        filtered = self._users
        for arg in args:
            if isinstance(arg, Q):
                filtered = [u for u in filtered if self._matches_q(u, arg)]

        if kwargs:
            filtered = [u for u in filtered if self._matches_kwargs(u, kwargs)]

        return FakeQuerySet(filtered)

    def exclude(self, **kwargs):
        filtered = [u for u in self._users if not self._matches_kwargs(u, kwargs)]
        return FakeQuerySet(filtered)

    def values_list(self, field_name, flat=False):
        if field_name != 'email':  # pragma: no cover - helper completeness
            raise ValueError("This fake queryset only supports 'email' values_list")
        return [getattr(u, field_name) for u in self._users]


class FakeManager:
    def __init__(self, users: List[FakeUser]):
        self._users = users

    def filter(self, *args, **kwargs):
        return FakeQuerySet(self._users).filter(*args, **kwargs)


class NotificationServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = NotificationService()

    @patch('coda.investing.services.notification_service.Group')
    @patch('coda.investing.services.notification_service.User')
    def test_get_staff_emails_returns_superusers_only_when_group_missing(self, mock_user, mock_group):
        users = [
            FakeUser(email='super@coda.test', is_superuser=True, is_staff=True),
            FakeUser(email='staff@coda.test', is_staff=True),
            FakeUser(email='client@coda.test', is_staff=False, is_superuser=False),
        ]
        mock_user.objects = FakeManager(users)
        mock_group.DoesNotExist = Group.DoesNotExist
        mock_group.objects.get.side_effect = Group.DoesNotExist

        emails = self.service._get_staff_emails()
        self.assertEqual(emails, ['super@coda.test'])

    @patch('coda.investing.services.notification_service.Group')
    @patch('coda.investing.services.notification_service.User')
    @override_settings(MANAGED_INCOME_DIGEST_GROUP='Managed Income Digest')
    def test_get_staff_emails_includes_configured_group_members(self, mock_user, mock_group):
        fake_group = object()
        users = [
            FakeUser(email='super@coda.test', is_superuser=True, is_staff=True),
            FakeUser(email='group@coda.test', is_staff=True, groups=[fake_group]),
            FakeUser(email='other@coda.test', is_staff=True),
        ]
        mock_user.objects = FakeManager(users)
        mock_group.DoesNotExist = Group.DoesNotExist
        mock_group.objects.get.return_value = fake_group

        emails = self.service._get_staff_emails()
        self.assertEqual(emails, ['group@coda.test', 'super@coda.test'])

    @patch('coda.investing.services.notification_service.send_mail')
    def test_send_internal_allocation_digest_no_recipients_returns_false(self, mock_send_mail):
        with patch.object(self.service, '_get_staff_emails', return_value=[]):
            result = self.service.send_internal_allocation_digest({})
        self.assertFalse(result)
        mock_send_mail.assert_not_called()

    @patch('coda.investing.services.notification_service.send_mail')
    def test_send_internal_allocation_digest_sends_email(self, mock_send_mail):
        recipients = ['one@coda.test', 'two@coda.test']
        summary = {
            'allocations': [
                {'symbol': 'AAPL', 'strategy': 'bull_put_spread', 'capital_used': 5000, 'expected_income': 200, 'flow_score': 75, 'ai_score': 88, 'timing_signal': '🟢 ENTER NOW'},
            ],
            'totals': {'expected_income': 200, 'coverage_pct': 50, 'positions': 1},
            'account_capital': 30000,
            'income_target': 420,
            'meets_target': False,
            'cache_stats': {'cache_hits': 3, 'api_calls': 1, 'ttl': 3600},
        }

        with patch.object(self.service, '_get_staff_emails', return_value=recipients):
            result = self.service.send_internal_allocation_digest(summary)

        self.assertTrue(result)
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        self.assertEqual(kwargs['recipient_list'] if 'recipient_list' in kwargs else args[3], recipients)

