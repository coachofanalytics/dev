"""
Management command to check AI settings configuration.

Safely validates which API keys are present and which providers are configured.
Never prints full API keys - only shows presence (boolean) and last 4 characters.
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check AI settings configuration (safely - no secrets printed)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show more detailed information",
        )

    def handle(self, *args, **options):
        verbose = options.get("verbose", False)

        self.stdout.write(self.style.SUCCESS("🔍 AI Settings Check"))
        self.stdout.write("=" * 50)

        # Check OpenAI
        openai_key = getattr(settings, "OPENAI_API_KEY", None) or os.environ.get(
            "OPENAI_API_KEY"
        )
        if openai_key:
            # Show only last 4 chars for verification
            key_suffix = openai_key[-4:] if len(openai_key) > 4 else "****"
            self.stdout.write(
                self.style.SUCCESS(f"✅ OpenAI API Key: Present (sk-...{key_suffix})")
            )
            if verbose:
                self.stdout.write(f"   Key length: {len(openai_key)} characters")
        else:
            self.stdout.write(self.style.WARNING("❌ OpenAI API Key: Not configured"))

        # Check Claude
        claude_key = (
            getattr(settings, "CLAUDE_API_KEY", None)
            or getattr(settings, "ANTHROPIC_API_KEY", None)
            or os.environ.get("CLAUDE_API_KEY")
            or os.environ.get("ANTHROPIC_API_KEY")
        )
        if claude_key:
            key_suffix = claude_key[-4:] if len(claude_key) > 4 else "****"
            self.stdout.write(
                self.style.SUCCESS(f"✅ Claude API Key: Present (...{key_suffix})")
            )
        else:
            self.stdout.write(self.style.WARNING("❌ Claude API Key: Not configured"))

        # Check database configurations
        try:
            from ai_services.models import AIModelConfiguration, AIModelTypes

            configs = AIModelConfiguration.objects.filter(is_active=True).order_by(
                "priority_order"
            )

            if configs.exists():
                self.stdout.write(self.style.SUCCESS("\n📊 Database Configurations:"))
                for config in configs:
                    has_key = bool(config.api_key)
                    key_status = "✅" if has_key else "⚠️"
                    key_suffix = (
                        f"...{config.api_key[-4:]}"
                        if has_key and len(config.api_key) > 4
                        else "Not set"
                    )

                    self.stdout.write(
                        f"   {key_status} {config.model_name}: "
                        f"Priority {config.priority_order}, "
                        f"Key: {key_suffix}"
                    )
                    if verbose:
                        self.stdout.write(
                            f'      Endpoint: {config.api_endpoint or "N/A"}, '
                            f"Max tokens: {config.max_tokens}, "
                            f"Temperature: {config.temperature}"
                        )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "\n⚠️  No active AI model configurations in database"
                    )
                )
                self.stdout.write("   Run: python manage.py setup_ai_models")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error checking database: {e}"))

        # Determine primary provider
        self.stdout.write("\n🎯 Primary Provider:")
        if openai_key:
            self.stdout.write(self.style.SUCCESS("   OpenAI (GPT-4, GPT-3.5)"))
        elif claude_key:
            self.stdout.write(self.style.SUCCESS("   Claude (Claude-3)"))
        else:
            self.stdout.write(self.style.WARNING("   Local Offline (Fallback only)"))

        # Check fallback chain
        self.stdout.write("\n🔄 Fallback Chain:")
        fallbacks = []
        if openai_key:
            fallbacks.append("GPT-4 → GPT-3.5")
        if claude_key:
            fallbacks.append("Claude-3")
        fallbacks.append("Local Offline")

        for i, fb in enumerate(fallbacks, 1):
            self.stdout.write(f"   {i}. {fb}")

        # Check LangChain installation
        self.stdout.write("\n📦 LangChain Status:")
        try:
            import langchain_community

            langchain_installed = True
            self.stdout.write(self.style.SUCCESS("   ✅ LangChain: Installed"))
        except ImportError:
            langchain_installed = False
            self.stdout.write(self.style.WARNING("   ❌ LangChain: Not installed"))

        # Check AI feature flags
        self.stdout.write("\n🚩 AI Feature Flags:")
        ai_enabled = getattr(settings, "AI_ENABLED", False)
        ai_requirement_match = getattr(settings, "AI_REQUIREMENT_MATCH_ENABLED", False)
        ai_shadow_mode = getattr(settings, "AI_SHADOW_MODE", True)

        self.stdout.write(f'   AI_ENABLED: {"✅ True" if ai_enabled else "❌ False"}')
        self.stdout.write(
            f'   AI_REQUIREMENT_MATCH_ENABLED: {"✅ True" if ai_requirement_match else "❌ False"}'
        )
        self.stdout.write(
            f'   AI_SHADOW_MODE: {"✅ True" if ai_shadow_mode else "❌ False"}'
        )

        # Check cache settings
        self.stdout.write("\n💾 Cache Status:")
        try:
            from django.core.cache import cache

            cache.set("ai_test_key", "test", 60)
            if cache.get("ai_test_key") == "test":
                self.stdout.write(self.style.SUCCESS("   ✅ Django cache: Working"))
            else:
                self.stdout.write(self.style.WARNING("   ⚠️  Django cache: Not working"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Django cache: Error - {e}"))

        # Summary
        self.stdout.write("\n" + "=" * 50)
        if openai_key or claude_key:
            self.stdout.write(self.style.SUCCESS("✅ AI services: Ready"))
        else:
            self.stdout.write(
                self.style.WARNING("⚠️  AI services: Fallback mode only (no API keys)")
            )

        self.stdout.write(
            "\n💡 Tip: Add OPENAI_API_KEY to dev.env for local development"
        )
