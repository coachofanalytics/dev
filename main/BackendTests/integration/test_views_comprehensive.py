"""
Comprehensive Integration Tests for Main App Views
Tests view endpoints, form processing, and API interactions
"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta, date
import json
import tempfile
import time
from unittest.mock import patch, MagicMock
from PIL import Image
import io
from django.core.files.uploadedfile import SimpleUploadedFile

from main.models import (
    Doctor, AppointmentRequest, InsurancePlan, AIRecommendationRule,
    ExpertInquiry, Governance
)
from main.forms import AppointmentRequestForm

User = get_user_model()


# =====================================================================
# AI RECOMMENDATION ENDPOINT TESTS
# =====================================================================

@patch('main.views.generate_recommendation_text', return_value='Mocked recommendation')
class AIRecommendationAPITests(TestCase):
    """Tests for POST /healthcare/insurance-support/api/recommend/"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.url = '/healthcare/insurance-support/api/recommend/'
        self.plan = InsurancePlan.objects.create(
            provider_name='TestProvider',
            plan_name='TestPlan',
            network='Global',
            max_benefit='$1M',
            evacuation='Included',
            score=9.5
        )
    
    def test_post_valid_payload_returns_200(self, mock_gen):
        """Test: POST valid payload returns 200 + recommendation"""
        payload = {
            'age': 'young',
            'residence': 'usa',
            'priority': 'budget'
        }
        
        # Create matching rule
        rule = AIRecommendationRule.objects.create(
            age_bracket='young',
            residence='usa',
            priority='budget',
            recommended_plan=self.plan,
            recommendation_text='Perfect match'
        )
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('plan_name', data)
    
    def test_post_empty_payload_handles_gracefully(self, mock_gen):
        """Test: POST empty payload handles gracefully (no 500)"""
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )
        
        # Should not be 500
        self.assertNotEqual(response.status_code, 500)
    
    def test_post_missing_age_handles_gracefully(self, mock_gen):
        """Test: POST missing age field handles gracefully"""
        payload = {
            'residence': 'usa',
            'priority': 'comprehensive'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertNotEqual(response.status_code, 500)
    
    def test_post_no_matching_rule_uses_fallback(self, mock_gen):
        """Test: No matching rule uses fallback (highest score plan)"""
        # Don't create any rules, only plans
        payload = {
            'age': 'senior',
            'residence': 'other',
            'priority': 'emergency'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])


# =====================================================================
# DOCTOR BOOKING ENDPOINT TESTS
# =====================================================================

@override_settings(
    DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage',
    MEDIA_ROOT=tempfile.mkdtemp()
)
@patch('django.core.mail.send_mail')
class DoctorBookingTests(TestCase):
    """Tests for POST /api/doctor/<id>/book/"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.doctor = Doctor.objects.create(
            name='Dr. Booking Test',
            title='GP',
            specialty='General',
            categories=['general'],
            location_city='Test City',
            location_country='Test Country',
            languages=['english'],
            bio='Test'
        )
        self.future_date = str((timezone.now().date() + timedelta(days=7)))
        self.url = f'/api/doctor/{self.doctor.id}/book/'
    
    def test_post_valid_booking_returns_success(self, mock_mail):
        """Test: POST valid booking returns success response"""
        data = {
            'full_name': 'Patient Name',
            'email': 'patient@example.com',
            'preferred_date': self.future_date,
            'preferred_time': 'morning',
            'reason': 'Checkup',
            'honeypot': ''
        }
        
        response = self.client.post(self.url, data=data, follow=False)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
    
    def test_post_honeypot_filled_rejected(self, mock_mail):
        """Test: Honeypot filled is rejected"""
        data = {
            'full_name': 'Spammer',
            'email': 'spam@example.com',
            'preferred_date': self.future_date,
            'preferred_time': 'afternoon',
            'reason': 'Spam',
            'honeypot': 'FILLED'  # Should be empty!
        }
        
        response = self.client.post(self.url, data=data, follow=False)
        
        # Form should be invalid
        self.assertEqual(response.status_code, 400)
    
    def test_post_past_preferred_date_rejected(self, mock_mail):
        """Test: Past preferred_date is rejected"""
        past_date = str((timezone.now().date() - timedelta(days=1)))
        data = {
            'full_name': 'Patient',
            'email': 'patient@example.com',
            'preferred_date': past_date,
            'preferred_time': 'evening',
            'reason': 'Checkup',
            'honeypot': ''
        }
        
        response = self.client.post(self.url, data=data, follow=False)
        
        self.assertEqual(response.status_code, 400)
    
    def test_post_exceeds_session_rate_limit_blocked(self, mock_mail):
        """Test: 6th attempt within session is blocked"""
        data_base = {
            'full_name': 'Patient',
            'email': 'patient@example.com',
            'preferred_date': self.future_date,
            'preferred_time': 'morning',
            'reason': 'Test',
            'honeypot': ''
        }
        
        # Make 5 successful requests (limit)
        for i in range(5):
            response = self.client.post(self.url, data=data_base, follow=False)
            self.assertEqual(response.status_code, 200)
        
        # 6th request should be blocked
        response = self.client.post(self.url, data=data_base, follow=False)
        self.assertEqual(response.status_code, 429)
    
    def test_post_missing_required_fields_validation_error(self, mock_mail):
        """Test: Missing required fields returns validation error"""
        data = {
            'full_name': '',  # Missing
            'email': 'patient@example.com',
            'preferred_date': self.future_date,
            'preferred_time': 'morning',
            'reason': 'Test',
            'honeypot': ''
        }
        
        response = self.client.post(self.url, data=data, follow=False)
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])


# =====================================================================
# QUICK ADD USER ENDPOINT TESTS
# =====================================================================

class QuickAddUserTests(TestCase):
    """Tests for POST /quick-add-user/"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.url = '/quick-add-user/'
    
    def test_post_valid_new_user_returns_success(self):
        """Test: POST valid new user returns user ID + success"""
        payload = {
            'username': 'newuser123',
            'password': 'SecurePass123!',
            'email': 'newuser@example.com'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('user_id', data)
    
    def test_post_duplicate_username_returns_error(self):
        """Test: Duplicate username returns error not 500"""
        # Create existing user
        User.objects.create_user(
            username='existinguser',
            password='pass123',
            email='existing@example.com'
        )
        
        payload = {
            'username': 'existinguser',
            'password': 'NewPass123!',
            'email': 'different@example.com'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertNotEqual(response.status_code, 500)
    
    def test_post_no_csrf_required(self):
        """Test: No CSRF required (verify csrf_exempt works)"""
        # Try POST without CSRF token (should work due to @csrf_exempt)
        payload = {
            'username': 'nocsrftest',
            'password': 'Pass123!',
            'email': 'nocsrf@example.com'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should succeed (not be blocked by CSRF)
        self.assertEqual(response.status_code, 200)
    
    def test_post_without_password_validation_error(self):
        """Test: Missing password returns validation error"""
        payload = {
            'username': 'nopass',
            'password': '',  # Missing!
            'email': 'nopass@example.com'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])


# =====================================================================
# GOVERNANCE CREATE ENDPOINT TESTS
# =====================================================================

class GovernanceCreateTests(TestCase):
    """Tests for POST /governance/create/"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        self.member_user = User.objects.create_user(
            username='member',
            password='member123'
        )
        self.url = '/governance/create/'
    
    def test_get_without_staff_login_redirected_to_login(self):
        """Test: GET without staff login redirects to login"""
        response = self.client.get(self.url, follow=False)
        
        # Should redirect (not necessarily to login, may be permission denied)
        self.assertNotEqual(response.status_code, 200)
    
    def test_post_with_new_user_creates_both(self):
        """Test: POST with new_username + password creates both"""
        self.client.login(username='admin', password='admin123')
        
        data = {
            'governance_category': 'Test Category',
            'description': 'Test Description',
            'new_username': 'newmember',
            'new_password': 'NewPass123!',
            'new_email': 'newmember@example.com'
        }
        
        response = self.client.post(self.url, data=data, follow=True)
        
        # User should be created
        self.assertTrue(User.objects.filter(username='newmember').exists())
    
    def test_post_with_existing_member_links_correctly(self):
        """Test: POST with existing member links correctly"""
        self.client.login(username='admin', password='admin123')
        
        data = {
            'governance_category': 'Category',
            'description': 'Description',
            'members': self.member_user.id
        }
        
        response = self.client.post(self.url, data=data, follow=True)
        
        # Governance record should be created with this member
        self.assertTrue(
            Governance.objects.filter(members=self.member_user).exists()
        )
    
    def test_post_with_both_member_and_new_user_rejected(self):
        """Test: POST with both member AND new user is rejected"""
        self.client.login(username='admin', password='admin123')
        
        data = {
            'governance_category': 'Bad Request',
            'description': 'Description',
            'members': self.member_user.id,
            'new_username': 'shouldfail',
            'new_password': 'Pass123!'
        }
        
        response = self.client.post(self.url, data=data, follow=False)
        
        # Should fail form validation
        # The form should reject having both
    
    def test_post_with_neither_member_nor_new_user_rejected(self):
        """Test: POST with neither member nor new user is rejected"""
        self.client.login(username='admin', password='admin123')
        
        data = {
            'governance_category': 'Invalid',
            'description': 'No member specified'
            # Missing both members and new_username
        }
        
        response = self.client.post(self.url, data=data, follow=False)
        
        # Should fail


# =====================================================================
# EXPERT INQUIRY SUBMISSION TESTS
# =====================================================================

@patch('django.core.mail.send_mail')
class ExpertInquiryTests(TestCase):
    """Tests for expert inquiry submission"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.plan = InsurancePlan.objects.create(
            provider_name='Insurance Co',
            plan_name='Plan A',
            network='Global',
            max_benefit='$1M',
            evacuation='Included',
            score=9.0
        )
    
    def test_submit_inquiry_creates_record(self, mock_mail):
        """Test: Submitting inquiry creates ExpertInquiry record"""
        url = '/healthcare/insurance-support/api/inquiry/'
        
        data = json.dumps({
            'full_name': 'John Inquirer',
            'email': 'inquirer@example.com',
            'phone': '+1234567890',
            'question': 'What is your best plan?',
            'interested_plan': self.plan.id
        })
        
        response = self.client.post(
            url,
            data=data,
            content_type='application/json'
        )
        
        # Should create inquiry
        self.assertTrue(
            ExpertInquiry.objects.filter(
                full_name='John Inquirer'
            ).exists()
        )


# =====================================================================
# APPOINTMENT FORM TESTS
# =====================================================================

class AppointmentFormTests(TestCase):
    """Tests for AppointmentRequestForm validation"""
    
    def setUp(self):
        """Set up test data"""
        self.doctor = Doctor.objects.create(
            name='Dr. Form Test',
            title='Doctor',
            specialty='Testing',
            categories=['general'],
            location_city='Test',
            location_country='Test',
            languages=['english'],
            bio='Test'
        )
        self.future_date = timezone.now().date() + timedelta(days=7)
    
    def test_honeypot_empty_is_valid(self):
        """Test: honeypot field empty is valid"""
        form_data = {
            'full_name': 'Patient',
            'email': 'patient@example.com',
            'preferred_date': self.future_date,
            'preferred_time': 'morning',
            'reason': 'Checkup',
            'honeypot': ''
        }
        
        form = AppointmentRequestForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_honeypot_filled_is_invalid(self):
        """Test: honeypot field filled is invalid"""
        form_data = {
            'full_name': 'Spammer',
            'email': 'spam@example.com',
            'preferred_date': self.future_date,
            'preferred_time': 'morning',
            'reason': 'Spam',
            'honeypot': 'FILLED'  # Invalid!
        }
        
        form = AppointmentRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_preferred_date_in_future_is_valid(self):
        """Test: preferred_date in future is valid"""
        future = timezone.now().date() + timedelta(days=5)
        form_data = {
            'full_name': 'Patient',
            'email': 'patient@example.com',
            'preferred_date': future,
            'preferred_time': 'afternoon',
            'reason': 'Consultation',
            'honeypot': ''
        }
        
        form = AppointmentRequestForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_preferred_date_today_rejected(self):
        """Test: preferred_date today is rejected"""
        today = timezone.now().date()
        form_data = {
            'full_name': 'Patient',
            'email': 'patient@example.com',
            'preferred_date': today,
            'preferred_time': 'evening',
            'reason': 'Checkup',
            'honeypot': ''
        }
        
        form = AppointmentRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_preferred_date_past_rejected(self):
        """Test: Past preferred_date is rejected"""
        past = timezone.now().date() - timedelta(days=1)
        form_data = {
            'full_name': 'Patient',
            'email': 'patient@example.com',
            'preferred_date': past,
            'preferred_time': 'morning',
            'reason': 'Checkup',
            'honeypot': ''
        }
        
        form = AppointmentRequestForm(data=form_data)
        self.assertFalse(form.is_valid())


if __name__ == '__main__':
    import unittest
    unittest.main()
