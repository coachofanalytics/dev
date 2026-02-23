# communities/tests/regression/test_bugs.py
from django.test import TestCase
from django.urls import reverse

class TestRegressionBugs(TestCase):
    """Regression tests for bugs that should stay fixed"""
    
    def test_empty_search_regression(self):
        """Empty search should not break the page"""
        response = self.client.get(reverse('member_directory'), {
            'search': ''  # Empty string
        })
        self.assertEqual(response.status_code, 200)
        print("✅ Empty search handled correctly")
    
    def test_special_characters_regression(self):
        """Special characters in search should be handled"""
        response = self.client.get(reverse('member_directory'), {
            'search': 'test@email.com #special $chars'
        })
        self.assertEqual(response.status_code, 200)
        print("✅ Special characters handled correctly")
    
    def test_long_input_regression(self):
        """Very long search input should not break"""
        long_string = 'a' * 1000  # Very long string
        response = self.client.get(reverse('member_directory'), {
            'search': long_string
        })
        self.assertEqual(response.status_code, 200)
        print("✅ Long input handled correctly")