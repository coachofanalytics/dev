from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from finance.models import Opportunity, NewsLetterSubscriber

class Command(BaseCommand):
    help = 'Sends a weekly digest of approved opportunities to subscribers'

    def handle(self, *args, **options):
        # 1. Get opportunities from the last 7 days
        last_week = timezone.now() - timedelta(days=7)
        new_opps = Opportunity.approved.filter(created_at__gte=last_week)

        if not new_opps.exists():
            self.stdout.write("No new opportunities to send.")
            return

        # 2. Build the email content
        subject = "This Week's Top Investment Opportunities"
        intro = "Check out the latest community-verified opportunities:\n\n"

        opp_list = ""
        for opp in new_opps:
            opp_list += f"- {opp.title} ({opp.type}): {opp.description[:100]}...\n"

        full_message = intro + opp_list + "\nVisit the directory for more details!"

        # 3. Get all verified subscribers
        subscribers = NewsLetterSubscriber.objects.filter(is_verified=True).values_list('email', flat=True)

        if subscribers:
            # We send to the list of emails
            send_mail(
                subject,
                full_message,
                settings.DEFAULT_FROM_EMAIL,
                list(subscribers),
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"Digest sent to {len(subscribers)} subscribers!"))
