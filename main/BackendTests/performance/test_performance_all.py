"""
Performance tests for main app - verify speed requirements.
Tests are timed to ensure endpoints respond within SLA.
"""
import json
import time
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from main.models import (
    Scholarship, TrainingCourse, Doctor,
    InsurancePlan, AIRecommendationRule
)

User = get_user_model()


class AIRecommendationPerformanceTests(TestCase):
    """Performance tests for AI recommendation endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = '/healthcare/insurance-support/api/recommend/'
        
        # Create recommendation rules
        plan = InsurancePlan.objects.create(
            provider_name="Perf Test",
            plan_name="Plan",
            network="Network",
            max_benefit=Decimal("100000")
        )
        
        AIRecommendationRule.objects.create(
            age_bracket=AIRecommendationRule.AgeBracket.AGE_25_35,
            residence=AIRecommendationRule.Residence.URBAN,
            priority=AIRecommendationRule.Priority.HIGH,
            recommended_plan=plan,
            recommendation_text="Test"
        )
    
    @patch('main.views.generate_recommendation_text', return_value='Recommendation')
    def test_ai_recommendation_response_under_1_second(self, mock_rec):
        """AI recommendation endpoint should respond in < 1 second."""
        payload = {
            'age': 30,
            'residence': 'urban',
            'priority': 'high'
        }
        
        start_time = time.time()
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        elapsed_time = time.time() - start_time
        
        # Assert response is successful
        self.assertEqual(response.status_code, 200)
        
        # Assert response time is under 1 second
        self.assertLess(elapsed_time, 1.0, 
                       f"Recommendation took {elapsed_time:.2f}s (max 1.0s)")


class DoctorBookingPerformanceTests(TestCase):
    """Performance tests for doctor booking endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.doctor = Doctor.objects.create(
            name="Perf Dr",
            specialty="General",
            location_city="Nairobi",
            location_country="Kenya"
        )
        self.future_date = (timezone.now() + timedelta(days=7)).date().isoformat()
        self.url = f'/api/doctor/{self.doctor.id}/book/'
    
    @patch('main.views.send_mail')
    def test_doctor_booking_page_loads_under_1_second(self, mock_mail):
        """Doctor booking page should load in < 1 second."""
        start_time = time.time()
        response = self.client.get(f'/doctor/{self.doctor.id}/')
        elapsed_time = time.time() - start_time
        
        # Assert page loads
        self.assertIn(response.status_code, [200, 301, 302])
        
        # Assert load time is under 1 second
        self.assertLess(elapsed_time, 1.0,
                       f"Doctor page took {elapsed_time:.2f}s (max 1.0s)")
    
    @patch('main.views.send_mail')
    def test_doctor_booking_submission_under_2_seconds(self, mock_mail):
        """Doctor booking submission should complete in < 2 seconds."""
        payload = {
            'full_name': 'Perf Patient',
            'email': 'perf@test.com',
            'preferred_date': self.future_date,
            'preferred_time': 'morning',
            'honeypot': ''
        }
        
        start_time = time.time()
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        elapsed_time = time.time() - start_time
        
        # Assert submission succeeds
        self.assertEqual(response.status_code, 200)
        
        # Assert submission time is under 2 seconds
        self.assertLess(elapsed_time, 2.0,
                       f"Booking submission took {elapsed_time:.2f}s (max 2.0s)")


class ScholarshipSearchPerformanceTests(TestCase):
    """Performance tests for scholarship search."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = '/education/scholarships/'
        
        # Create multiple scholarships
        future_date = timezone.now() + timedelta(days=30)
        for i in range(20):
            Scholarship.objects.create(
                title=f"Scholarship {i}",
                amount_value=Decimal("1000") * (i + 1),
                amount_currency="USD",
                provider=f"Provider {i}",
                level=Scholarship.Level.UNDERGRADUATE if i % 2 == 0 else Scholarship.Level.MASTERS,
                field=Scholarship.Field.STEM if i % 2 == 0 else Scholarship.Field.HUMANITIES,
                location=Scholarship.Location.GLOBAL,
                deadline=future_date,
                status=Scholarship.Status.OPEN
            )
    
    def test_scholarship_list_page_loads_under_1_second(self):
        """Scholarship list page should load in < 1 second."""
        start_time = time.time()
        response = self.client.get(self.url)
        elapsed_time = time.time() - start_time
        
        # Assert page loads
        self.assertEqual(response.status_code, 200)
        
        # Assert load time is under 1 second
        self.assertLess(elapsed_time, 1.0,
                       f"Scholarship list took {elapsed_time:.2f}s (max 1.0s)")
    
    def test_scholarship_search_filter_under_1_second(self):
        """Scholarship search with filters should complete in < 1 second."""
        start_time = time.time()
        response = self.client.get(
            f"{self.url}?filter_field={Scholarship.Field.STEM}"
        )
        elapsed_time = time.time() - start_time
        
        # Assert search completes
        self.assertEqual(response.status_code, 200)
        
        # Assert search time is under 1 second
        self.assertLess(elapsed_time, 1.0,
                       f"Scholarship search took {elapsed_time:.2f}s (max 1.0s)")


class GovernanceCreatePerformanceTests(TestCase):
    """Performance tests for governance creation."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.staff = User.objects.create_user(
            username='perf_staff',
            email='staff@test.com',
            password='pass',
            is_staff=True
        )
        self.url = '/governance/create/'
    
    @patch('main.views.send_mail')
    def test_governance_page_loads_under_2_seconds(self, mock_mail):
        """Governance creation page should load in < 2 seconds."""
        self.client.login(username='perf_staff', password='pass')
        
        start_time = time.time()
        response = self.client.get(self.url)
        elapsed_time = time.time() - start_time
        
        # Assert page loads
        self.assertEqual(response.status_code, 200)
        
        # Assert load time is under 2 seconds (authenticated page)
        self.assertLess(elapsed_time, 2.0,
                       f"Governance page took {elapsed_time:.2f}s (max 2.0s)")


class TrainingCourseListPerformanceTests(TestCase):
    """Performance tests for training course listing."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = '/education/training/'
        
        # Create multiple courses
        future_date = timezone.now() + timedelta(days=30)
        later_date = future_date + timedelta(days=10)
        
        for i in range(15):
            TrainingCourse.objects.create(
                title=f"Course {i}",
                category=TrainingCourse.Category.TECH if i % 2 == 0 else TrainingCourse.Category.BUSINESS,
                description=f"Test course {i}",
                duration="4 weeks",
                format=TrainingCourse.Format.ONLINE,
                enrollment=TrainingCourse.Enrollment.OPEN,
                max_students=50,
                start_date=future_date,
                end_date=later_date
            )
    
    def test_training_course_list_under_1_second(self):
        """Training course list should load in < 1 second."""
        start_time = time.time()
        response = self.client.get(self.url)
        elapsed_time = time.time() - start_time
        
        # Assert page loads
        self.assertEqual(response.status_code, 200)
        
        # Assert load time is under 1 second
        self.assertLess(elapsed_time, 1.0,
                       f"Training list took {elapsed_time:.2f}s (max 1.0s)")


class DatabaseQueryPerformanceTests(TestCase):
    """Performance tests for database query efficiency."""
    
    def setUp(self):
        """Set up test data."""
        # Create multiple plans for search
        for i in range(50):
            InsurancePlan.objects.create(
                provider_name=f"Provider {i}",
                plan_name=f"Plan {i}",
                network=f"Network {i}",
                max_benefit=Decimal("100000") * (i + 1),
                score=Decimal("3.0") + Decimal(i % 5) * Decimal("0.5")
            )
    
    def test_insurance_plan_query_performance(self):
        """Insurance plan queries should be efficient."""
        start_time = time.time()
        
        # Perform lookup with filtering
        plans = InsurancePlan.objects.filter(
            is_active=True
        ).order_by('-score')[:10]
        
        # Consume results
        list(plans)
        
        elapsed_time = time.time() - start_time
        
        # Should complete quickly (even with many records)
        self.assertLess(elapsed_time, 0.5,
                       f"Query took {elapsed_time:.2f}s (max 0.5s)")


class BulkOperationPerformanceTests(TestCase):
    """Performance tests for bulk operations."""
    
    def test_bulk_scholarship_creation_under_5_seconds(self):
        """Bulk creation of 100 scholarships should complete in < 5 seconds."""
        future_date = timezone.now() + timedelta(days=30)
        
        start_time = time.time()
        
        scholarships = [
            Scholarship(
                title=f"Bulk {i}",
                amount_value=Decimal("1000"),
                amount_currency="USD",
                provider=f"Provider {i}",
                level=Scholarship.Level.UNDERGRADUATE,
                field=Scholarship.Field.STEM,
                location=Scholarship.Location.GLOBAL,
                deadline=future_date,
                status=Scholarship.Status.OPEN
            )
            for i in range(100)
        ]
        
        Scholarship.objects.bulk_create(scholarships)
        
        elapsed_time = time.time() - start_time
        
        # Verify creation
        self.assertEqual(Scholarship.objects.count(), 100)
        
        # Assert bulk creation is efficient
        self.assertLess(elapsed_time, 5.0,
                       f"Bulk creation took {elapsed_time:.2f}s (max 5.0s)")


class ConcurrentQueryPerformanceTests(TestCase):
    """Performance tests for concurrent-like queries."""
    
    def setUp(self):
        """Set up test data."""
        # Create test data
        for i in range(10):
            Doctor.objects.create(
                name=f"Dr {i}",
                specialty="General",
                location_city="Nairobi",
                location_country="Kenya"
            )
    
    def test_multiple_doctor_queries_performance(self):
        """Multiple doctor queries should complete efficiently."""
        start_time = time.time()
        
        # Simulate multiple searches
        doctors1 = list(Doctor.objects.filter(specialty__icontains="General"))
        doctors2 = list(Doctor.objects.filter(location_city="Nairobi"))
        doctors3 = list(Doctor.objects.all()[:5])
        
        elapsed_time = time.time() - start_time
        
        # Should complete quickly
        self.assertLess(elapsed_time, 1.0,
                       f"Multiple queries took {elapsed_time:.2f}s (max 1.0s)")
        
        # Verify results
        self.assertGreater(len(doctors1), 0)
        self.assertGreater(len(doctors2), 0)
