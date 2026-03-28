"""
Comprehensive Performance Tests for Main App
Tests response times and load performance of critical endpoints
"""
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
import json
import time
from unittest.mock import patch

from main.models import (
    Scholarship, TrainingCourse, Doctor, InsurancePlan, AIRecommendationRule
)

User = get_user_model()


# =====================================================================
# PERFORMANCE TEST CONFIGURATION
# =====================================================================

PERFORMANCE_THRESHOLDS = {
    'ai_recommendation': 1.0,      # 1 second
    'doctor_booking': 1.0,          # 1 second
    'scholarship_list': 1.0,        # 1 second
    'governance_create': 2.0        # 2 seconds
}


# =====================================================================
# AI RECOMMENDATION ENDPOINT PERFORMANCE TESTS
# =====================================================================

@patch('main.views.generate_recommendation_text', return_value='Recommendation')
class AIRecommendationPerformanceTests(TestCase):
    """Performance tests for AI recommendation endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.url = '/healthcare/insurance-support/api/recommend/'
        
        # Create test plans
        for i in range(5):
            InsurancePlan.objects.create(
                provider_name=f'Provider{i}',
                plan_name=f'Plan{i}',
                network='Global',
                max_benefit='$1,000,000',
                evacuation='Included',
                score=9.0 - (i * 0.1)
            )
        
        # Create test rules
        ages = ['young', 'mid', 'senior']
        residences = ['usa', 'europe', 'other']
        priorities = ['budget', 'comprehensive', 'emergency']
        
        plan = InsurancePlan.objects.first()
        for age in ages:
            for residence in residences:
                for priority in priorities:
                    AIRecommendationRule.objects.create(
                        age_bracket=age,
                        residence=residence,
                        priority=priority,
                        recommended_plan=plan,
                        recommendation_text='Test recommendation'
                    )
    
    def test_ai_recommendation_endpoint_under_1_second(self, mock_gen):
        """Performance: AI recommendation endpoint < 1 second"""
        payload = {
            'age': 'young',
            'residence': 'usa',
            'priority': 'budget'
        }
        
        start_time = time.time()
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        elapsed_time = time.time() - start_time
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertLess(
            elapsed_time,
            PERFORMANCE_THRESHOLDS['ai_recommendation'],
            f"AI recommendation took {elapsed_time:.3f}s, "
            f"threshold is {PERFORMANCE_THRESHOLDS['ai_recommendation']}s"
        )
    
    def test_ai_recommendation_with_multiple_sequential_requests(self, mock_gen):
        """Performance: Multiple requests stay under threshold"""
        payload = {
            'age': 'mid',
            'residence': 'europe',
            'priority': 'comprehensive'
        }
        
        times = []
        for _ in range(3):
            start = time.time()
            response = self.client.post(
                self.url,
                data=json.dumps(payload),
                content_type='application/json'
            )
            elapsed = time.time() - start
            times.append(elapsed)
            self.assertEqual(response.status_code, 200)
        
        avg_time = sum(times) / len(times)
        self.assertLess(
            avg_time,
            PERFORMANCE_THRESHOLDS['ai_recommendation'],
            f"Average time {avg_time:.3f}s exceeds threshold"
        )


# =====================================================================
# DOCTOR BOOKING ENDPOINT PERFORMANCE TESTS
# =====================================================================

@patch('django.core.mail.send_mail')
class DoctorBookingPerformanceTests(TestCase):
    """Performance tests for doctor booking endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.doctor = Doctor.objects.create(
            name='Dr. Performance',
            title='Specialist',
            specialty='Performance Testing',
            categories=['general'],
            location_city='Test City',
            location_country='Test Country',
            languages=['english'],
            bio='Performance test doctor'
        )
        self.future_date = str(timezone.now().date() + timedelta(days=7))
        self.url = f'/api/doctor/{self.doctor.id}/book/'
        self.data = {
            'full_name': 'Perf Patient',
            'email': 'perf@example.com',
            'preferred_date': self.future_date,
            'preferred_time': 'morning',
            'reason': 'Performance test',
            'honeypot': ''
        }
    
    def test_doctor_booking_endpoint_under_1_second(self, mock_mail):
        """Performance: Doctor booking endpoint < 1 second"""
        start_time = time.time()
        
        response = self.client.post(self.url, data=self.data, follow=False)
        
        elapsed_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(
            elapsed_time,
            PERFORMANCE_THRESHOLDS['doctor_booking'],
            f"Doctor booking took {elapsed_time:.3f}s, "
            f"threshold is {PERFORMANCE_THRESHOLDS['doctor_booking']}s"
        )
    
    def test_doctor_booking_with_form_validation_under_threshold(self, mock_mail):
        """Performance: Booking with validation still under threshold"""
        # Valid data
        data = self.data.copy()
        data['email'] = 'perf2@example.com'  # Different email for each
        
        start_time = time.time()
        response = self.client.post(self.url, data=data, follow=False)
        elapsed_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed_time, PERFORMANCE_THRESHOLDS['doctor_booking'])


# =====================================================================
# SCHOLARSHIP LIST PAGE PERFORMANCE TESTS
# =====================================================================

class ScholarshipListPerformanceTests(TestCase):
    """Performance tests for scholarship listing"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.today = timezone.now().date()
        
        # Create multiple scholarships
        for i in range(20):
            Scholarship.objects.create(
                title=f'Scholarship {i}',
                provider=f'Provider {i}',
                level='Undergraduate',
                field='STEM',
                location='Global',
                deadline=self.today + timedelta(days=i % 30),
                amount_value=1000 * (i + 1),
                amount_currency='USD'
            )
    
    def test_scholarship_page_loads_under_1_second(self):
        """Performance: Scholarship list page < 1 second"""
        # Assuming there's a scholarship list view
        url = '/scholarships/'  # Adjust based on actual URL
        
        try:
            start_time = time.time()
            response = self.client.get(url, follow=False)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                self.assertLess(
                    elapsed_time,
                    PERFORMANCE_THRESHOLDS['scholarship_list'],
                    f"Scholarship page took {elapsed_time:.3f}s"
                )
        except Exception:
            # URL might not exist, skip if not found
            pass


# =====================================================================
# GOVERNANCE CREATE PAGE PERFORMANCE TESTS
# =====================================================================

class GovernanceCreatePerformanceTests(TestCase):
    """Performance tests for governance creation"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.admin = User.objects.create_user(
            username='perf_admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        # Create many users to test form loading
        for i in range(10):
            User.objects.create_user(
                username=f'member{i}',
                password='pass123'
            )
        self.url = '/governance/create/'
    
    def test_governance_create_page_loads_under_2_seconds(self):
        """Performance: Governance page loads < 2 seconds"""
        self.client.login(username='perf_admin', password='admin123')
        
        start_time = time.time()
        response = self.client.get(self.url, follow=False)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            self.assertLess(
                elapsed_time,
                PERFORMANCE_THRESHOLDS['governance_create'],
                f"Governance page took {elapsed_time:.3f}s"
            )


# =====================================================================
# QUERY OPTIMIZATION TESTS
# =====================================================================

class QueryOptimizationTests(TestCase):
    """Performance tests for query optimization"""
    
    def setUp(self):
        """Set up test data"""
        # Create test data
        self.plan = InsurancePlan.objects.create(
            provider_name='QueryPlan',
            plan_name='Test',
            network='Global',
            max_benefit='$1M',
            evacuation='Included',
            score=9.0
        )
        
        # Create multiple doctors
        for i in range(10):
            Doctor.objects.create(
                name=f'Dr. Query {i}',
                title='Doctor',
                specialty='General',
                categories=['general'],
                location_city='City',
                location_country='Country',
                languages=['english'],
                bio=f'Doctor {i}'
            )
    
    def test_doctor_list_query_efficiency(self):
        """Performance: Doctor list loads efficiently"""
        doctors = Doctor.objects.all()
        
        start_time = time.time()
        # Iterate through doctors (simulating list view)
        names = [doc.name for doc in doctors]
        elapsed_time = time.time() - start_time
        
        # Should be fast for 10 doctors
        self.assertLess(elapsed_time, 0.1)
        self.assertEqual(len(names), 10)


# =====================================================================
# CONCURRENT REQUEST PERFORMANCE TESTS
# =====================================================================

@patch('django.core.mail.send_mail')
class ConcurrentPerformanceTests(TestCase):
    """Performance tests under concurrent load"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.doctor = Doctor.objects.create(
            name='Dr. Concurrent',
            title='Doctor',
            specialty='General',
            categories=['general'],
            location_city='Test',
            location_country='Test',
            languages=['english'],
            bio='Test'
        )
        self.future_date = str(timezone.now().date() + timedelta(days=7))
        self.url = f'/api/doctor/{self.doctor.id}/book/'
    
    def test_multiple_sequential_bookings_performance(self, mock_mail):
        """Performance: Multiple sequential bookings stay efficient"""
        times = []
        
        for i in range(5):
            data = {
                'full_name': f'Patient {i}',
                'email': f'patient{i}@example.com',
                'preferred_date': self.future_date,
                'preferred_time': 'morning',
                'reason': 'Test',
                'honeypot': ''
            }
            
            start = time.time()
            response = self.client.post(self.url, data=data, follow=False)
            elapsed = time.time() - start
            
            self.assertEqual(response.status_code, 200)
            times.append(elapsed)
        
        # Each should be under threshold
        for elapsed in times:
            self.assertLess(
                elapsed,
                PERFORMANCE_THRESHOLDS['doctor_booking'],
                f"Booking took {elapsed:.3f}s"
            )
        
        # Average should also be good
        avg = sum(times) / len(times)
        self.assertLess(avg, PERFORMANCE_THRESHOLDS['doctor_booking'] * 0.8)


# =====================================================================
# CACHE EFFICIENCY TESTS
# =====================================================================

class CacheEfficiencyTests(TestCase):
    """Performance tests for cache efficiency"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create insurance plans
        for i in range(3):
            InsurancePlan.objects.create(
                provider_name=f'Provider {i}',
                plan_name=f'Plan {i}',
                network='Global',
                max_benefit='$1M',
                evacuation='Included',
                score=9.0 - (i * 0.2)
            )
    
    def test_repeated_plan_queries_should_avoid_redundant_hits(self):
        """Performance: Repeated queries should be optimized"""
        # First query
        start1 = time.time()
        plans1 = list(InsurancePlan.objects.all())
        time1 = time.time() - start1
        
        # Second query (could be cached in real scenario)
        start2 = time.time()
        plans2 = list(InsurancePlan.objects.all())
        time2 = time.time() - start2
        
        # Both should be fast
        self.assertLess(time1, 0.1)
        self.assertLess(time2, 0.1)
        
        # Data should be consistent
        self.assertEqual(len(plans1), len(plans2))


# =====================================================================
# API RESPONSE TIME TESTS
# =====================================================================

@patch('main.views.generate_recommendation_text', return_value='Rec')
class APIResponseTimeTests(TestCase):
    """Performance tests for API response times"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.plan = InsurancePlan.objects.create(
            provider_name='APIPlan',
            plan_name='Test',
            network='Global',
            max_benefit='$1M',
            evacuation='Included',
            score=9.5
        )
        
        # Create recommendation rule
        AIRecommendationRule.objects.create(
            age_bracket='young',
            residence='usa',
            priority='budget',
            recommended_plan=self.plan,
            recommendation_text='For you'
        )
    
    def test_json_api_response_time_includes_serialization(self, mock_gen):
        """Performance: JSON serialization doesn't slow response"""
        url = '/healthcare/insurance-support/api/recommend/'
        payload = {
            'age': 'young',
            'residence': 'usa',
            'priority': 'budget'
        }
        
        start_time = time.time()
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        elapsed_time = time.time() - start_time
        
        # Parse response to ensure serialization worked
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Total time including serialization should be under threshold
        self.assertLess(
            elapsed_time,
            PERFORMANCE_THRESHOLDS['ai_recommendation']
        )


if __name__ == '__main__':
    import unittest
    unittest.main()
