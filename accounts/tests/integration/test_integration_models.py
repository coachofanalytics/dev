from django.test import TestCase
from django.utils import timezone
from datetime import time, timedelta
from accounts.models import Tracker  # Ensure this matches your app name
from django.db.models import Sum, Avg

from datetime import time, date, timedelta # Import date here
# ... (rest of imports)

class TrackerIntegrationTest(TestCase):

    def setUp(self):
        """
        Create multiple Tracker instances for integration testing.
        """
        # --- FIX START ---
        # 1. Get today's date
        today_date = timezone.now().date()
        yesterday_date = today_date - timedelta(days=1)

        # 2. Convert date objects to timezone-aware datetime objects (at midnight)
        # This resolves the RuntimeWarning
        self.today = timezone.make_aware(timezone.datetime.combine(today_date, time.min))
        self.yesterday = timezone.make_aware(timezone.datetime.combine(yesterday_date, time.min))
        # --- FIX END ---
        
        # Tracker 1: John, Development, Today, 120 mins
        Tracker.objects.create(
            category="Development",
            sub_category="Backend",
            task="API implementation",
            plan="Implement CRUD endpoints for UserProfile",
            employee="John Doe",
            # Use the corrected self.today (which is a full datetime object)
            login_date=self.today, 
            start_time=time(9, 0, 0),
            duration=120,
            time=120
        )
        
        # Tracker 2: John, Testing, Today, 60 mins
        Tracker.objects.create(
            category="Testing",
            sub_category="Unit Tests",
            task="Model tests",
            plan="Refactor and finalize model tests",
            employee="John Doe",
            login_date=self.today,
            start_time=time(11, 0, 0),
            duration=60,
            time=60
        )
        
        # Tracker 3: Jane, Development, Yesterday, 90 mins
        Tracker.objects.create(
            category="Development",
            sub_category="Frontend",
            task="UI design",
            plan="Draft initial UI/UX wireframes",
            employee="Jane Smith",
            login_date=self.yesterday,
            start_time=time(10, 0, 0),
            duration=90,
            time=90
        )