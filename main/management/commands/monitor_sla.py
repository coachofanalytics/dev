from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from main.models import ExpertInquiry
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Monitor SLA compliance and send alerts'
    
    def handle(self, *args, **options):
        self.stdout.write(f"SLA check started at {timezone.now()}")
        
        # Check SLA for all open inquiries
        ExpertInquiry.check_all_sla()
        
        # Get stats
        stats = ExpertInquiry.get_sla_compliance_stats()
        
        self.stdout.write(f"Stats: {stats}")
        
        # Send hourly report if there are escalated issues
        if stats and stats.get('escalated', 0) > 0:
            report = f"""
            🚨 SLA MONITORING REPORT
            ========================
            Time: {timezone.now().strftime('%Y-%m-%d %H:%M')}
            
            Escalated Inquiries: {stats.get('escalated', 0)}
            Total Open: {stats.get('total', 0) - stats.get('resolved', 0)}
            Compliance Rate: {stats.get('compliance_rate', 0)}%
            Avg Response: {stats.get('avg_response_time', 'N/A')}
            
            Please check admin panel immediately.
            """
            
            try:
                send_mail(
                    subject=f"🚨 {stats.get('escalated', 0)} Inquiries Escalated - Immediate Action Required",
                    message=report,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS("Alert email sent"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to send email: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"SLA check complete. Escalated: {stats.get('escalated', 0)}"))