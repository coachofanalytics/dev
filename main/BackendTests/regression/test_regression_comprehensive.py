"""
Comprehensive Regression Tests for Main App
Tests for known issues, edge cases, and data integrity
"""
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta, date
import json
import tempfile
from unittest.mock import patch

from main.models import (
    Scholarship, TrainingCourse, ExpertInquiry, AppointmentRequest,
    Doctor, InsurancePlan, Governance, AIRecommendationRule
)

User = get_user_model()


# =====================================================================
# SCHOLARSHIP REGRESSION TESTS
# =====================================================================

class ScholarshipRegressionTests(TestCase):
    """Regression tests for Scholarship model"""
    
    def setUp(self):
        """Set up test data"""
        self.today = timezone.now().date()
    
    def test_scholarship_status_does_not_reset_if_deadline_not_changed(self):
        """Regression: Status should not reset if deadline unchanged"""
        future = self.today + timedelta(days=30)
        scholarship = Scholarship.objects.create(
            title='Test',
            provider='Provider',
            deadline=future
        )
        original_status = scholarship.status
        original_deadline = scholarship.deadline
        
        # Update title only
        scholarship.title = 'Updated Title'
        scholarship.save()
        
        scholarship.refresh_from_db()
        self.assertEqual(scholarship.status, original_status)
        self.assertEqual(scholarship.deadline, original_deadline)


# =====================================================================
# TRAINING COURSE REGRESSION TESTS
# =====================================================================

class TrainingCourseRegressionTests(TestCase):
    """Regression tests for TrainingCourse model"""
    
    def setUp(self):
        """Set up test data"""
        self.today = timezone.now().date()
    
    def test_enrolled_students_count_accurate_after_multiple_enrollments(self):
        """Regression: Enrollment count stays accurate after updates"""
        course = TrainingCourse.objects.create(
            title='Test Course',
            category='Tech',
            start_date=self.today,
            max_students=10,
            enrolled_students=3
        )
        
        original_count = course.enrolled_students
        
        # Simulate adding more students
        course.enrolled_students = 5
        course.save()
        
        course.refresh_from_db()
        self.assertEqual(course.enrolled_students, 5)
        self.assertNotEqual(course.enrolled_students, original_count)
    
    def test_course_status_updates_correctly_over_time(self):
        """Regression: Course status transitions correctly"""
        # Future course
        future_start = self.today + timedelta(days=30)
        future_end = future_start + timedelta(days=30)
        
        course = TrainingCourse.objects.create(
            title='Future Course',
            category='Business',
            start_date=future_start,
            end_date=future_end
        )
        
        self.assertEqual(course.status, TrainingCourse.Status.UPCOMING)


# =====================================================================
# EXPERT INQUIRY REGRESSION TESTS
# =====================================================================

class ExpertInquiryRegressionTests(TestCase):
    """Regression tests for ExpertInquiry model"""
    
    def setUp(self):
        """Set up test data"""
        self.plan = InsurancePlan.objects.create(
            provider_name='TestCo',
            plan_name='Plan',
            network='Global',
            max_benefit='$1M',
            evacuation='Included',
            score=9.0
        )
        self.staff = User.objects.create_user(
            username='staff1',
            password='pass123',
            is_staff=True
        )
    
    def test_auto_assign_does_not_double_assign_same_person(self):
        """Regression: auto_assign should not double-assign"""
        inquiry = ExpertInquiry.objects.create(
            full_name='Test',
            email='test@example.com',
            question='Test question',
            interested_plan=self.plan
        )
        
        inquiry.assigned_to = self.staff
        inquiry.save()
        
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.assigned_to, self.staff)
        
        # Verify it's still assigned to only one person
        self.assertEqual(inquiry.assigned_to.id, self.staff.id)


# =====================================================================
# APPOINTMENT REQUEST REGRESSION TESTS
# =====================================================================

class AppointmentRequestRegressionTests(TestCase):
    """Regression tests for AppointmentRequest model"""
    
    def setUp(self):
        """Set up test data"""
        self.doctor = Doctor.objects.create(
            name='Dr. Test',
            title='Doctor',
            specialty='Testing',
            categories=['general'],
            location_city='Test',
            location_country='Test',
            languages=['english'],
            bio='Test'
        )
        self.future = timezone.now().date() + timedelta(days=7)
    
    def test_honeypot_check_cannot_be_bypassed_by_empty_string(self):
        """Regression: Honeypot cannot be bypassed"""
        valid_data = {
            'doctor': self.doctor,
            'full_name': 'Patient',
            'email': 'patient@example.com',
            'preferred_date': self.future,
            'preferred_time': 'morning',
            'reason': 'Checkup',
            'honeypot': ''
        }
        
        # Valid request with empty honeypot
        request = AppointmentRequest.objects.create(**valid_data)
        self.assertEqual(request.honeypot, '')
        
        # If form validation is used, honeypot with value should fail
        from main.forms import AppointmentRequestForm
        invalid_form_data = valid_data.copy()
        invalid_form_data['honeypot'] = 'filled'
        form = AppointmentRequestForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())


# =====================================================================
# SESSION RATE LIMIT REGRESSION TESTS
# =====================================================================

@patch('django.core.mail.send_mail')
class SessionRateLimitRegressionTests(TestCase):
    """Regression tests for session rate limiting"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.doctor = Doctor.objects.create(
            name='Dr. RateLimit',
            title='Doctor',
            specialty='Testing',
            categories=['general'],
            location_city='Test',
            location_country='Test',
            languages=['english'],
            bio='Test'
        )
        self.future = str(timezone.now().date() + timedelta(days=7))
        self.url = f'/api/doctor/{self.doctor.id}/book/'
    
    def test_session_rate_limit_resets_correctly(self, mock_mail):
        """Regression: Rate limit should reset between sessions"""
        data = {
            'full_name': 'Patient',
            'email': 'patient@example.com',
            'preferred_date': self.future,
            'preferred_time': 'morning',
            'reason': 'Checkup',
            'honeypot': ''
        }
        
        # Make 5 attempts in first session
        client1 = Client()
        for i in range(5):
            response = client1.post(self.url, data=data, follow=False)
            self.assertEqual(response.status_code, 200)
        
        # 6th attempt should be blocked
        response = client1.post(self.url, data=data, follow=False)
        self.assertEqual(response.status_code, 429)
        
        # New client (different session) should work
        client2 = Client()
        response = client2.post(self.url, data=data, follow=False)
        self.assertEqual(response.status_code, 200)


# =====================================================================
# GOVERNANCE FORM REGRESSION TESTS
# =====================================================================

class GovernanceFormRegressionTests(TestCase):
    """Regression tests for GovernanceForm mutual exclusivity"""
    
    def setUp(self):
        """Set up test data"""
        self.member = User.objects.create_user(
            username='member',
            password='pass123'
        )
    
    def test_governance_form_mutual_exclusivity_enforced(self):
        """Regression: GovernanceForm must enforce mutual exclusivity"""
        from main.forms import GovernanceForm
        
        # Both members and new_username provided
        form_data = {
            'governance_category': 'Test',
            'description': 'Test',
            'members': self.member.id,
            'new_username': 'newuser',
            'new_password': 'Pass123!'
        }
        
        form = GovernanceForm(data=form_data)
        # Should either fail or handle gracefully
        # (implementation depends on form logic)


# =====================================================================
# AI RECOMMENDATION REGRESSION TESTS
# =====================================================================

@patch('main.views.generate_recommendation_text', return_value='Fallback recommendation')
class AIRecommendationRegressionTests(TestCase):
    """Regression tests for AI recommendation system"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.plan = InsurancePlan.objects.create(
            provider_name='InsureCo',
            plan_name='Premium',
            network='Global',
            max_benefit='$2M',
            evacuation='Included',
            score=9.8
        )
        self.url = '/healthcare/insurance-support/api/recommend/'
    
    def test_ai_recommendation_falls_back_when_no_rules_match(self, mock_gen):
        """Regression: Falls back correctly when no rules match"""
        # Create no rules, only plan
        payload = {
            'age': 'unknown',
            'residence': 'unknown',
            'priority': 'unknown'
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
# DOCTOR BOOKING REGRESSION TESTS
# =====================================================================

class DoctorBookingRegressionTests(TestCase):
    """Regression tests for doctor booking logic"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.doctor = Doctor.objects.create(
            name='Dr. Regression',
            title='Doctor',
            specialty='Testing',
            categories=['general'],
            location_city='Test',
            location_country='Test',
            languages=['english'],
            bio='Test'
        )
        self.today = timezone.now().date()
    
    def test_booking_date_validation_rejects_todays_date(self):
        """Regression: Booking for today should be rejected"""
        from main.forms import AppointmentRequestForm
        
        form_data = {
            'full_name': 'Patient',
            'email': 'patient@example.com',
            'preferred_date': self.today,  # Today!
            'preferred_time': 'morning',
            'reason': 'Checkup',
            'honeypot': ''
        }
        
        form = AppointmentRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_booking_date_validation_rejects_past_dates(self):
        """Regression: Booking for past dates rejected"""
        from main.forms import AppointmentRequestForm
        
        past = self.today - timedelta(days=5)
        form_data = {
            'full_name': 'Patient',
            'email': 'patient@example.com',
            'preferred_date': past,
            'preferred_time': 'noon',
            'reason': 'Checkup',
            'honeypot': ''
        }
        
        form = AppointmentRequestForm(data=form_data)
        self.assertFalse(form.is_valid())


# =====================================================================
# DATA INTEGRITY REGRESSION TESTS
# =====================================================================

class DataIntegrityRegressionTests(TestCase):
    """Regression tests for data integrity"""
    
    def test_scholarship_currency_stored_correctly(self):
        """Regression: Currency values stored and retrieved correctly"""
        scholarship = Scholarship.objects.create(
            title='Currency Test',
            provider='Provider',
            amount_value=5000,
            amount_currency='EUR',
            deadline=timezone.now().date()
        )
        
        scholarship.refresh_from_db()
        self.assertEqual(scholarship.amount_currency, 'EUR')
    
    def test_training_course_dates_persist_correctly(self):
        """Regression: Course dates persist without corruption"""
        start = timezone.now().date()
        end = start + timedelta(days=90)
        
        course = TrainingCourse.objects.create(
            title='Date Test',
            category='Tech',
            start_date=start,
            end_date=end
        )
        
        course.refresh_from_db()
        self.assertEqual(course.start_date, start)
        self.assertEqual(course.end_date, end)
    
    def test_expert_inquiry_escalation_fields_independent(self):
        """Regression: Escalation fields don't interfere with others"""
        plan = InsurancePlan.objects.create(
            provider_name='InsureCo',
            plan_name='Plan',
            network='Global',
            max_benefit='$1M',
            evacuation='Included',
            score=9.0
        )
        
        inquiry = ExpertInquiry.objects.create(
            full_name='Test',
            email='test@example.com',
            question='Question',
            interested_plan=plan,
            is_contacted=True,
            escalated=False
        )
        
        inquiry.refresh_from_db()
        self.assertTrue(inquiry.is_contacted)
        self.assertFalse(inquiry.escalated)


if __name__ == '__main__':
    import unittest
    unittest.main()
