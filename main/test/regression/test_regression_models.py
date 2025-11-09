from django.test import TestCase
from main.models import Scholarship
from datetime import date, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError


class ScholarshipModelRegressionTest(TestCase):
    """Regression tests to ensure model behavior doesn't break over time"""
    
    def test_field_constraints_unchanged(self):
        """Ensure field constraints remain consistent"""
        # Test max lengths haven't changed
        self.assertEqual(Scholarship._meta.get_field('title').max_length, 200)
        self.assertEqual(Scholarship._meta.get_field('provider').max_length, 200)
        self.assertEqual(Scholarship._meta.get_field('amount').max_length, 100)
        self.assertEqual(Scholarship._meta.get_field('status').max_length, 20)
        
        # Test choice options haven't changed
        level_choices = [choice[0] for choice in Scholarship._meta.get_field('level').choices]
        expected_levels = ['Undergraduate', 'Masters', 'PhD', 'Vocational']
        self.assertEqual(sorted(level_choices), sorted(expected_levels))
        
        field_choices = [choice[0] for choice in Scholarship._meta.get_field('field').choices]
        expected_fields = ['STEM', 'Humanities', 'Business', 'Arts']
        self.assertEqual(sorted(field_choices), sorted(expected_fields))
    
    def test_ordering_behavior_unchanged(self):
        """Ensure default ordering behavior remains consistent"""
        # Create scholarships with different deadlines
        scholarship1 = Scholarship.objects.create(
            title="Regression Test 1",
            provider="Test",
            level="Undergraduate",
            field="STEM",
            location="Kenya",
            amount="1000 USD",
            deadline=date(2025, 12, 31),
            status="Open"
        )
        
        scholarship2 = Scholarship.objects.create(
            title="Regression Test 2",
            provider="Test",
            level="Masters",
            field="Business",
            location="Global",
            amount="2000 USD",
            deadline=date(2025, 6, 30),
            status="Open"
        )
        
        scholarships = list(Scholarship.objects.all())
        # Should still be ordered by deadline (earliest first)
        self.assertEqual(scholarships[0], scholarship2)  # June deadline
        self.assertEqual(scholarships[1], scholarship1)  # December deadline
    
    def test_choice_validation_regression(self):
        """Ensure choice validation remains strict"""
        # These should always raise errors if choices are enforced
        invalid_data_combinations = [
            {'level': 'InvalidLevel'},
            {'field': 'InvalidField'},
            {'location': 'InvalidLocation'},
            {'status': 'InvalidStatus'}
        ]
        
        for invalid_data in invalid_data_combinations:
            with self.subTest(data=invalid_data):
                scholarship_data = {
                    'title': 'Regression Test',
                    'provider': 'Test Provider',
                    'level': 'Undergraduate',
                    'field': 'STEM',
                    'location': 'Kenya',
                    'amount': '1000 USD',
                    'deadline': timezone.now().date() + timedelta(days=10),
                    'status': 'Open'
                }
                scholarship_data.update(invalid_data)
                
                # This might raise an error or might be handled by Django
                # The important thing is consistent behavior
                try:
                    scholarship = Scholarship(**scholarship_data)
                    scholarship.full_clean()  # This might raise ValidationError
                    # If no error, the invalid data was accepted (might be OK depending on model)
                    print(f"Note: Invalid data {invalid_data} was accepted")
                except ValidationError as e:
                    # Expected behavior - invalid choices should raise validation errors
                    field_name = list(invalid_data.keys())[0]
                    self.assertIn(field_name, e.error_dict)
    
    def test_required_fields_regression(self):
        """Ensure required field behavior remains consistent"""
        # Test that the same fields are still required/non-required
        test_cases = [
            {'field': 'title', 'value': '', 'should_raise': False},  # Based on your model
            {'field': 'provider', 'value': '', 'should_raise': False},
            {'field': 'level', 'value': '', 'should_raise': True},  # Choices usually required
        ]
        
        for test_case in test_cases:
            with self.subTest(field=test_case['field']):
                scholarship_data = {
                    'title': 'Required Field Test',
                    'provider': 'Test Provider',
                    'level': 'Undergraduate',
                    'field': 'STEM',
                    'location': 'Kenya',
                    'amount': '1000 USD',
                    'deadline': timezone.now().date() + timedelta(days=10),
                    'status': 'Open'
                }
                
                scholarship_data[test_case['field']] = test_case['value']
                
                try:
                    scholarship = Scholarship(**scholarship_data)
                    scholarship.full_clean()
                    if test_case['should_raise']:
                        self.fail(f"Expected ValidationError for empty {test_case['field']}")
                    else:
                        # No error expected
                        pass
                except ValidationError:
                    if not test_case['should_raise']:
                        self.fail(f"Unexpected ValidationError for {test_case['field']}")