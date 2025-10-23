"""
Options Monitoring Service
Position monitoring, alerts, and risk management

This service handles:
- Real-time position monitoring
- Alert generation
- Risk threshold checks
- Exit criteria evaluation
"""

import logging
from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Tuple
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings

from ..models import (
    ManagedTradingAccount,
    OptionsPosition,
    TradingActivity,
    RiskAlert
)
from .base_service import BaseInvestingService

logger = logging.getLogger(__name__)


class OptionsMonitoringService(BaseInvestingService):
    """
    Service for monitoring options positions and generating alerts
    
    Provides methods for:
    - Monitoring open positions
    - Evaluating exit criteria
    - Generating risk alerts
    - Checking account risk limits
    """
    
    def monitor_account(self, account: ManagedTradingAccount) -> List[Dict]:
        """
        Monitor all positions in an account
        
        Args:
            account: ManagedTradingAccount instance
        
        Returns:
            List of alerts/recommendations
        """
        alerts = []
        
        # Check if account is active
        if account.status != 'active':
            return alerts
        
        # Get open positions
        open_positions = account.positions.filter(status='open')
        
        # Monitor each position
        for position in open_positions:
            position_alerts = self.monitor_position(position)
            alerts.extend(position_alerts)
        
        # Check account-level risks
        account_alerts = self._check_account_risks(account)
        alerts.extend(account_alerts)
        
        # Save critical alerts
        for alert in alerts:
            if alert['severity'] == 'critical':
                self._create_alert(account, alert)
        
        return alerts
    
    def monitor_position(self, position: OptionsPosition) -> List[Dict]:
        """
        Monitor individual position for exit criteria
        
        Args:
            position: OptionsPosition instance
        
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        # Check profit target (50% of max profit)
        if position.unrealized_pnl > 0:
            profit_pct = (position.unrealized_pnl / position.max_profit) * 100 if position.max_profit > 0 else 0
            
            if profit_pct >= 50:
                alerts.append({
                    'type': 'profit_target',
                    'severity': 'high',
                    'position': position,
                    'message': f'{position.symbol}: Profit target reached ({profit_pct:.1f}% of max profit)',
                    'recommendation': 'Close position to lock in profit',
                    'action_required': True
                })
        
        # Check stop loss (200% of premium collected)
        if position.unrealized_pnl < 0:
            loss_amount = abs(position.unrealized_pnl)
            stop_loss_threshold = position.premium_collected * Decimal('2.00')
            
            if loss_amount >= stop_loss_threshold:
                alerts.append({
                    'type': 'stop_loss',
                    'severity': 'critical',
                    'position': position,
                    'message': f'{position.symbol}: STOP LOSS HIT - Loss ${loss_amount:,.2f}',
                    'recommendation': 'CLOSE IMMEDIATELY to prevent further losses',
                    'action_required': True
                })
        
        # Check days to expiration
        dte = position.days_to_expiration
        if dte <= 5 and dte >= 0:
            alerts.append({
                'type': 'expiration',
                'severity': 'high' if dte <= 3 else 'medium',
                'position': position,
                'message': f'{position.symbol}: {dte} days to expiration',
                'recommendation': 'Consider closing to avoid gamma risk',
                'action_required': dte <= 3
            })
        
        # Check delta shift (if delta > 0.50 or < -0.50)
        if abs(position.position_delta) > Decimal('0.50'):
            alerts.append({
                'type': 'delta_shift',
                'severity': 'medium',
                'position': position,
                'message': f'{position.symbol}: Delta shifted to {position.position_delta:.2f}',
                'recommendation': 'Review position - may be moving ITM',
                'action_required': False
            })
        
        return alerts
    
    def _check_account_risks(self, account: ManagedTradingAccount) -> List[Dict]:
        """Check account-level risk thresholds"""
        alerts = []
        
        # Check total risk exposure
        if account.current_risk_exposure > account.max_total_risk:
            alerts.append({
                'type': 'risk_exposure',
                'severity': 'critical',
                'position': None,
                'message': f'Account risk exposure ({account.current_risk_exposure:.1f}%) exceeds limit ({account.max_total_risk:.1f}%)',
                'recommendation': 'Close positions to reduce risk exposure',
                'action_required': True
            })
        
        # Check daily loss (if we had daily tracking)
        # This would require additional tracking of daily P&L changes
        
        # Check available buying power
        if account.available_buying_power < Decimal('1000.00'):
            alerts.append({
                'type': 'low_buying_power',
                'severity': 'medium',
                'position': None,
                'message': f'Low buying power: ${account.available_buying_power:,.2f}',
                'recommendation': 'Close positions to free up capital',
                'action_required': False
            })
        
        return alerts
    
    def _create_alert(self, account: ManagedTradingAccount, alert_data: Dict):
        """Create and save risk alert"""
        try:
            # Use RiskAlert model if it exists, otherwise log to activity
            try:
                RiskAlert.objects.create(
                    managed_account=account,
                    alert_type=alert_data['type'],
                    severity=alert_data['severity'],
                    message=alert_data['message'],
                    recommendation=alert_data['recommendation'],
                    is_resolved=False
                )
            except:
                # Fallback to trading activity
                TradingActivity.objects.create(
                    managed_account=account,
                    position=alert_data.get('position'),
                    activity_type='alert_generated',
                    description=f"[{alert_data['severity'].upper()}] {alert_data['message']}",
                    data_snapshot=alert_data
                )
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    def evaluate_exit_criteria(self, position: OptionsPosition) -> Dict:
        """
        Evaluate if position should be closed
        
        Args:
            position: OptionsPosition instance
        
        Returns:
            Dict with recommendation
        """
        alerts = self.monitor_position(position)
        
        # Check for critical alerts
        critical_alerts = [a for a in alerts if a['severity'] == 'critical']
        if critical_alerts:
            return {
                'should_close': True,
                'reason': critical_alerts[0]['type'],
                'message': critical_alerts[0]['message'],
                'urgency': 'immediate'
            }
        
        # Check for high priority alerts
        high_alerts = [a for a in alerts if a['severity'] == 'high' and a['action_required']]
        if high_alerts:
            return {
                'should_close': True,
                'reason': high_alerts[0]['type'],
                'message': high_alerts[0]['message'],
                'urgency': 'high'
            }
        
        # No immediate action required
        return {
            'should_close': False,
            'reason': None,
            'message': 'Position within acceptable parameters',
            'urgency': 'none',
            'alerts': alerts
        }
    
    def send_alert_notification(
        self,
        account: ManagedTradingAccount,
        alerts: List[Dict]
    ):
        """
        Send alert notifications to account manager and client
        
        Args:
            account: ManagedTradingAccount instance
            alerts: List of alert dictionaries
        """
        if not alerts:
            return
        
        # Filter critical and high severity alerts
        important_alerts = [
            a for a in alerts 
            if a['severity'] in ['critical', 'high']
        ]
        
        if not important_alerts:
            return
        
        # Prepare email
        subject = f"[ALERT] Trading Alerts for Account {account.account_number}"
        
        message_lines = [
            f"Account: {account.account_number}",
            f"Client: {account.client.get_full_name()}",
            f"",
            "The following alerts require attention:",
            ""
        ]
        
        for alert in important_alerts:
            severity_marker = "🚨" if alert['severity'] == 'critical' else "⚠️"
            message_lines.append(f"{severity_marker} {alert['message']}")
            message_lines.append(f"   Recommendation: {alert['recommendation']}")
            message_lines.append("")
        
        message = "\n".join(message_lines)
        
        # Send to account manager
        if account.account_manager and account.account_manager.email:
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[account.account_manager.email],
                    fail_silently=True
                )
                logger.info(f"Alert email sent to {account.account_manager.email}")
            except Exception as e:
                logger.error(f"Error sending alert email: {e}")
    
    def get_positions_requiring_action(
        self,
        account: ManagedTradingAccount
    ) -> List[Dict]:
        """
        Get list of positions that require immediate action
        
        Args:
            account: ManagedTradingAccount instance
        
        Returns:
            List of position dictionaries with action details
        """
        open_positions = account.positions.filter(status='open')
        action_required = []
        
        for position in open_positions:
            evaluation = self.evaluate_exit_criteria(position)
            
            if evaluation['should_close'] and evaluation['urgency'] in ['immediate', 'high']:
                action_required.append({
                    'position': position,
                    'evaluation': evaluation,
                    'symbol': position.symbol,
                    'strategy': position.get_strategy_display(),
                    'unrealized_pnl': position.unrealized_pnl,
                    'days_to_expiration': position.days_to_expiration
                })
        
        # Sort by urgency (immediate first)
        action_required.sort(
            key=lambda x: 0 if x['evaluation']['urgency'] == 'immediate' else 1
        )
        
        return action_required
    
    def monitor_all_accounts(self) -> Dict:
        """
        Monitor all active managed trading accounts
        
        Returns:
            Dict with summary of all alerts
        """
        active_accounts = ManagedTradingAccount.objects.filter(
            status='active',
            trading_enabled=True
        )
        
        all_alerts = {
            'critical': [],
            'high': [],
            'medium': [],
            'total_accounts': active_accounts.count(),
            'accounts_with_alerts': 0
        }
        
        for account in active_accounts:
            alerts = self.monitor_account(account)
            
            if alerts:
                all_alerts['accounts_with_alerts'] += 1
                
                for alert in alerts:
                    severity = alert['severity']
                    if severity in all_alerts:
                        all_alerts[severity].append({
                            'account': account,
                            'alert': alert
                        })
                
                # Send notifications for important alerts
                self.send_alert_notification(account, alerts)
        
        logger.info(
            f"Monitored {active_accounts.count()} accounts, "
            f"found {len(all_alerts['critical'])} critical alerts"
        )
        
        return all_alerts

