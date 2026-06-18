from django.conf import settings
from django.test import SimpleTestCase


class TemplatesUnitTest(SimpleTestCase):
    def test_templates_config_present(self):
        self.assertTrue(getattr(settings, "TEMPLATES", None))

