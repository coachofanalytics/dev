from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from main.models import ExpertInquiry
from datetime import datetime

class Command(BaseCommand):
    help = 'Check for overdue and urgent inquiries'
    
    def handle(self, *args, **options):
        # Get urgent inquiries
        urgent = ExpertInquiry.get_urgent_inquiries()
        overdue = ExpertInquiry.get_overdue_inquiries()
        
        if urgent or overdue:
            # Build email message
            message = f"Daily Inquiry Report - {datetime.now().strftime('%Y-%m-%d')}\n"
            message += "="*50 + "\n\n"
            
            if urgent:
                message += f"🔴 URGENT INQUIRIES ({len(urgent)}):\n"
                for i in urgent:
                    message += f"  - {i.full_name} ({i.email}) - {i.created_at.strftime('%Y-%m-%d')}\n"
                message += "\n"
            
            if overdue:
                message += f"⚠️ OVERDUE INQUIRIES ({len(overdue)}):\n"
                for i in overdue:
                    message += f"  - {i.full_name} ({i.email}) - {i.days_since_created()} days old\n"
                message += "\n"
            
            # Send email to admin
            send_mail(
                subject=f"Daily Inquiry Report: {len(urgent)} urgent, {len(overdue)} overdue",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )
            
            self.stdout.write(self.style.SUCCESS(f"Report sent: {len(urgent)} urgent, {len(overdue)} overdue"))
        else:
            self.stdout.write(self.style.SUCCESS("No urgent or overdue inquiries"))