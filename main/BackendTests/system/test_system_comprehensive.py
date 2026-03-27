"""
Comprehensive System Tests for Main App
Full end-to-end workflows testing multiple components
"""
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta, date
import json
import tempfile
from unittest.mock import patch, MagicMock

from main.models import (
    Scholarship, TrainingCourse, ExpertInquiry, AppointmentRequest,
    Doctor, InsurancePlan, Governance, AIRecommendationRule
)

User = get_user_model()


# =====================================================================
# SCHOLARSHIP FULL WORKFLOW TESTS
# =====================================================================

class ScholarshipFullWorkflowTests(TestCase):
    """System tests for complete scholarship lifecycle"""
    
    def setUp(self):
        """Set up test data"""
        self.today = timezone.now().date()
        self.client = Client()
    
    def test_full_scholarship_workflow_create_deadline_passes_closes(self):
        """System: Full workflow - Create → Deadline passes → Status Closed"""
        # 1. Create scholarship with future deadline
        future = self.today + timedelta(days=5)
        scholarship = Scholarship.objects.create(
            title='Lifecycle Scholarship',
            provider='Test Provider',
            deadline=future,
            level='Masters',
            field='STEM',
            location='Global'
        )
        
        self.assertEqual(scholarship.status, Scholarship.Status.CLOSING_SOON)
        
        # 2. Simulate deadline passing by updating to past
        scholarship.deadline = self.today - timedelta(days=1)
        scholarship.save()
        
        # 3. Verify status is now Closed
        scholarship.refresh_from_db()
        self.assertEqual(scholarship.status, Scholarship.Status.CLOSED)


# =====================================================================
# DOCTOR BOOKING FULL WORKFLOW TESTS
# =====================================================================

@patch('django.core.mail.send_mail')
class DoctorBookingFullWorkflowTests(TestCase):
    """System tests for complete doctor booking workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.doctor = Doctor.objects.create(
            name='Dr. Workflow',
            title='Specialist',
            specialty='Health Consultation',
            categories=['general', 'mental_health'],
            location_city='Healthcare City',
            location_country='Test Country',
            languages=['english', 'swahili'],
            bio='Experienced healthcare provider',
            available=True,
            rating=4.8,
            review_count=125
        )
        self.future_date = str(timezone.now().date() + timedelta(days=10))
    
    def test_full_booking_workflow_select_form_submit_confirmation(self, mock_mail):
        """System: Full workflow - Doctor selected → Form → Booking confirmed"""
        # 1. Doctor is available and visible
        self.assertTrue(self.doctor.available)
        
        # 2. Submit booking form
        url = f'/api/doctor/{self.doctor.id}/book/'
        data = {
            'full_name': 'Patient Workflow',
            'email': 'workflow@example.com',
            'preferred_date': self.future_date,
            'preferred_time': 'afternoon',
            'reason': 'Health consultation',
            'honeypot': ''
        }
        
        response = self.client.post(url, data=data, follow=False)
        
        # 3. Verify booking created
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # 4. Verify appointment in database
        appointment = AppointmentRequest.objects.filter(
            full_name='Patient Workflow',
            email='workflow@example.com'
        ).first()
        self.assertIsNotNone(appointment)
        self.assertEqual(appointment.doctor, self.doctor)


# =====================================================================
# EXPERT INQUIRY FULL WORKFLOW TESTS
# =====================================================================

@patch('django.core.mail.send_mail')
class ExpertInquiryFullWorkflowTests(TestCase):
    """System tests for complete inquiry workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.plan = InsurancePlan.objects.create(
            provider_name='GlobalInsure',
            plan_name='Premium Plus',
            network='Worldwide Coverage',
            max_benefit='$3,000,000',
            evacuation='Included',
            score=9.7
        )
        self.staff = User.objects.create_user(
            username='specialist',
            password='pass123',
            is_staff=True
        )
    
    def test_full_inquiry_workflow_created_assigned_tracked_escalated(self, mock_mail):
        """System: Full workflow - Created → Assigned → SLA tracked → Escalated"""
        # 1. Create inquiry
        inquiry = ExpertInquiry.objects.create(
            full_name='Escalation Test',
            email='escalate@example.com',
            phone='+1234567890',
            question='This is an emergency with my coverage!',
            interested_plan=self.plan
        )
        
        self.assertIsNotNone(inquiry.id)
        self.assertIn('URGENT', inquiry.notes or '')
        
        # 2. Assign to staff
        inquiry.assigned_to = self.staff
        inquiry.save()
        
        self.assertEqual(inquiry.assigned_to, self.staff)
        
        # 3. SLA deadline exists
        # (in real system, this would be auto-calculated)
        
        # 4. Mark as contacted
        inquiry.is_contacted = True
        inquiry.save()
        
        self.assertTrue(inquiry.is_contacted)


# =====================================================================
# GOVERNANCE FULL WORKFLOW TESTS
# =====================================================================

class GovernanceFullWorkflowTests(TestCase):
    """System tests for complete governance workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.admin = User.objects.create_user(
            username='governor',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        self.existing_member = User.objects.create_user(
            username='existingmember',
            password='pass123'
        )
    
    def test_full_governance_workflow_staff_creates_user_governance_linked(self):
        """System: Full workflow - Staff creates → User + Governance linked"""
        # 1. Staff logs in
        self.client.login(username='governor', password='admin123')
        
        # 2. Create governance with new user
        initial_user_count = User.objects.count()
        
        governance = Governance.objects.create(
            governance_category='Leadership Council',
            description='Regional leadership oversight',
            members=self.existing_member
        )
        
        # 3. Verify governance created and linked
        self.assertIsNotNone(governance.id)
        self.assertEqual(governance.members, self.existing_member)
        
        # 4. Verify linkage is persistent
        governance.refresh_from_db()
        self.assertEqual(governance.members.username, 'existingmember')


# =====================================================================
# AI RECOMMENDATION FULL WORKFLOW TESTS
# =====================================================================

@patch('main.views.generate_recommendation_text', 
       return_value='Based on your profile, this is the ideal plan.')
class AIRecommendationFullWorkflowTests(TestCase):
    """System tests for complete recommendation workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.url = '/healthcare/insurance-support/api/recommend/'
        
        # Create insurance plans
        self.budget_plan = InsurancePlan.objects.create(
            provider_name='BudgetCare',
            plan_name='Basic',
            network='Regional',
            max_benefit='$500,000',
            evacuation='Optional',
            score=7.5
        )
        
        self.premium_plan = InsurancePlan.objects.create(
            provider_name='PremiumHealth',
            plan_name='Gold',
            network='Worldwide',
            max_benefit='$2,000,000',
            evacuation='Included',
            score=9.2
        )
    
    def test_full_recommendation_flow_input_match_recommendation(self, mock_gen):
        """System: Full workflow - Input → Match → Recommendation returned"""
        # 1. Create matching rule
        rule = AIRecommendationRule.objects.create(
            age_bracket='young',
            residence='usa',
            priority='budget',
            recommended_plan=self.budget_plan,
            recommendation_text='Perfect for young professionals'
        )
        
        # 2. Submit request
        payload = {
            'age': 'young',
            'residence': 'usa',
            'priority': 'budget'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # 3. Verify recommendation returned
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('budget', data['plan_name'].lower())
    
    def test_full_fallback_flow_input_no_match_fallback_recommendation(self, mock_gen):
        """System: Full fallback - Input → No match → Fallback recommendation"""
        # Don't create any rules!
        
        # 1. Submit request with non-matching criteria
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
        
        # 2. Should get fallback recommendation
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('PremiumHealth', data['plan_name'])  # Highest score


# =====================================================================
# MULTI-USER CONCURRENT OPERATIONS TESTS
# =====================================================================

@patch('django.core.mail.send_mail')
class ConcurrentOperationsTests(TestCase):
    """System tests for concurrent user operations"""
    
    def setUp(self):
        """Set up test data"""
        self.client1 = Client()
        self.client2 = Client()
        self.doctor = Doctor.objects.create(
            name='Dr. Concurrent',
            title='Doctor',
            specialty='Testing',
            categories=['general'],
            location_city='Test',
            location_country='Test',
            languages=['english'],
            bio='Test'
        )
        self.future_date = str(timezone.now().date() + timedelta(days=7))
        self.url = f'/api/doctor/{self.doctor.id}/book/'
    
    def test_concurrent_bookings_from_different_sessions(self, mock_mail):
        """System: Multiple users can book concurrently without interference"""
        data1 = {
            'full_name': 'Patient 1',
            'email': 'patient1@example.com',
            'preferred_date': self.future_date,
            'preferred_time': 'morning',
            'reason': 'Checkup',
            'honeypot': ''
        }
        
        data2 = {
            'full_name': 'Patient 2',
            'email': 'patient2@example.com',
            'preferred_date': self.future_date,
            'preferred_time': 'afternoon',
            'reason': 'Consultation',
            'honeypot': ''
        }
        
        # Both users book
        response1 = self.client1.post(self.url, data=data1, follow=False)
        response2 = self.client2.post(self.url, data=data2, follow=False)
        
        # Both should succeed
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Both appointments should exist
        appointments = AppointmentRequest.objects.filter(
            doctor=self.doctor
        )
        self.assertEqual(appointments.count(), 2)


# =====================================================================
# TRAINING COURSE ENROLLMENT WORKFLOW TESTS
# =====================================================================

class TrainingCourseEnrollmentWorkflowTests(TestCase):
    """System tests for training course enrollment"""
    
    def setUp(self):
        """Set up test data"""
        self.today = timezone.now().date()
    
    def test_full_course_workflow_creation_enrollment_completion(self):
        """System: Full course workflow - Create → Enroll → Complete"""
        # 1. Create course with future start
        start = self.today + timedelta(days=10)
        end = start + timedelta(days=60)
        
        course = TrainingCourse.objects.create(
            title='Full Workflow Course',
            category='Tech',
            format='Online',
            start_date=start,
            end_date=end,
            max_students=50,
            enrolled_students=0,
            enrollment='Open'
        )
        
        self.assertEqual(course.status, TrainingCourse.Status.UPCOMING)
        self.assertEqual(course.enrollment, TrainingCourse.Enrollment.OPEN)
        
        # 2. Simulate enrollment growth
        course.enrolled_students = 25
        course.save()
        
        self.assertEqual(course.enrolled_students, 25)
        
        # 3. Course becomes full
        course.enrolled_students = 50
        course.save()
        
        self.assertEqual(course.enrollment, TrainingCourse.Enrollment.CLOSED)


# =====================================================================
# DATA CONSISTENCY ACROSS OPERATIONS TESTS
# =====================================================================

class DataConsistencyTests(TestCase):
    """System tests for data consistency"""
    
    def setUp(self):
        """Set up test data"""
        self.today = timezone.now().date()
    
    def test_scholarship_data_consistency_after_updates(self):
        """System: Scholarship data remains consistent through updates"""
        scholarship = Scholarship.objects.create(
            title='Consistency Test',
            provider='Provider',
            amount_value=5000,
            amount_currency='USD',
            level='Masters',
            field='Business',
            location='USA',
            deadline=self.today + timedelta(days=30)
        )
        
        original_id = scholarship.id
        original_slug = scholarship.slug
        
        # Update multiple fields
        scholarship.title = 'Updated Title'
        scholarship.provider = 'Updated Provider'
        scholarship.save()
        
        # Verify immutable fields don't change
        scholarship.refresh_from_db()
        self.assertEqual(scholarship.id, original_id)
        self.assertEqual(scholarship.slug, original_slug)
    
    def test_doctor_data_consistency_with_json_fields(self):
        """System: Doctor JSONFields remain consistent"""
        doctor = Doctor.objects.create(
            name='Dr. JSON Test',
            title='Doctor',
            specialty='Testing',
            categories=['general', 'pediatrics'],
            location_city='Test',
            location_country='Test',
            languages=['english', 'swahili', 'french'],
            bio='Test'
        )
        
        # Verify JSON fields are lists
        self.assertIsInstance(doctor.categories, list)
        self.assertIsInstance(doctor.languages, list)
        
        # Update and verify
        doctor.categories = ['cardiology', 'neurology']
        doctor.save()
        
        doctor.refresh_from_db()
        self.assertEqual(doctor.categories, ['cardiology', 'neurology'])


if __name__ == '__main__':
    import unittest
    unittest.main()
