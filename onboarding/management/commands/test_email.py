"""
Management command to test email sending functionality.
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email sending functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            default='test@example.com',
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        to_email = options['to']

        self.stdout.write(f'Sending test email to: {to_email}')
        self.stdout.write(f'Email Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'Email Host: {settings.EMAIL_HOST}')
        self.stdout.write(f'Email Port: {settings.EMAIL_PORT}')
        self.stdout.write(f'From Email: {settings.DEFAULT_FROM_EMAIL}')

        try:
            send_mail(
                subject='Test Email from Biashara Bridges',
                message='This is a test email to verify email sending is working correctly.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message="""
                    <html>
                    <body>
                        <h2>Test Email</h2>
                        <p>This is a test email to verify email sending is working correctly.</p>
                        <p>If you received this, email configuration is working!</p>
                    </body>
                    </html>
                """,
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'[SUCCESS] Email sent successfully to {to_email}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] Failed to send email: {str(e)}'))
