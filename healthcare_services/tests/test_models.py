from django.test import TestCase
from healthcare_services.models import DoctorSpecialty


class DoctorSpecialtyModelTest(TestCase):

    def test_create_doctor_specialty(self):
        specialty = DoctorSpecialty.objects.create(
            name="General Practice",
            is_default=True
        )

        self.assertEqual(specialty.name, "General Practice")
        self.assertTrue(specialty.is_default)

    def test_doctor_specialty_string_method(self):
        specialty = DoctorSpecialty.objects.create(
            name="Pediatrics",
            is_default=False
        )

        self.assertEqual(str(specialty), "Pediatrics")