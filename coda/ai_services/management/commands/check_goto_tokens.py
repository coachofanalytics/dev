"""
Management command to check GoToMeeting OAuth token status in database.

Usage:
    poetry run python coda/manage.py check_goto_tokens

This command prints the current OAuth token status from the database
(without exposing token values) to help verify DB persistence.
"""

from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check GoToMeeting OAuth token status in database"

    def handle(self, *args, **options):
        """Print OAuth token status with safe information only."""
        try:
            OAuthToken = apps.get_model("ai_services", "OAuthToken")
        except LookupError:
            self.stdout.write(self.style.ERROR("ai_services app not found"))
            return

        # Get latest token for gotomeeting service
        try:
            token = (
                OAuthToken.objects.filter(service_name="gotomeeting")
                .order_by("-id")
                .first()
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error querying OAuthToken: {e}"))
            return

        self.stdout.write("=" * 60)
        self.stdout.write("GoToMeeting OAuth Token Status (Database)")
        self.stdout.write("=" * 60)

        if token:
            self.stdout.write(self.style.SUCCESS(f"✓ Token found (ID: {token.id})"))
            self.stdout.write(f"  Service: {token.service_name}")
            self.stdout.write(f"  Expires at: {token.expires_at}")
            self.stdout.write(f"  Is valid: {token.is_valid}")
            self.stdout.write(f"  Has access token: {bool(token.access_token)}")
            self.stdout.write(f"  Has refresh token: {bool(token.refresh_token)}")
            self.stdout.write(f"  Created: {token.created_at}")
            self.stdout.write(f"  Last refreshed: {token.last_refreshed_at or 'Never'}")
            self.stdout.write(f"  Is expired: {token.is_expired}")
            self.stdout.write(f"  Needs refresh: {token.needs_refresh}")
        else:
            self.stdout.write(
                self.style.WARNING("✗ No token found for service 'gotomeeting'")
            )
            self.stdout.write(
                "  Run OAuth flow at /management/oauth/login/ to create a token"
            )

        self.stdout.write("=" * 60)
        self.stdout.write("")
