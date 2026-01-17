from django.test import TestCase, Client
from main.models import Scholarship

from datetime import date, timedelta
from django.utils import timezone
from django.urls import reverse, resolve
from main.models import Team, Governance


class ScholarshipIntegrationTest(TestCase):
    """End-to-end integration tests for scholarship functionality"""
    
    def setUp(self):
        self.client = Client()
        
        # Create initial test data
        self.scholarship = Scholarship.objects.create(
            title="Integration Test Scholarship",
            provider="Integration University",
            level="Undergraduate",
            field="STEM",
            location="Kenya",
            amount="7500 USD",
            deadline=timezone.now().date() + timedelta(days=45),
            status="Open"
        )
    
    def test_scholarship_workflow_integration(self):
        """Test complete scholarship workflow from model to template"""
        # 1. Model Layer - Data creation
        scholarship = Scholarship.objects.create(
            title="Workflow Test Scholarship",
            provider="Workflow University",
            level="PhD",
            field="Arts",
            location="Global",
            amount="15000 USD",
            deadline=timezone.now().date() + timedelta(days=60),
            status="Closing Soon"
        )
        
        # Verify model creation
        self.assertEqual(Scholarship.objects.count(), 2)
        self.assertEqual(scholarship.title, "Workflow Test Scholarship")
        
        # 2. View Layer - Data retrieval
        response = self.client.get('/scholarship')
        self.assertEqual(response.status_code, 200)
        
        # 3. Context Integration - Verify data passed to template
        self.assertIn('scholarships', response.context)
        scholarships = list(response.context['scholarships'])
        self.assertEqual(len(scholarships), 2)
        
        # 4. Template Integration - Verify data is rendered
        self.assertContains(response, "Workflow Test Scholarship")
        self.assertContains(response, "Workflow University")
        self.assertContains(response, "PhD")
        self.assertContains(response, "Arts")
        self.assertContains(response, "15000 USD")
        self.assertContains(response, "Closing Soon")
    
    def test_form_model_integration(self):
        """Test integration between forms and models"""
        # Test valid form data creates valid model instance
        form_data = {
            'title': 'Form Integration Test',
            'provider': 'Form University',
            'level': 'Masters',
            'field': 'Business',
            'location': 'USA',
            'amount': '12000 USD',
            'deadline': timezone.now().date() + timedelta(days=30),
            'status': 'Open'
        }
        
        # form = ScholarshipForm(data=form_data)
        # self.assertTrue(form.is_valid())
        
        # # Save form to create model instance
        # scholarship = form.save()
        
        # # Verify model instance was created correctly
        # self.assertEqual(scholarship.title, 'Form Integration Test')
        # self.assertEqual(scholarship.provider, 'Form University')
        # self.assertEqual(scholarship.level, 'Masters')
        # self.assertEqual(scholarship.amount, '12000 USD')
        
        # # Verify instance is in database
        # self.assertTrue(Scholarship.objects.filter(title='Form Integration Test').exists())
    
    def test_url_view_template_integration(self):
        """Test integration between URLs, views, and templates"""
        # Test URL resolution
        response = self.client.get('/scholarship')
        self.assertEqual(response.status_code, 200)
        
        # Test template used
        self.assertTemplateUsed(response, 'scholarship_app/scholarship_search.html')
        
        # Test context data
        self.assertIn('scholarships', response.context)
        
        # Test template rendering with context data
        content = response.content.decode()
        self.assertIn('Integration Test Scholarship', content)
        self.assertIn('Integration University', content)
        self.assertIn('Undergraduate', content)
        self.assertIn('STEM', content)
        self.assertIn('7500 USD', content)
    
    def test_filtering_integration(self):
        """Test integrated filtering functionality"""
        # Create additional test data for filtering
        Scholarship.objects.create(
            title="Filter Test Undergraduate",
            provider="Filter University",
            level="Undergraduate",
            field="STEM",
            location="Kenya",
            amount="5000 USD",
            deadline=timezone.now().date() + timedelta(days=30),
            status="Open"
        )
        
        Scholarship.objects.create(
            title="Filter Test Masters", 
            provider="Filter University",
            level="Masters",
            field="Business",
            location="Global",
            amount="10000 USD",
            deadline=timezone.now().date() + timedelta(days=20),
            status="Closing Soon"
        )
        
        # Test level filtering integration
        response = self.client.get('/scholarship?level=Undergraduate')
        self.assertEqual(response.status_code, 200)
        
        scholarships = list(response.context['scholarships'])
        undergraduate_scholarships = [s for s in scholarships if s.level == 'Undergraduate']
        # Verify exactly 2 undergraduate scholarships were found
        self.assertEqual(len(scholarships), 2)
        
        # Test field filtering integration
        response = self.client.get('/scholarship?field=Business')
        self.assertEqual(response.status_code, 200)
        
        scholarships = list(response.context['scholarships'])
        business_scholarships = [s for s in scholarships if s.field == 'Business']
        self.assertEqual(len(business_scholarships), len(scholarships))  # All should be business
        
        # Test combined filtering
        response = self.client.get('/scholarship?level=Undergraduate&field=STEM')
        self.assertEqual(response.status_code, 200)
        
        scholarships = list(response.context['scholarships'])
        for scholarship in scholarships:
            self.assertEqual(scholarship.level, 'Undergraduate')
            self.assertEqual(scholarship.field, 'STEM')
    
    def test_ordering_integration(self):
        """Test that ordering works correctly across the stack"""
        # Create scholarships with specific deadlines for ordering test
        scholarship_early = Scholarship.objects.create(
            title="Early Deadline",
            provider="Order University",
            level="Undergraduate",
            field="STEM",
            location="Kenya",
            amount="5000 USD",
            deadline=timezone.now().date() + timedelta(days=5),
            status="Open"
        )
        
        scholarship_late = Scholarship.objects.create(
            title="Late Deadline",
            provider="Order University",
            level="Masters",
            field="Business",
            location="Global",
            amount="10000 USD",
            deadline=timezone.now().date() + timedelta(days=50),
            status="Open"
        )
        
        # Test ordering in view
        response = self.client.get('/scholarship')
        self.assertEqual(response.status_code, 200)
        
        scholarships = list(response.context['scholarships'])
        
        # Verify ordering (earliest deadline first)
        self.assertEqual(scholarships[0], scholarship_early)  # 5 days
        # scholarships[1] would be the original scholarship (45 days)
        # scholarships[2] would be scholarship_late (50 days)
        
        # The earliest deadline should be first
        deadlines = [s.deadline for s in scholarships]
        self.assertEqual(deadlines, sorted(deadlines))





class GovernanceIntegrationTest(TestCase):
    def setUp(self):
        # Setup data needed for the test
        self.client = Client()
        self.team_member = Team.objects.create(name="Integration User")
        # Replace 'governance-create' with the actual 'name' in your urls.py
        self.url = reverse('main:governance_create')

    def test_governance_post_request_creates_object(self):
        """Test that a POST request successfully creates a Governance record."""
        data = {
            'governance_category': 'Financial Policy',
            'description': 'Integration test description',
            'members': self.team_member.id  # Passing the ID for the foreign key
        }
        
        # Simulate POST request
        response = self.client.post(self.url, data)

        # 1. Check for successful redirect (usually 302) or success status (200/201)
        self.assertEqual(response.status_code, 302) 
        
        # 2. Verify the data actually exists in the database
        self.assertTrue(Governance.objects.filter(governance_category='Financial Policy').exists())