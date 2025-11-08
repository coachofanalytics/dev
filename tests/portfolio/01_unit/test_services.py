"""
Unit tests for portfolio services

Tests business logic, calculations, and service methods in isolation.

Author: CODA Development Team
Created: November 6, 2025
Category: Unit Tests
"""

from django.test import SimpleTestCase, override_settings

from portfolio.services.base_presentation import BasePresentationService, ProjectRegistry


class DemoPresentationService(BasePresentationService):
    """Concrete test implementation of BasePresentationService."""

    project_name = "AI Diaspora"
    project_slug = "ai-diaspora"
    project_tagline = "AI-powered diaspora intelligence"
    created_date = "2025"

    def get_technologies(self):
        return {
            "core": [
                {"name": "Django", "purpose": "Backend"},
                {"name": "PostgreSQL", "purpose": "Database"},
            ]
        }

    def get_key_metrics(self):
        return {"investors": "120", "roi": "18%"}

    def get_investor_context(self):
        return {
            "subtitle": "Investor Value",
            "market_size": "$2B",
            "business_model": "Subscription",
        }

    def get_technical_context(self):
        return {
            "subtitle": "Technical Architecture",
            "stack": ["Django", "Celery", "Redis"],
        }


class BasePresentationServiceTest(SimpleTestCase):
    """Tests for BasePresentationService core behaviour."""

    def setUp(self):
        self.service = DemoPresentationService()

    def test_get_context_includes_core_fields(self):
        """Context should include project metadata and branding."""
        context = self.service.get_context(audience_type="investor")
        self.assertEqual(context["project_name"], "AI Diaspora")
        self.assertEqual(context["project_slug"], "ai-diaspora")
        self.assertTrue(context["show_branding"])
        self.assertIn("branding", context)
        self.assertEqual(context["subtitle"], "Investor Value")
        self.assertEqual(context["market_size"], "$2B")
        self.assertEqual(context["technologies"]["core"][0]["name"], "Django")

    @override_settings(
        DEVELOPER_NAME="Jane Developer",
        DEVELOPER_TITLE="Lead Engineer",
        DEVELOPER_EMAIL="jane@example.com",
        DEVELOPER_LINKEDIN="https://linkedin.com/in/jane",
        DEVELOPER_GITHUB="https://github.com/jane",
    )
    def test_get_context_interview_mode_branding(self):
        """Interview mode should use developer-centric branding."""
        context = self.service.get_context(audience_type="technical", presentation_mode="interview")
        self.assertFalse(context["show_branding"])
        branding = context["branding"]
        self.assertEqual(branding["developer_name"], "Jane Developer")
        self.assertEqual(context["subtitle"], "Technical Architecture")
        self.assertIn("stack", context)
        self.assertIn("Django", context["stack"])

    def test_get_context_default_subtitle(self):
        """Unknown audience should fall back to default subtitle."""
        context = self.service.get_context(audience_type="demo")
        self.assertEqual(context["subtitle"], "Interactive Demonstration")


class ProjectRegistryTest(SimpleTestCase):
    """Tests for ProjectRegistry registration and retrieval."""

    def setUp(self):
        # Reset registry between tests
        ProjectRegistry._projects = {}

    def test_register_and_retrieve_service(self):
        """Services can be registered and retrieved by slug."""
        ProjectRegistry.register("ai-diaspora", DemoPresentationService)
        service = ProjectRegistry.get_service("ai-diaspora")
        self.assertIsInstance(service, DemoPresentationService)
        self.assertEqual(service.project_name, "AI Diaspora")

    def test_get_all_projects_sorted(self):
        """Project list should return metadata sorted by created_date desc."""
        class OlderService(DemoPresentationService):
            project_name = "Legacy Project"
            project_slug = "legacy"
            created_date = "2024"

        ProjectRegistry.register("legacy", OlderService)
        ProjectRegistry.register("ai-diaspora", DemoPresentationService)

        projects = ProjectRegistry.get_all_projects()
        self.assertEqual(projects[0]["slug"], "ai-diaspora")
        self.assertEqual(projects[1]["slug"], "legacy")

    def test_get_service_missing_project(self):
        """Requesting unknown project should raise ValueError."""
        with self.assertRaises(ValueError):
            ProjectRegistry.get_service("unknown-project")
