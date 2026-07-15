from django.test import TestCase
from django.urls import reverse

from healthcare_services.models import DoctorSpecialty


class DoctorSpecialtyListViewTest(TestCase):

    def setUp(self):
        DoctorSpecialty.objects.create(
            name="Cardiology",
            is_default=True
        )

        DoctorSpecialty.objects.create(
            name="Dermatology",
            is_default=False
        )

    def test_doctor_specialty_list_view_status_code(self):
        response = self.client.get("/healthcare/doctor-specialties/")
        self.assertEqual(response.status_code, 200)

    def test_doctor_specialty_list_view_uses_correct_template(self):
        response = self.client.get("/healthcare/doctor-specialties/")
        self.assertTemplateUsed(
            response,
            "healthcare_services/doctor_specialty_list.html"
        )

    def test_doctor_specialty_list_view_displays_specialties(self):
        response = self.client.get("/healthcare/doctor-specialties/")
        self.assertContains(response, "Cardiology")
        self.assertContains(response, "Dermatology")

    def test_doctor_specialty_list_context_name(self):
        response = self.client.get("/healthcare/doctor-specialties/")
        self.assertIn("specialties", response.context)
        self.assertEqual(response.context["specialties"].count(), 2)

    def test_doctor_specialty_list_url_name(self):
        url = reverse("healthcare_services:doctor_specialty_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)