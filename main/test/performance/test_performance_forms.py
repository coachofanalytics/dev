import time
from django.test import TestCase, Client
from django.test.utils import override_settings
from main.forms import ScholarshipSearchForm  # Import your actual forms
from datetime import timedelta
from django.utils import timezone

@override_settings(
    DEBUG=True,
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    STATICFILES_DIRS=[],
)
class FormPerformanceTest(TestCase):
    """Performance tests for Django forms"""
    
    def setUp(self):
        self.client = Client()
        self.test_data_size = 100
    
    def test_form_validation_performance(self):
        """Test form validation performance with large datasets"""
        print("Testing form validation performance...")
        
        # Test data for form validation
        valid_data = {
            'title': 'Test Scholarship Performance',
            'provider': 'Test University',
            'level': 'Undergraduate',
            'field': 'STEM',
            'location': 'Kenya',
            'amount': '5000 USD',
            'deadline': (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'status': 'Open'
        }
        
        invalid_data = {
            'title': '',  # Invalid - required field
            'provider': 'Test University',
            'level': 'Invalid Level',  # Invalid choice
            'field': 'STEM',
            'location': 'Kenya',
            'amount': 'Invalid Amount',  # Invalid format
            'deadline': 'invalid-date',  # Invalid date
            'status': 'Invalid Status'
        }
        
        # Test valid form performance
        start_time = time.time()
        for i in range(self.test_data_size):
            form = ScholarshipSearchForm(data=valid_data)
            is_valid = form.is_valid()
        end_time = time.time()
        
        valid_time = end_time - start_time
        print(f"✓ Valid form validation: {self.test_data_size} iterations in {valid_time:.3f}s")
        self.assertLess(valid_time, 2.0)
        
        # Test invalid form performance
        start_time = time.time()
        for i in range(self.test_data_size):
            form = ScholarshipSearchForm(data=invalid_data)
            is_valid = form.is_valid()
        end_time = time.time()
        
        invalid_time = end_time - start_time
        print(f"✓ Invalid form validation: {self.test_data_size} iterations in {invalid_time:.3f}s")
        self.assertLess(invalid_time, 3.0)
    
    def test_form_rendering_performance(self):
        """Test form rendering performance"""
        print("Testing form rendering performance...")
        
        form = ScholarshipSearchForm()
        
        start_time = time.time()
        for i in range(self.test_data_size):
            rendered_form = form.as_p()  # Test different rendering methods
            rendered_form_table = form.as_table()
            rendered_form_ul = form.as_ul()
        end_time = time.time()
        
        render_time = end_time - start_time
        print(f"✓ Form rendering: {self.test_data_size * 3} renderings in {render_time:.3f}s")
        self.assertLess(render_time, 5.0)
    
   
    
    def test_form_clean_methods_performance(self):
        """Test custom form clean methods performance"""
        print("Testing custom clean methods performance...")
        
        # Test data that might trigger custom clean methods
        test_cases = [
            {'title': 'Valid Title', 'deadline': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d')},
            {'title': 'A' * 255, 'deadline': (timezone.now() + timedelta(days=365)).strftime('%Y-%m-%d')},  # Max length
            {'title': 'Short', 'deadline': (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d')},  # Past date
        ]
        
        start_time = time.time()
        for test_data in test_cases * 20:  # Repeat each test case
            form = ScholarshipSearchForm(data=test_data)
            form.is_valid()  # This triggers clean methods
        end_time = time.time()
        
        clean_time = end_time - start_time
        print(f"✓ Custom clean methods: {len(test_cases * 20)} validations in {clean_time:.3f}s")
        self.assertLess(clean_time, 2.0)