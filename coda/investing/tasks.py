"""
Celery Tasks for Managed Options Trading

Background tasks for automated position fetching, batch processing, and notifications.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

from .services import (
    PositionFetcherService,
    BatchApprovalService,
    NotificationService,
    CapitalAllocationService,
    UnusualWhalesService,
)
from .models import SuggestedPosition, ManagedTradingAccount, PositionBatch

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def daily_position_fetch_task(self):
    """
    Scheduled task: Fetch high-probability positions daily at 9 AM EST
    
    Workflow:
    1. Fetch positions from OptionPlay/Thinkorswim
    2. Save to SuggestedPosition model (status=pending)
    3. Email staff to review
    
    Schedule: Daily at 9:00 AM EST (14:00 UTC)
    Configured in: celeryapp.py beat_schedule
    """
    try:
        logger.info("🤖 Starting daily position fetch task...")
        
        # Default high-probability filters
        filters = {
            'probability_min': 70,
            'premium_min': 100,
            'dte_min': 30,
            'dte_max': 60,
            'strategies': [
                'bull_put_spread',
                'bear_call_spread',
                'bull_call_spread',
                'bear_put_spread'
            ],
            'max_positions': 10,  # Fetch 10, staff will pick best 5
            'symbols': ['SPY', 'QQQ', 'IWM', 'DIA', 'AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMZN', 'GOOGL']
        }
        
        # Fetch positions
        fetcher = PositionFetcherService()
        suggested_positions = fetcher.fetch_high_probability_positions(filters)
        
        if suggested_positions:
            # Calculate summary stats
            avg_probability = sum(float(p.probability_of_profit) for p in suggested_positions) / len(suggested_positions)
            total_premium = sum(float(p.premium_collected) for p in suggested_positions)
            
            # Email staff
            staff_emails = list(User.objects.filter(is_staff=True, email__isnull=False).values_list('email', flat=True))
            
            if staff_emails:
                site_url = getattr(settings, 'SITE_URL', 'https://codatrainingapp.herokuapp.com')
                
                send_mail(
                    subject=f"🤖 Daily Position Fetch: {len(suggested_positions)} New Suggestions (Avg {avg_probability:.1f}% Prob)",
                    message=f"""
Daily position fetch complete!

📊 Summary:
• Positions Fetched: {len(suggested_positions)}
• Average Probability: {avg_probability:.1f}%
• Total Premium: ${total_premium:,.0f}
• Date: {timezone.now().strftime('%Y-%m-%d %H:%M %Z')}

🔍 Top 3 Positions:
""" + "\n".join([
    f"{i+1}. {p.symbol} {p.get_strategy_display()} - {p.probability_of_profit}% prob, ${p.premium_collected} premium, {p.dte} DTE"
    for i, p in enumerate(suggested_positions[:3])
]) + f"""

📝 Next Steps:
1. Review positions: {site_url}/investing/managed/staff/suggestions/
2. Approve/edit positions
3. Create batch for client approval

⚙️ Automation Status:
✅ OptionPlay API: {'Connected' if suggested_positions[0].source == 'optionplay' else 'Using fallback'}
✅ Filters Applied: 70%+ prob, $100+ premium, 30-60 DTE
✅ Positions saved to database

This is an automated daily fetch (9 AM EST).
                    """,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@codanalytics.net'),
                    recipient_list=staff_emails,
                    fail_silently=False,
                )
                
                logger.info(f"✅ Sent notification to {len(staff_emails)} staff members")
            
            logger.info(f"✅ Daily position fetch complete: {len(suggested_positions)} positions")
            return {
                'success': True,
                'positions_fetched': len(suggested_positions),
                'avg_probability': avg_probability,
                'total_premium': float(total_premium)
            }
        else:
            logger.warning("⚠️  No positions met criteria")
            return {
                'success': False,
                'message': 'No positions met filtering criteria'
            }
    
    except Exception as exc:
        logger.error(f"❌ Daily position fetch failed: {exc}", exc_info=True)
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_batch_timeouts_task(self):
    """
    Scheduled task: Process batch approval timeouts (24-hour deadline)
    
    Finds batches past deadline and auto-rejects them.
    
    Schedule: Every hour
    """
    try:
        logger.info("⏰ Checking for expired position batches...")
        
        batch_service = BatchApprovalService()
        expired_batches = batch_service.process_timeouts()
        
        if expired_batches:
            logger.info(f"✅ Processed {len(expired_batches)} expired batches")
            
            # Email affected clients
            notification_service = NotificationService()
            for batch in expired_batches:
                notification_service.send_batch_timeout_notification(batch)
            
            return {
                'success': True,
                'expired_batches': len(expired_batches)
            }
        else:
            logger.info("✅ No expired batches")
            return {
                'success': True,
                'expired_batches': 0
            }
    
    except Exception as exc:
        logger.error(f"❌ Batch timeout processing failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@shared_task
def send_weekly_position_summary_task():
    """
    Scheduled task: Send weekly summary to staff
    
    Summary includes:
    - Total positions fetched this week
    - Approval rate (staff and client)
    - Top performing strategies
    - API health status
    
    Schedule: Every Monday at 8 AM EST
    """
    try:
        logger.info("📊 Generating weekly position summary...")
        
        week_ago = timezone.now() - timedelta(days=7)
        
        # Get positions fetched this week
        fetched_this_week = SuggestedPosition.objects.filter(
            fetched_at__gte=week_ago
        )
        
        # Calculate stats
        total_fetched = fetched_this_week.count()
        staff_approved = fetched_this_week.filter(review_status__in=['approved', 'modified', 'converted']).count()
        staff_rejected = fetched_this_week.filter(review_status='rejected').count()
        
        staff_approval_rate = (staff_approved / total_fetched * 100) if total_fetched > 0 else 0
        
        # Get batches created this week
        batches_this_week = PositionBatch.objects.filter(
            created_date__gte=week_ago
        )
        
        client_approved = batches_this_week.filter(status='approved').count()
        client_rejected = batches_this_week.filter(status__in=['rejected', 'expired']).count()
        
        client_approval_rate = (client_approved / batches_this_week.count() * 100) if batches_this_week.count() > 0 else 0
        
        # Email staff
        staff_emails = list(User.objects.filter(is_staff=True, email__isnull=False).values_list('email', flat=True))
        
        if staff_emails:
            send_mail(
                subject=f"📊 Weekly Position Summary - {timezone.now().strftime('%Y-W%W')}",
                message=f"""
Weekly Automated Position Sourcing Summary

📅 Week of: {timezone.now().strftime('%Y-%m-%d')}

📊 Positions Fetched:
• Total Fetched: {total_fetched}
• Staff Approved: {staff_approved} ({staff_approval_rate:.1f}%)
• Staff Rejected: {staff_rejected}

📦 Client Batches:
• Batches Created: {batches_this_week.count()}
• Client Approved: {client_approved} ({client_approval_rate:.1f}%)
• Client Rejected: {client_rejected}

🎯 Top Strategies:
{self._get_top_strategies(fetched_this_week)}

⚙️ System Health:
• OptionPlay API: {'🟢 Operational' if fetched_this_week.filter(source='optionplay').exists() else '🔴 Down - Using fallback'}
• Thinkorswim API: {'🟢 Operational' if fetched_this_week.filter(source='thinkorswim').exists() else '⚪ Not used'}

📝 Action Items:
• Review suggestions: https://codatrainingapp.herokuapp.com/investing/managed/staff/suggestions/
• Monitor batches: https://codatrainingapp.herokuapp.com/investing/managed/staff/batches/

This is an automated weekly summary.
                """,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@codanalytics.net'),
                recipient_list=staff_emails,
                fail_silently=False,
            )
            
            logger.info(f"✅ Sent weekly summary to {len(staff_emails)} staff members")
        
        return {
            'success': True,
            'total_fetched': total_fetched,
            'staff_approval_rate': staff_approval_rate,
            'client_approval_rate': client_approval_rate
        }
    
    except Exception as exc:
        logger.error(f"❌ Weekly summary failed: {exc}", exc_info=True)
        return {'success': False, 'error': str(exc)}
    
    def _get_top_strategies(self, queryset):
        """Get top 3 most fetched strategies"""
        from django.db.models import Count
        top = queryset.values('strategy').annotate(
            count=Count('id')
        ).order_by('-count')[:3]
        
        if top:
            return "\n".join([
                f"• {item['get_strategy_display']}: {item['count']} positions"
                for item in top
            ])
        return "• No data"


@shared_task(bind=True, default_retry_delay=180, max_retries=3)
def managed_income_scheduler(self):
    """Size positions for managed accounts to hit monthly income targets."""

    try:
        logger.info("💼 Running managed income scheduler...")

        pending_qs = SuggestedPosition.objects.filter(review_status='pending').order_by('-ai_score')
        suggestions = list(pending_qs[:25])

        if not suggestions:
            logger.info("No pending suggestions found — triggering fetch fallback")
            fetcher = PositionFetcherService()
            fallback_filters = {
                'probability_min': 65,
                'premium_min': 75,
                'dte_min': 25,
                'dte_max': 55,
                'max_positions': 12,
            }
            suggestions = fetcher.fetch_high_probability_positions(fallback_filters) or []

        if not suggestions:
            logger.warning("Managed income scheduler: still no suggestions after fallback")
            return {
                'success': False,
                'message': 'No suggestions available for allocation'
            }

        uw_service = UnusualWhalesService()
        if uw_service.is_enabled():
            uw_service.apply_flow_to_suggestions(suggestions)

        allocation_service = CapitalAllocationService()
        summary = allocation_service.recommend_allocations(suggestions)

        digest_sent = NotificationService().send_internal_allocation_digest(summary)

        totals = summary.get('totals', {})
        logger.info(
            "✅ Managed income scheduler complete: %s positions (coverage %s%%, digest=%s)",
            totals.get('positions', 0),
            totals.get('coverage_pct', 0),
            'sent' if digest_sent else 'skipped',
        )

        return {
            'success': True,
            'totals': totals,
            'meets_target': summary.get('meets_target', False),
            'notes': summary.get('notes', []),
        }

    except Exception as exc:
        logger.error("❌ Managed income scheduler failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)

