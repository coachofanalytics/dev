"""
Managed account analytics views.

Provides Phase 4 predictive analytics dashboard for staff users.
"""

import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render

from ...models import ManagedTradingAccount
from ...services import PredictiveAnalyticsService

logger = logging.getLogger(__name__)


@staff_member_required
def account_analytics(request, account_id):
    """
    Display predictive analytics and historical outcomes for a managed account.
    """
    account = get_object_or_404(
        ManagedTradingAccount.objects.select_related('client', 'account_manager'),
        id=account_id
    )

    service = PredictiveAnalyticsService()
    forecast = None
    error_message = None

    try:
        forecast = service.forecast_account_balance(account)
    except ValueError as exc:
        error_message = str(exc)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Predictive analytics failed for account %s", account.account_number)
        error_message = f"Unable to generate forecast: {exc}"

    if error_message:
        messages.warning(request, error_message)

    context = {
        'account': account,
        'forecast': forecast or {},
        'uses_prophet': bool(forecast and forecast.get('uses_prophet')),
        'title': f'Predictive Analytics - {account.account_number}',
    }

    return render(request, 'investing/managed/account_analytics.html', context)

