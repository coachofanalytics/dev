from django.test import TestCase
from main.models import EmergencyHotline, StaffContact

class EmergencyModelsTest(TestCase):
    def test_hotline_ordering(self):
        EmergencyHotline.objects.create(name="B", number="+2", sort_order=2, is_active=True)
        EmergencyHotline.objects.create(name="A", number="+1", sort_order=1, is_active=True)
        names = list(
            EmergencyHotline.objects.filter(is_active=True)
            .order_by("sort_order", "id")
            .values_list("name", flat=True)
        )
        self.assertEqual(names, ["A", "B"])

    def test_staff_filter_active_notify_email(self):
        StaffContact.objects.create(name="Jane", email="ops@example.org", notify_via_email=True, is_active=True)
        StaffContact.objects.create(name="John", email="", notify_via_email=True, is_active=True)
        emails = list(
            StaffContact.objects.filter(is_active=True, notify_via_email=True)
            .exclude(email__isnull=True)
            .exclude(email__exact="")
            .values_list("email", flat=True)
        )
        self.assertEqual(emails, ["ops@example.org"])
