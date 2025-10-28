"""
Performance Reporting Service
Generate monthly/quarterly performance reports for clients
"""

import logging
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from datetime import date, timedelta
from django.core.mail import send_mail, EmailMessage
from django.conf import settings

from ..models import OptionsPosition, ManagedTradingAccount, TradingActivity

logger = logging.getLogger(__name__)


class PerformanceReportingService:
    """
    Service for generating and distributing performance reports
    """
    
    def generate_monthly_report(self, managed_account, month=None, year=None):
        """
        Generate comprehensive monthly performance report
        
        Args:
            managed_account: ManagedTradingAccount instance
            month: Month number (1-12), defaults to last month
            year: Year, defaults to current year
        
        Returns:
            dict with report data
        """
        if not month or not year:
            last_month = timezone.now().replace(day=1) - timedelta(days=1)
            month = last_month.month
            year = last_month.year
        
        # Get positions for the month
        positions = OptionsPosition.objects.filter(
            managed_account=managed_account,
            entry_date__month=month,
            entry_date__year=year
        )
        
        # Closed positions (for realized P&L)
        closed_positions = positions.filter(status='closed')
        
        # Calculate metrics
        total_positions = positions.count()
        winning_trades = closed_positions.filter(realized_pnl__gt=0).count()
        losing_trades = closed_positions.filter(realized_pnl__lt=0).count()
        breakeven_trades = closed_positions.filter(realized_pnl=0).count()
        
        total_realized_pnl = closed_positions.aggregate(
            total=Sum('realized_pnl')
        )['total'] or Decimal('0.00')
        
        # Calculate fees for the month
        fees_paid = self.calculate_monthly_fees(managed_account, month, year)
        
        # Win rate
        win_rate = (winning_trades / closed_positions.count() * 100) if closed_positions.count() > 0 else 0
        
        # Average profit/loss per trade
        avg_pnl = closed_positions.aggregate(
            avg=Avg('realized_pnl')
        )['avg'] or Decimal('0.00')
        
        # Net return (after fees)
        net_return = total_realized_pnl - fees_paid
        
        # ROI calculation
        roi = (net_return / managed_account.initial_capital * 100) if managed_account.initial_capital > 0 else 0
        
        report = {
            'account': managed_account,
            'period': f"{month}/{year}",
            'month_name': date(year, month, 1).strftime('%B %Y'),
            
            # Position counts
            'total_positions': total_positions,
            'closed_positions': closed_positions.count(),
            'open_positions': positions.filter(status='open').count(),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'breakeven_trades': breakeven_trades,
            
            # Performance metrics
            'total_realized_pnl': total_realized_pnl,
            'fees_paid': fees_paid,
            'net_return': net_return,
            'win_rate': win_rate,
            'avg_pnl_per_trade': avg_pnl,
            'roi': roi,
            
            # Account status
            'starting_balance': managed_account.initial_capital,
            'current_balance': managed_account.current_balance,
            'total_profit_loss': managed_account.total_profit_loss,
            
            # Top positions
            'best_trade': closed_positions.order_by('-realized_pnl').first(),
            'worst_trade': closed_positions.order_by('realized_pnl').first(),
        }
        
        return report
    
    def calculate_monthly_fees(self, managed_account, month, year):
        """
        Calculate fees paid for a specific month
        
        Different calculation based on fee tier:
        - Starter/Professional/Premium: % of realized profits
        - Consultative: Session fees + % of profits
        - Co-invest: % of profits
        """
        tier = managed_account.fee_tier
        
        # Get closed positions for the month
        closed_positions = OptionsPosition.objects.filter(
            managed_account=managed_account,
            exit_date__month=month,
            exit_date__year=year,
            status='closed'
        )
        
        # Calculate profit for fee calculation (only profitable trades)
        profitable_trades = closed_positions.filter(realized_pnl__gt=0)
        total_profit = profitable_trades.aggregate(
            total=Sum('realized_pnl')
        )['total'] or Decimal('0.00')
        
        # Fee percentages by tier
        profit_share_rates = {
            'starter': Decimal('0.10'),  # 10%
            'professional': Decimal('0.15'),  # 15%
            'premium': Decimal('0.20'),  # 20%
            'consultative': Decimal('0.20'),  # 20%
            'co_invest': Decimal('0.30'),  # 30%
        }
        
        profit_share_rate = profit_share_rates.get(tier, Decimal('0.10'))
        profit_share_fee = total_profit * profit_share_rate
        
        # Add session fees for consultative tier
        session_fees = Decimal('0.00')
        if tier == 'consultative':
            from ..models import TradingSession
            sessions_this_month = TradingSession.objects.filter(
                managed_account=managed_account,
                session_date__month=month,
                session_date__year=year,
                is_billed=True
            )
            session_fees = sessions_this_month.aggregate(
                total=Sum('fee_charged')
            )['total'] or Decimal('0.00')
        
        total_fees = profit_share_fee + session_fees
        
        return total_fees
    
    def send_monthly_report_email(self, managed_account, month=None, year=None):
        """
        Generate and email monthly performance report to client
        
        Args:
            managed_account: ManagedTradingAccount instance
            month: Month number (defaults to last month)
            year: Year number (defaults to current year)
        
        Returns:
            bool - True if sent successfully
        """
        report = self.generate_monthly_report(managed_account, month, year)
        client = managed_account.client
        
        subject = f"Monthly Performance Report - {report['month_name']}"
        
        # Create email body
        message = f"""
Dear {client.first_name},

Here is your managed trading performance report for {report['month_name']}.

ACCOUNT SUMMARY
--------------
Account Number: {managed_account.account_number}
Fee Tier: {managed_account.get_fee_tier_display()}

PERFORMANCE METRICS
------------------
Total Positions Entered: {report['total_positions']}
Positions Closed: {report['closed_positions']}
Winning Trades: {report['winning_trades']}
Losing Trades: {report['losing_trades']}
Win Rate: {report['win_rate']:.1f}%

FINANCIAL SUMMARY
----------------
Gross P&L: ${report['total_realized_pnl']:,.2f}
Fees Paid: ${report['fees_paid']:,.2f}
Net Return: ${report['net_return']:,.2f}
Monthly ROI: {report['roi']:.2f}%

ACCOUNT BALANCE
--------------
Starting Balance: ${report['starting_balance']:,.2f}
Current Balance: ${report['current_balance']:,.2f}
Total Profit/Loss: ${report['total_profit_loss']:,.2f}

{self._format_best_worst_trades(report)}

View detailed performance:
{getattr(settings, 'SITE_URL', 'https://codamakutano.herokuapp.com')}/investing/managed/portal/

Questions? Contact your account manager or reply to this email.

Best regards,
CODA Investment Team
        """
        
        try:
            # For now, send text email
            # TODO: Generate PDF attachment
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [client.email],
                fail_silently=False
            )
            
            logger.info(f"Monthly report sent to {client.email} for {report['month_name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending monthly report: {str(e)}")
            return False
    
    def send_all_monthly_reports(self, month=None, year=None):
        """
        Send monthly reports to all active managed accounts
        Called monthly via cron (e.g., 1st of each month)
        
        Returns:
            dict with counts of reports sent
        """
        active_accounts = ManagedTradingAccount.objects.filter(
            status='active'
        )
        
        sent_count = 0
        failed_count = 0
        
        for account in active_accounts:
            success = self.send_monthly_report_email(account, month, year)
            if success:
                sent_count += 1
            else:
                failed_count += 1
        
        logger.info(
            f"Monthly reports: {sent_count} sent, {failed_count} failed"
        )
        
        return {
            'sent': sent_count,
            'failed': failed_count,
            'total': active_accounts.count()
        }
    
    def _format_best_worst_trades(self, report):
        """Format best and worst trades section"""
        text = "\nTOP TRADES\n----------\n"
        
        if report['best_trade']:
            best = report['best_trade']
            text += f"Best Trade: {best.symbol} {best.strategy} - ${best.realized_pnl:,.2f}\n"
        
        if report['worst_trade']:
            worst = report['worst_trade']
            text += f"Worst Trade: {worst.symbol} {worst.strategy} - ${worst.realized_pnl:,.2f}\n"
        
        return text

