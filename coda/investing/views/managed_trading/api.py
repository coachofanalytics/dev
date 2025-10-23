"""
API Endpoints for Managed Trading

JSON API endpoints for AJAX requests and external integrations.
"""

from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from ...models import ManagedTradingAccount, OptionsPosition
from ...services import ManagedTradingService, OptionsMonitoringService


@staff_member_required
@require_http_methods(["GET"])
def account_summary_api(request, account_id):
    """
    API endpoint for account summary
    
    Returns JSON with account details, performance, and positions
    """
    account = get_object_or_404(ManagedTradingAccount, id=account_id)
    service = ManagedTradingService()
    
    summary = service.get_account_summary(account)
    
    # Convert to JSON-serializable format
    response_data = {
        'success': True,
        'account': {
            'account_number': summary['summary']['account_number'],
            'client_name': summary['summary']['client_name'],
            'status': summary['summary']['status'],
            'fee_tier': summary['summary']['fee_tier'],
        },
        'financial': {
            'current_balance': float(summary['summary']['current_balance']),
            'initial_capital': float(summary['summary']['initial_capital']),
            'total_profit_loss': float(summary['summary']['total_profit_loss']),
            'return_on_investment': float(summary['summary']['return_on_investment']),
            'available_buying_power': float(summary['summary']['available_buying_power']),
            'cash_reserved': float(summary['summary']['cash_reserved']),
            'risk_exposure': float(summary['summary']['risk_exposure']),
        },
        'performance': {
            'total_trades': summary['performance']['total_trades'],
            'winning_trades': summary['performance']['winning_trades'],
            'losing_trades': summary['performance']['losing_trades'],
            'win_rate': float(summary['performance']['win_rate']),
            'total_realized_pnl': float(summary['performance']['total_realized_pnl']),
            'total_unrealized_pnl': float(summary['performance']['total_unrealized_pnl']),
        },
        'positions': {
            'open_count': summary['positions']['open_count'],
            'closed_count': summary['positions']['closed_count'],
        },
        'fees': summary['fees']
    }
    
    return JsonResponse(response_data)


@staff_member_required
@require_http_methods(["GET"])
def position_evaluation_api(request, position_id):
    """
    API endpoint for position exit criteria evaluation
    
    Returns JSON with recommendation on whether to close position
    """
    position = get_object_or_404(OptionsPosition, id=position_id)
    service = OptionsMonitoringService()
    
    evaluation = service.evaluate_exit_criteria(position)
    
    response_data = {
        'success': True,
        'position': {
            'id': position.id,
            'symbol': position.symbol,
            'strategy': position.get_strategy_display(),
            'status': position.status,
            'unrealized_pnl': float(position.unrealized_pnl),
            'days_to_expiration': position.days_to_expiration,
        },
        'evaluation': {
            'should_close': evaluation['should_close'],
            'reason': evaluation['reason'],
            'message': evaluation['message'],
            'urgency': evaluation['urgency'],
        }
    }
    
    # Add alerts if any
    if 'alerts' in evaluation:
        response_data['alerts'] = [
            {
                'type': alert['type'],
                'severity': alert['severity'],
                'message': alert['message'],
                'recommendation': alert['recommendation']
            }
            for alert in evaluation['alerts']
        ]
    
    return JsonResponse(response_data)


@staff_member_required
@require_http_methods(["GET"])
def monitoring_summary_api(request):
    """
    API endpoint for system-wide monitoring summary
    
    Returns summary of all alerts across all accounts
    """
    service = OptionsMonitoringService()
    
    alerts_summary = service.monitor_all_accounts()
    
    response_data = {
        'success': True,
        'summary': {
            'total_accounts': alerts_summary['total_accounts'],
            'accounts_with_alerts': alerts_summary['accounts_with_alerts'],
            'critical_count': len(alerts_summary['critical']),
            'high_count': len(alerts_summary['high']),
            'medium_count': len(alerts_summary['medium']),
        },
        'critical_alerts': [
            {
                'account_number': item['account'].account_number,
                'message': item['alert']['message'],
                'type': item['alert']['type']
            }
            for item in alerts_summary['critical']
        ]
    }
    
    return JsonResponse(response_data)

