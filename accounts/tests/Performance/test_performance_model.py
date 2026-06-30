from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from accounts.models import UserProfile, UserGroup
import time

User = get_user_model()

class ModelPerformanceTest(TestCase):
    def setUp(self):
        """Create a bulk batch of data to test database stress levels."""
        self.users = []
        # Creating 50 users and profiles to simulate a growing database
        for i in range(50):
            user = User.objects.create_user(
                username=f"perfuser_{i}", 
                password="password123"
            )
            UserProfile.objects.create(
                user=user,
                position="Developer",
                company="Performance Inc"
            )
            self.users.append(user)

        self.group = UserGroup.objects.create(name="Performance Group")
        self.group.members.add(*self.users)

    def test_profile_list_query_efficiency(self):
        """
        Performance Test: Ensure fetching profiles does not cause an N+1 query issue.
        We use select_related('user') so it fetches everything in ONE database join.
        """
        with CaptureQueriesContext(connection) as context:
            # Good performance practice: select_related joins the tables in SQL
            profiles = list(UserProfile.objects.select_related('user').all())
            
            # Loop through them to mimic reading them in a template or API
            for profile in profiles:
                _ = profile.user.username

        # If select_related is working correctly, this should require exactly 1 query.
        # Without select_related, it would make 51 queries (1 for profiles + 50 for users)!
        self.assertEqual(len(context), 1)

    def test_get_member_count_speed(self):
        """
        Performance Test: Ensure custom model methods execute quickly.
        The get_member_count() uses .count() which happens efficiently inside SQL.
        """
        start_time = time.time()
        
        # Run the method we are testing
        count = self.group.get_member_count()
        
        end_time = time.time()
        execution_time = end_time - start_time

        # 1. Ensure the count is accurate
        self.assertEqual(count, 50)
        
        # 2. Speed Benchmarking: Database count should take less than 0.05 seconds
        self.assertLess(execution_time, 0.05, f"Database count took too long: {execution_time}s")