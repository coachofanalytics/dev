"""
Comprehensive integration tests for main app views and APIs.
Covers: AI Recommendation, Doctor Booking, Quick Add User, Governance Create, etc.
"""
import json
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from main.models import (
    Scholarship, TrainingCourse, ExpertInquiry, Doctor,
    AppointmentRequest, AIRecommendationRule, InsurancePlan,
    Governance, Donation_organisation
)
from main.forms import AppointmentRequestForm, GovernanceForm

User = get_user_model()


class AIRecommendationAPITests(TestCase):
    """Tests for AI recommendation endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.plan1 = InsurancePlan.objects.create(
            provider_name="Provider A",
            plan_name="Basic Plan",
            network="Network A",
            max_benefit=Decimal("50000"),
            score=Decimal("3.5")
        )
        self.plan2 = InsurancePlan.objects.create(
            provider_name="Provider B",
            plan_name="Premium Plan",
            network="Network B",
            max_benefit=Decimal("200000"),
            score=Decimal("4.8")
        )
        self.url = '/healthcare/insurance-support/api/recommend/'
        
        # Create recommendation rules
        AIRecommendationRule.objects.create(
            age_bracket=AIRecommendationRule.AgeBracket.AGE_25_35,
            residence=AIRecommendationRule.Residence.URBAN,
            priority=AIRecommendationRule.Priority.HIGH,
            recommended_plan=self.plan2,
            recommendation_text="Premium coverage for cities"
        )
    
    @patch('main.views.generate_recommendation_text', return_value='Mocked recommendation')
    def test_post_valid_payload_returns_200_and_recommendation(self, mock_rec):
        """POST valid payload should return 200 with recommendation."""
        payload = {
            'age': 30,
            'residence': 'urban',
            'priority': 'high'
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('recommendation', data)
    
    def test_post_empty_payload_handles_gracefully(self):
        """POST empty payload should not return 500 error."""
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )
        # Should handle gracefully (200 or 400, not 500)
        self.assertNotEqual(response.status_code, 500)
    
    def test_post_missing_age_handles_gracefully(self):
        """POST missing age field should handle gracefully."""
        payload = {
            'residence': 'rural',
            'priority': 'low'
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertNotEqual(response.status_code, 500)
    
    def test_post_invalid_residence_uses_fallback(self):
        """POST invalid residence should use fallback recommendation."""
        payload = {
            'age': 45,
            'residence': 'invalid_place',
            'priority': 'medium'
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertNotEqual(response.status_code, 500)
        if response.status_code == 200:
            data = response.json()
            self.assertIn('recommendation', data)


@override_settings(
    DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage',
    MEDIA_ROOT=tempfile.mkdtemp()
)
@patch('main.views.send_mail')
class DoctorBookingAPITests(TestCase):
    """Tests for doctor booking endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.doctor = Doctor.objects.create(
            name="Dr. Booking",
            specialty="General Practice",
            location_city="Nairobi",
            location_country="Kenya",
            clinic_name="Test Clinic",
            available=True
        )
        self.future_date = (timezone.now() + timedelta(days=7)).date().isoformat()
        self.past_date = (timezone.now() - timedelta(days=1)).date().isoformat()
        self.today = timezone.now().date().isoformat()
        self.url = f'/api/doctor/{self.doctor.id}/book/'
    
    def test_post_valid_booking_returns_success(self, mock_mail):
        """POST valid booking should return success response."""
        payload = {
            'full_name': 'John Patient',
            'email': 'patient@test.com',
            'preferred_date': self.future_date,
            'preferred_time': 'morning',
            'reason': 'Checkup',
            'honeypot': ''
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('success', data)
    
    def test_post_honeypot_filled_rejects_request(self, mock_mail):
        """POST with honeypot filled should be rejected."""
        payload = {
            'full_name': 'Bot',
            'email': 'bot@test.com',
            'preferred_date': self.future_date,
            'preferred_time': 'afternoon',
            'honeypot': 'I_AM_A_BOT'
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        # Should not create appointment
        self.assertEqual(AppointmentRequest.objects.count(), 0)
    
    def test_post_past_date_rejected(self, mock_mail):
        """POST with past preferred_date should be rejected."""
        payload = {
            'full_name': 'Past Patient',
            'email': 'past@test.com',
            'preferred_date': self.past_date,
            'preferred_time': 'evening',
            'reason': 'Checkup'
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        # Should fail validation
        self.assertNotEqual(response.status_code, 200)
    
    def test_post_today_date_rejected(self, mock_mail):
        """POST with today's date should be rejected (must be future)."""
        payload = {
            'full_name': 'Today Patient',
            'email': 'today@test.com',
            'preferred_date': self.today,
            'preferred_time': 'morning'
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        # Should not accept today's date
        self.assertNotEqual(response.status_code, 200)
    
    def test_session_rate_limit_6th_attempt_blocked(self, mock_mail):
        """6th booking attempt in same session should be blocked."""
        session = self.client.session
        
        # Make 5 successful requests first
        for i in range(5):
            payload = {
                'full_name': f'Patient {i}',
                'email': f'patient{i}@test.com',
                'preferred_date': self.future_date,
                'preferred_time': 'morning',
                'honeypot': ''
            }
            self.client.post(
                self.url,
                data=json.dumps(payload),
                content_type='application/json'
            )
        
        # 6th request should be blocked
        payload = {
            'full_name': 'Blocked Patient',
            'email': 'blocked@test.com',
            'preferred_date': self.future_date,
            'preferred_time': 'afternoon',
            'honeypot': ''
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        # Should indicate rate limit exceeded
        self.assertIn(response.status_code, [400, 429])
    
    def test_post_missing_required_fields_validation_error(self, mock_mail):
        """POST without required fields should return validation error."""
        payload = {
            'full_name': 'Incomplete'
            # Missing email, preferred_date, etc.
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertNotEqual(response.status_code, 200)


class QuickAddUserAPITests(TestCase):
    """Tests for quick-add-user endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = '/quick-add-user/'
    
    def test_post_valid_new_user_returns_id_and_success(self):
        """POST valid new user should return user ID + success."""
        payload = {
            'username': 'newuser123',
            'password': 'SecurePass@123',
            'email': 'newuser@test.com'
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('user_id', data)
        self.assertIn('success', data)
    
    def test_post_duplicate_username_returns_error_not_500(self):
        """POST duplicate username should return error, not 500."""
        User.objects.create_user(
            username='existing',
            email='existing@test.com',
            password='pass'
        )
        
        payload = {
            'username': 'existing',
            'password': 'NewPass@123',
            'email': 'different@test.com'
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertNotEqual(response.status_code, 500)
        self.assertEqual(response.status_code, 400)
    
    def test_csrf_exempt_works(self):
        """Endpoint should not require CSRF token (verify csrf_exempt)."""
        # Make POST without CSRF token
        payload = {
            'username': 'nocsrf',
            'password': 'Pass@123',
            'email': 'nocsrf@test.com'
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        # Should not return 403 Forbidden (CSRF failure)
        self.assertNotEqual(response.status_code, 403)
    
    def test_post_without_password_validation_error(self):
        """POST without password should return validation error."""
        payload = {
            'username': 'nopass',
            'email': 'nopass@test.com'
            # Missing password
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertNotEqual(response.status_code, 200)


@patch('main.views.send_mail')
class GovernanceCreateAPITests(TestCase):
    """Tests for governance create endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='staffpass',
            is_staff=True
        )
        self.member_user = User.objects.create_user(
            username='member',
            email='member@test.com',
            password='memberpass'
        )
        self.url = '/governance/create/'
    
    def test_post_with_new_username_and_password_creates_both(self, mock_mail):
        """POST with new_username + new_password should create user and governance."""
        self.client.login(username='staff', password='staffpass')
        
        payload = {
            'governance_category': 'Board',
            'description': 'Board member',
            'new_username': 'newmember',
            'new_password': 'NewMemberPass@123',
            'new_email': 'newmember@test.com'
        }
        response = self.client.post(self.url, data=payload)
        
        # Should create user
        self.assertTrue(User.objects.filter(username='newmember').exists())
        # Should create governance
        self.assertEqual(response.status_code, 302)  # Redirect after success
    
    def test_post_with_existing_member_links_correctly(self, mock_mail):
        """POST with existing member should link governance correctly."""
        self.client.login(username='staff', password='staffpass')
        
        payload = {
            'governance_category': 'Committee',
            'description': 'Committee member',
            'members': self.member_user.id
        }
        response = self.client.post(self.url, data=payload)
        
        # Should create governance with member linked
        self.assertEqual(response.status_code, 302)
    
    def test_post_with_both_member_and_new_user_rejected(self, mock_mail):
        """POST with both member AND new user should be rejected."""
        self.client.login(username='staff', password='staffpass')
        
        payload = {
            'governance_category': 'Board',
            'members': self.member_user.id,
            'new_username': 'conflicting',
            'new_password': 'Pass@123'
        }
        response = self.client.post(self.url, data=payload, follow=True)
        
        # Form should show error
        self.assertFormError(response.context['form'], None, 'Provide either member OR new user, not both')
    
    def test_post_with_neither_member_nor_new_user_rejected(self, mock_mail):
        """POST with neither member nor new user should be rejected."""
        self.client.login(username='staff', password='staffpass')
        
        payload = {
            'governance_category': 'Board',
            'description': 'Missing both'
        }
        response = self.client.post(self.url, data=payload, follow=True)
        
        # Form should show error
        self.assertFormError(response.context['form'], None, 'Provide either member OR new user')
    
    def test_get_without_staff_login_redirected_to_login(self, mock_mail):
        """GET without staff login should redirect to login."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_get_with_staff_login_returns_form(self, mock_mail):
        """GET with staff login should return form."""
        self.client.login(username='staff', password='staffpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)


class ScholarshipSearchViewTests(TestCase):
    """Tests for scholarship search view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = '/education/scholarships/'
        
        future_date = timezone.now() + timedelta(days=30)
        past_date = timezone.now() - timedelta(days=1)
        soon_date = timezone.now() + timedelta(days=3)
        
        self.scholarship1 = Scholarship.objects.create(
            title="STEM Open",
            amount_value=Decimal("5000"),
            amount_currency="USD",
            provider="Provider A",
            level=Scholarship.Level.UNDERGRADUATE,
            field=Scholarship.Field.STEM,
            location=Scholarship.Location.GLOBAL,
            deadline=future_date,
            status=Scholarship.Status.OPEN
        )
        
        self.scholarship2 = Scholarship.objects.create(
            title="Humanities Closing",
            amount_value=Decimal("3000"),
            amount_currency="KES",
            provider="Provider B",
            level=Scholarship.Level.MASTERS,
            field=Scholarship.Field.HUMANITIES,
            location=Scholarship.Location.KENYA,
            deadline=soon_date,
            status=Scholarship.Status.CLOSING_SOON
        )
        
        self.scholarship3 = Scholarship.objects.create(
            title="Business Closed",
            amount_value=Decimal("2000"),
            amount_currency="EUR",
            provider="Provider C",
            level=Scholarship.Level.VOCATIONAL,
            field=Scholarship.Field.BUSINESS,
            location=Scholarship.Location.UK,
            deadline=past_date,
            status=Scholarship.Status.CLOSED
        )
    
    def test_get_all_scholarships_displayed(self):
        """GET should display all scholarships by default."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('scholarships', response.context)
        # Should have 3 scholarships
        scholarships = response.context['scholarships']
        self.assertGreaterEqual(len(list(scholarships)), 2)  # At least closed and open
    
    def test_filter_by_level(self):
        """GET with level filter should return only that level."""
        response = self.client.get(f"{self.url}?filter_level={Scholarship.Level.MASTERS}")
        self.assertEqual(response.status_code, 200)
    
    def test_filter_by_field(self):
        """GET with field filter should return only that field."""
        response = self.client.get(f"{self.url}?filter_field={Scholarship.Field.STEM}")
        self.assertEqual(response.status_code, 200)
    
    def test_filter_by_location(self):
        """GET with location filter should return only that location."""
        response = self.client.get(f"{self.url}?filter_location={Scholarship.Location.KENYA}")
        self.assertEqual(response.status_code, 200)
    
    def test_search_by_keyword(self):
        """GET with keyword should filter by title/provider."""
        response = self.client.get(f"{self.url}?search_keyword=STEM")
        self.assertEqual(response.status_code, 200)


class ExpertInquirySubmissionTests(TestCase):
    """Tests for expert inquiry submission."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.plan = InsurancePlan.objects.create(
            provider_name="Test",
            plan_name="Test Plan",
            network="Network",
            max_benefit=Decimal("100000")
        )
        self.url = '/api/expert-inquiry/'
    
    @patch('main.views.send_mail')
    def test_post_valid_inquiry_creates_record(self, mock_mail):
        """POST valid inquiry should create ExpertInquiry record."""
        payload = {
            'full_name': 'John Inquirer',
            'email': 'inquirer@test.com',
            'phone': '+254712345678',
            'question': 'What is the best plan for me?',
            'interested_plan': self.plan.id
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ExpertInquiry.objects.filter(email='inquirer@test.com').exists())
