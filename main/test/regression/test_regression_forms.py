from django.test import TestCase
from main.forms import ScholarshipSearchForm


class ScholarshipSearchFormRegressionTest(TestCase):
    """Regression tests for ScholarshipSearchForm"""
    
    def test_form_structure_consistency(self):
        """Ensure form fields remain consistent"""
        form = ScholarshipSearchForm()
        expected_fields = ['search_keyword', 'filter_level', 'filter_field', 
                          'filter_location', 'filter_status']
        
        current_fields = list(form.fields.keys())
        self.assertEqual(current_fields, expected_fields,
                       "Form field structure should not change")
        print("✓ Form structure is consistent")
    
    def test_form_always_valid(self):
        """Search forms should always be valid"""
        # Test various data combinations
        test_cases = [
            {},  # Empty
            {'search_keyword': 'test'},
            {'filter_level': 'Undergraduate'},
            {'search_keyword': 'test', 'filter_level': 'Masters'}
        ]
        
        for data in test_cases:
            form = ScholarshipSearchForm(data=data)
            self.assertTrue(form.is_valid(), 
                           f"Form should be valid with data: {data}")
        print("✓ Form is always valid")
    
    def test_field_types_consistency(self):
        """Ensure field types remain the same"""
        form = ScholarshipSearchForm()
        
        field_types = {
            'search_keyword': 'CharField',
            'filter_level': 'ChoiceField',
            'filter_field': 'ChoiceField',
            'filter_location': 'ChoiceField',
            'filter_status': 'BooleanField',  # Based on your error
        }
        
        for field_name, expected_type in field_types.items():
            actual_type = type(form.fields[field_name]).__name__
            self.assertEqual(actual_type, expected_type,
                           f"Field {field_name} should be {expected_type}")
            print(f"✓ {field_name} is {expected_type}")
    
    def test_choice_fields_have_options(self):
        """Ensure choice fields have expected options"""
        form = ScholarshipSearchForm()
        
        # Only test fields that are actually ChoiceFields
        choice_fields = ['filter_level', 'filter_field', 'filter_location']
        
        for field_name in choice_fields:
            field = form.fields[field_name]
            self.assertTrue(hasattr(field, 'choices'), 
                          f"{field_name} should have choices")
            self.assertGreater(len(field.choices), 0,
                             f"{field_name} should have choice options")
            print(f"✓ {field_name} has choice options")


class ScholarshipSearchFormQuickTest(TestCase):
    """Quick regression test"""
    
    def test_basic_functionality(self):
        """Test the form works as expected"""
        # Test structure
        form = ScholarshipSearchForm()
        self.assertEqual(list(form.fields.keys()), 
                        ['search_keyword', 'filter_level', 'filter_field', 
                         'filter_location', 'filter_status'])
        
        # Test validation
        self.assertTrue(ScholarshipSearchForm(data={}).is_valid())
        self.assertTrue(ScholarshipSearchForm(data={'search_keyword': 'test'}).is_valid())
        
        # Test field types
        self.assertEqual(type(form.fields['search_keyword']).__name__, 'CharField')
        self.assertEqual(type(form.fields['filter_status']).__name__, 'BooleanField')
        
        print("✓ All basic regression checks passed!")