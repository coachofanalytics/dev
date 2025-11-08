from django.test import TestCase, override_settings
from django.urls import reverse
from main.models import EmergencyHotline, StaffContact, EmergencyHelpActivation
from django.core import mail

@override_settings(STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
class CrisisPageViewTest(TestCase):
    def test_crisis_page_hotlines_in_context(self):
        EmergencyHotline.objects.create(name="A", number="+1", sort_order=1, is_active=True)
        EmergencyHotline.objects.create(name="B", number="+2", sort_order=2, is_active=True)
        resp = self.client.get(reverse("main:crisis_page"))
        self.assertEqual(resp.status_code, 200)
        names = list(resp.context["hotlines"].values_list("name", flat=True))
        self.assertEqual(names, ["A", "B"])

@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ActivateHelplineTest(TestCase):
    def test_requires_phone(self):
        resp = self.client.post(reverse("main:activate_helpline"), {"name": "X", "phone": ""})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Phone number is required", resp.json()["message"]) 

    def test_creates_activation_and_sends_emails(self):
        StaffContact.objects.create(name="Jane", email="ops@example.org", notify_via_email=True, is_active=True)
        payload = {"name": "User", "phone": "+1555", "location": "Nairobi", "notes": "Help"}
        resp = self.client.post(reverse("main:activate_helpline"), payload)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"]) 
        self.assertEqual(EmergencyHelpActivation.objects.count(), 1)
        # confirm an email was queued for sending
        self.assertEqual(len(mail.outbox), 1)
