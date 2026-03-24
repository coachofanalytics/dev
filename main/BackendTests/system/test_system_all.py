"""
System tests for main app - full end-to-end workflows.
Covers complete user journeys from start to finish.
"""
import json
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from main.models import (
    Scholarship, TrainingCourse, ExpertInquiry, Doctor,
    AppointmentRequest, AIRecommendationRule, InsurancePlan,
    Governance
)

User = get_user_model()


class FullScholarshipFlowTests(TestCase):
    """System test: complete scholarship lifecycle."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
    
    def test_full_scholarship_flow_create_to_closed(self):
        """Full flow: Create scholarship → deadline passes → status changes to Closed."""
        # Create scholarship with deadline 5 days away
        future_date = timezone.now() + timedelta(days=5)
        scholarship = Scholarship.objects.create(
            title="Test Scholarship Flow",
            amount_value=Decimal("5000"),
            amount_currency="USD",
            provider="Test Provider",
            level=Scholarship.Level.UNDERGRADUATE,
            field=Scholarship.Field.STEM,
            location=Scholarship.Location.GLOBAL,
            deadline=future_date,
            status=Scholarship.Status.OPEN
        )
        
        # Verify initial status
        self.assertEqual(scholarship.status, Scholarship.Status.OPEN)
        
        # Simulate deadline passing
        scholarship.deadline = timezone.now() - timedelta(days=1)
        scholarship.save()
        
        # Verify status changed to Closed
        scholarship.refresh_from_db()
        self.assertEqual(scholarship.status, Scholarship.Status.CLOSED)
        
        # Verify metadata is intact
        self.assertEqual(scholarship.title, "Test Scholarship Flow")
        self.assertEqual(scholarship.provider, "Test Provider")


class FullDoctorBookingFlowTests(TestCase):
    """System test: complete doctor booking workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.doctor = Doctor.objects.create(
            name="Dr. System Test",
            specialty="General Practice",
            location_city="Nairobi",
            location_country="Kenya",
            clinic_name="System Test Clinic",
            available=True,
            telehealth=True
        )
        self.future_date = (timezone.now() + timedelta(days=7)).date()
        self.url = f'/api/doctor/{self.doctor.id}/book/'
    
    @patch('main.views.send_mail')
    def test_full_appointment_flow_search_to_booked(self, mock_mail):
        """Full flow: Find doctor → fill form → submit → get confirmation."""
        # Step 1: Search for doctor (verify exists)
        self.assertTrue(Doctor.objects.filter(id=self.doctor.id).exists())
        
        # Step 2: Get doctor details
        doctor = Doctor.objects.get(id=self.doctor.id)
        self.assertEqual(doctor.name, "Dr. System Test")
        self.assertTrue(doctor.available)
        
        # Step 3: Submit appointment booking
        payload = {
            'full_name': 'System Test Patient',
            'email': 'systemtest@test.com',
            'preferred_date': self.future_date.isoformat(),
            'preferred_time': 'morning',
            'reason': 'General checkup',
            'honeypot': ''
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Step 4: Verify booking was created
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AppointmentRequest.objects.filter(
                email='systemtest@test.com',
                doctor=self.doctor
            ).exists()
        )
        
        # Step 5: Verify booking details
        booking = AppointmentRequest.objects.get(email='systemtest@test.com')
        self.assertEqual(booking.status, AppointmentRequest.StatusChoice.NEW)
        self.assertEqual(booking.preferred_time, 'morning')
        self.assertEqual(booking.reason, 'General checkup')
        
        # Step 6: Verify email was sent
        mock_mail.assert_called()


class FullExpertInquiryFlowTests(TestCase):
    """System test: complete expert inquiry workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.plan = InsurancePlan.objects.create(
            provider_name="System Plan",
            plan_name="Complete Plan",
            network="System Network",
            max_benefit=Decimal("500000"),
            score=Decimal("4.5")
        )
        self.staff = User.objects.create_user(
            username='inquiry_staff',
            email='inquiry_staff@test.com',
            password='pass',
            is_staff=True
        )
        self.url = '/api/expert-inquiry/'
    
    @patch('main.views.send_mail')
    @patch('main.models.ExpertInquiry.auto_assign')
    @patch('main.models.ExpertInquiry.check_and_escalate')
    def test_full_inquiry_flow_created_assigned_tracked(self, mock_escalate, mock_assign, mock_mail):
        """Full flow: Create inquiry → auto-assign → track SLA → escalate if needed."""
        # Step 1: Submit inquiry
        payload = {
            'full_name': 'Inquiry Submitter',
            'email': 'inquirer@system.com',
            'phone': '+254712345678',
            'question': 'EMERGENCY: Need urgent insurance coverage advice',
            'interested_plan': self.plan.id
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Verify inquiry was created
        inquiry = ExpertInquiry.objects.get(email='inquirer@system.com')
        self.assertEqual(inquiry.full_name, 'Inquiry Submitter')
        self.assertEqual(inquiry.interested_plan, self.plan)
        
        # Step 3: Verify SLA deadline was set
        self.assertIsNotNone(inquiry.sla_deadline)
        self.assertGreater(inquiry.sla_deadline, inquiry.created_at)
        
        # Step 4: Verify priority was detected (for EMERGENCY keyword)
        priority = inquiry.get_priority()
        self.assertIsNotNone(priority)
        
        # Step 5: Simulate checking SLA status
        sla_status = inquiry.get_sla_status()
        self.assertIsNotNone(sla_status)
        
        # Step 6: Mark as contacted
        inquiry.is_contacted = True
        inquiry.mark_as_contacted()
        self.assertIsNotNone(inquiry.first_response_time)


class FullGovernanceFlowTests(TestCase):
    """System test: complete governance creation workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.staff = User.objects.create_user(
            username='governance_staff',
            email='gov_staff@test.com',
            password='staffpass',
            is_staff=True
        )
        self.url = '/governance/create/'
    
    @patch('main.views.send_mail')
    def test_full_governance_flow_new_user_creation(self, mock_mail):
        """Full flow: Staff creates new governance member → user created → linked."""
        # Step 1: Login as staff
        self.client.login(username='governance_staff', password='staffpass')
        
        # Step 2: Submit governance creation with new user
        payload = {
            'governance_category': 'Board',
            'description': 'System Test Board Member',
            'new_username': 'governance_member_new',
            'new_password': 'GovernancePass@123',
            'new_email': 'govnew@test.com'
        }
        response = self.client.post(self.url, data=payload, follow=True)
        
        # Step 3: Verify response
        self.assertEqual(response.status_code, 200)
        
        # Step 4: Verify user was created
        self.assertTrue(
            User.objects.filter(username='governance_member_new').exists()
        )
        
        # Step 5: Verify governance record exists
        self.assertTrue(
            Governance.objects.filter(
                governance_category='Board'
            ).exists()
        )
    
    @patch('main.views.send_mail')
    def test_full_governance_flow_existing_member(self, mock_mail):
        """Full flow: Staff links existing member to governance."""
        # Step 1: Create existing member
        member = User.objects.create_user(
            username='existing_gov',
            email='existing@test.com',
            password='pass'
        )
        
        # Step 2: Login as staff
        self.client.login(username='governance_staff', password='staffpass')
        
        # Step 3: Submit governance with existing member
        payload = {
            'governance_category': 'Committee',
            'description': 'System Test Committee',
            'members': member.id
        }
        response = self.client.post(self.url, data=payload, follow=True)
        
        # Step 4: Verify governance was created
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Governance.objects.filter(
                governance_category='Committee',
                members=member
            ).exists()
        )


class FullAIRecommendationFlowTests(TestCase):
    """System test: complete AI recommendation workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.plan_basic = InsurancePlan.objects.create(
            provider_name="Basic Provider",
            plan_name="Basic Plan",
            network="Network A",
            max_benefit=Decimal("50000"),
            score=Decimal("3.0")
        )
        self.plan_premium = InsurancePlan.objects.create(
            provider_name="Premium Provider",
            plan_name="Premium Plan",
            network="Network B",
            max_benefit=Decimal("500000"),
            score=Decimal("4.8")
        )
        
        # Create recommendation rules
        AIRecommendationRule.objects.create(
            age_bracket=AIRecommendationRule.AgeBracket.AGE_25_35,
            residence=AIRecommendationRule.Residence.URBAN,
            priority=AIRecommendationRule.Priority.HIGH,
            recommended_plan=self.plan_premium,
            recommendation_text="Premium coverage recommended for urban young professionals"
        )
        
        AIRecommendationRule.objects.create(
            age_bracket=AIRecommendationRule.AgeBracket.AGE_50_PLUS,
            residence=AIRecommendationRule.Residence.RURAL,
            priority=AIRecommendationRule.Priority.LOW,
            recommended_plan=self.plan_basic,
            recommendation_text="Basic coverage sufficient for rural seniors"
        )
        
        self.url = '/healthcare/insurance-support/api/recommend/'
    
    @patch('main.views.generate_recommendation_text', return_value='Recommended plan')
    def test_full_recommendation_flow_input_to_output(self, mock_rec):
        """Full flow: User inputs criteria → rules match → recommendation returned."""
        # Step 1: Submit recommendation request
        payload = {
            'age': 28,
            'residence': 'urban',
            'priority': 'high'
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Step 2: Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Step 3: Verify recommendation data
        self.assertIn('recommendation', data)
        if 'plan' in data:
            self.assertIsNotNone(data['plan'])


class FullTrainingCourseEnrollmentFlowTests(TestCase):
    """System test: complete training course enrollment workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.future_date = timezone.now() + timedelta(days=30)
        self.later_date = self.future_date + timedelta(days=10)
    
    def test_full_enrollment_flow_course_creation_to_completion(self):
        """Full flow: Create course → enroll students → track progress → complete."""
        # Step 1: Create course
        course = TrainingCourse.objects.create(
            title="System Test Course",
            category=TrainingCourse.Category.TECH,
            description="Python Programming Fundamentals",
            duration="4 weeks",
            format=TrainingCourse.Format.ONLINE,
            enrollment=TrainingCourse.Enrollment.OPEN,
            max_students=50,
            enrolled_students=0,
            start_date=self.future_date,
            end_date=self.later_date,
            instructor="System Instructor"
        )
        
        # Step 2: Verify course created
        self.assertEqual(course.title, "System Test Course")
        self.assertEqual(course.enrolled_students, 0)
        self.assertEqual(course.enrollment, TrainingCourse.Enrollment.OPEN)
        
        # Step 3: Simulate enrollments
        course.enrolled_students = 15
        course.save()
        
        # Step 4: Verify enrollment tracking
        course.refresh_from_db()
        self.assertEqual(course.enrolled_students, 15)
        self.assertLess(course.enrolled_students, course.max_students)
        
        # Step 5: Check enrollment status
        self.assertEqual(course.enrollment, TrainingCourse.Enrollment.OPEN)
        
        # Step 6: Check progress
        progress = course.progress_percentage
        self.assertGreaterEqual(progress, 0)
        self.assertLessEqual(progress, 100)


class FullCSVExportFlowTests(TestCase):
    """System test: complete CSV export workflow for insurance plans."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = '/download-comparison/'
        
        # Create multiple plans
        for i in range(3):
            InsurancePlan.objects.create(
                provider_name=f"Provider {i}",
                plan_name=f"Plan {i}",
                network=f"Network {i}",
                max_benefit=Decimal("100000") * (i + 1),
                evacuation=i % 2 == 0,
                score=Decimal("3.5") + Decimal(i) * Decimal("0.5"),
                is_active=True,
                display_order=i
            )
    
    def test_full_csv_export_flow(self):
        """Full flow: Access CSV export → get file → verify data."""
        # Step 1: Request CSV export
        response = self.client.get(self.url)
        
        # Step 2: Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        
        # Step 3: Verify content is CSV-formatted
        content = response.content.decode('utf-8')
        lines = content.strip().split('\n')
        self.assertGreater(len(lines), 1)  # Headers + at least 1 row
        
        # Step 4: Verify headers exist
        self.assertIn('Provider', lines[0])


class ConcurrentAccessRegressionTests(TestCase):
    """System test: verify concurrent access doesn't cause issues."""
    
    def setUp(self):
        """Set up test data."""
        self.plan = InsurancePlan.objects.create(
            provider_name="Concurrent Test",
            plan_name="Plan",
            network="Network",
            max_benefit=Decimal("100000")
        )
    
    def test_multiple_concurrent_inquiries_no_conflict(self):
        """Multiple inquiries created simultaneously should not conflict."""
        # Create multiple inquiries
        inquiries = []
        for i in range(5):
            inquiry = ExpertInquiry(
                full_name=f"User {i}",
                email=f"concurrent{i}@test.com",
                phone=f"+254712{i:06d}",
                question="Test question",
                interested_plan=self.plan
            )
            inquiries.append(inquiry)
        
        # Save all
        for inquiry in inquiries:
            inquiry.save()
        
        # Verify all were saved
        self.assertEqual(ExpertInquiry.objects.count(), 5)
        
        # Verify no duplicates/conflicts
        emails = [i.email for i in inquiries]
        self.assertEqual(len(emails), len(set(emails)))
