from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from main.models import ExpertInquiry

class Command(BaseCommand):
    help = 'Test email configuration'
    
    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to send test to')
    
    def handle(self, *args, **options):
        email = options['email']
        
        try:
            send_mail(
                subject='Test Email from Insurance Support',
                message='This is a test email to verify your email configuration.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Test email sent to {email}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to send email: {e}'))