"""
Management command to verify GoToMeeting OAuth token acquisition and refresh.

Usage:
    poetry run python coda/manage.py verify_goto_oauth
    poetry run python coda/manage.py verify_goto_oauth --service external
    poetry run python coda/manage.py verify_goto_oauth --force-refresh
"""

import logging

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Verify GoToMeeting OAuth token acquisition and refresh (for environment validation)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--service",
            type=str,
            choices=[
                "gotomeeting",
                "gotomeeting_external",
                "gotomeeting_internal",
                "all",
            ],
            default="gotomeeting_internal",
            help='Service name for token lookup (default: gotomeeting_internal). Use "all" to verify all services.',
        )
        parser.add_argument(
            "--force-refresh",
            action="store_true",
            help="Force token refresh by clearing cached token (if caching exists)",
        )

    def handle(self, *args, **options):
        service_param = options.get("service", "gotomeeting_internal")
        force_refresh = options.get("force_refresh", False)

        self.stdout.write(
            self.style.SUCCESS(f"\n🔐 GoToMeeting OAuth Token Verification\n")
        )

        # Determine which services to verify
        if service_param == "all":
            from ai_services.utils.goto_service_registry import \
                list_goto_services

            try:
                services_to_verify = list_goto_services()
                if not services_to_verify:
                    self.stdout.write(
                        self.style.WARNING("⚠️  No GoToMeeting services configured.")
                    )
                    return
            except ImportError:
                # Fallback to internal if registry not available
                services_to_verify = ["gotomeeting_internal"]
        else:
            services_to_verify = [service_param]

        all_success = True

        for service_name in services_to_verify:
            self.stdout.write(f"\nService: {service_name}\n")

            # Force refresh by clearing cache if requested
            if force_refresh:
                cache_key = f"oauth_token_{service_name}"
                cache.delete(cache_key)
                self.stdout.write(
                    self.style.WARNING("⚠️  Cleared cached token (force refresh mode)\n")
                )

            try:
                from ai_services.models import OAuthToken
                from shared_core.utils.oauth import get_access_token

                # Check token status first
                token_obj = OAuthToken.objects.filter(service_name=service_name).first()

                # Determine service type for re-auth URL
                service_type = "external" if "external" in service_name else "internal"
                re_auth_url = f"/management/oauth/login/?service={service_type}"

                # Attempt to get access token
                self.stdout.write("Attempting token acquisition...")
                access_token = get_access_token(service_name=service_name)

                if access_token:
                    # Determine if refresh occurred (check logs or token metadata)
                    try:
                        token_obj = OAuthToken.objects.get(
                            service_name=service_name, is_valid=True
                        )
                        was_refreshed = (
                            token_obj.needs_refresh
                        )  # If it needed refresh, it was refreshed
                        expires_at = token_obj.expires_at

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ Token acquisition OK (refreshed={'yes' if was_refreshed else 'no'})"
                            )
                        )
                        self.stdout.write(f"   Expires at: {expires_at}")
                        self.stdout.write(
                            f"   Token length: {len(access_token)} characters (not displayed for security)"
                        )
                    except OAuthToken.DoesNotExist:
                        self.stdout.write(
                            self.style.SUCCESS(
                                "✅ Token acquisition OK (refreshed=unknown)"
                            )
                        )
                        self.stdout.write(
                            self.style.WARNING(
                                "   Note: Token metadata not available in database"
                            )
                        )
                else:
                    self.stdout.write(self.style.ERROR("❌ Token acquisition FAILED"))

                    # Provide operator-friendly guidance
                    if not token_obj:
                        self.stdout.write(
                            self.style.WARNING(
                                f"   No token found for service '{service_name}'"
                            )
                        )
                        self.stdout.write(
                            self.style.WARNING(f"   Re-authenticate at: {re_auth_url}")
                        )
                    elif not token_obj.is_valid:
                        self.stdout.write(
                            self.style.WARNING(
                                f"   Token exists but is marked as invalid"
                            )
                        )
                        self.stdout.write(
                            self.style.WARNING(f"   Re-authenticate at: {re_auth_url}")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                "   Check logs for details. Token may need to be refreshed or re-authenticated."
                            )
                        )
                        self.stdout.write(
                            self.style.WARNING(f"   Re-authenticate at: {re_auth_url}")
                        )

                    all_success = False

            except ImportError as e:
                self.stdout.write(self.style.ERROR(f"❌ Import error: {e}"))
                all_success = False
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Unexpected error: {e}"))
                logger.exception(f"Error verifying OAuth token for {service_name}")
                all_success = False

        if all_success:
            self.stdout.write(self.style.SUCCESS("\n✅ Verification complete\n"))
        else:
            self.stdout.write(
                self.style.WARNING("\n⚠️  Verification completed with errors\n")
            )
            raise CommandError("Token verification failed for one or more services")
