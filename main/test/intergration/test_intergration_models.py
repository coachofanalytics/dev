from django.test import TestCase, Client
from main.models import Scholarship, Governance
# from main.forms import ScholarshipForm
from datetime import timedelta
from django.utils import timezone


from django.contrib.auth import get_user_model

User = get_user_model()


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
        
        form = ScholarshipForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Save form to create model instance
        scholarship = form.save()
        
        # Verify model instance was created correctly
        self.assertEqual(scholarship.title, 'Form Integration Test')
        self.assertEqual(scholarship.provider, 'Form University')
        self.assertEqual(scholarship.level, 'Masters')
        self.assertEqual(scholarship.amount, '12000 USD')
        
        # Verify instance is in database
        self.assertTrue(Scholarship.objects.filter(title='Form Integration Test').exists())
    
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
        self.assertEqual(len(undergraduate_scholarships), len(scholarships))  # All should be undergraduate
        
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
    """End-to-end integration tests for Governance functionality"""

    def setUp(self):
        self.client = Client()

        # Create a test user
        self.user = User.objects.create_user(
            username="integration_user",
            email="integration@test.com",
            password="password123"
        )

        # Create initial test data
        self.governance = Governance.objects.create(
            governance_category="Integration Test Governance",
            description="Initial governance record for integration tests",
            members=self.user,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

    def test_governance_workflow_integration(self):
        """Test complete governance workflow from model to template"""
        # 1. Model Layer - Data creation
        governance = Governance.objects.create(
            governance_category="Workflow Test Governance",
            description="Testing end-to-end workflow",
            members=self.user,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # Verify model creation
        self.assertEqual(Governance.objects.count(), 2)
        self.assertEqual(governance.governance_category, "Workflow Test Governance")

        # 2. View Layer - Data retrieval
        response = self.client.get('/governance')
        self.assertEqual(response.status_code, 200)

        # 3. Context Integration - Verify data passed to template
        self.assertIn('governances', response.context)
        governances = list(response.context['governances'])
        self.assertEqual(len(governances), 2)

        # 4. Template Integration - Verify data is rendered
        self.assertContains(response, "Workflow Test Governance")
        self.assertContains(response, "Testing end-to-end workflow")

    def test_filtering_integration(self):
        """Test integrated filtering functionality"""
        # Create additional records
        Governance.objects.create(
            governance_category="Filter Test A",
            description="Filter integration A",
            members=self.user,
            created_at=timezone.now() - timedelta(days=5),
            updated_at=timezone.now() - timedelta(days=5)
        )
        Governance.objects.create(
            governance_category="Filter Test B",
            description="Filter integration B",
            members=self.user,
            created_at=timezone.now() - timedelta(days=1),
            updated_at=timezone.now() - timedelta(days=1)
        )

        # Test filtering by governance_category containing 'Filter'
        response = self.client.get('/governance?search=Filter')
        self.assertEqual(response.status_code, 200)
        governances = list(response.context['governances'])
        for governance in governances:
            self.assertIn("Filter", governance.governance_category)

    def test_ordering_integration(self):
        """Test that ordering works correctly across the stack"""
        # Create governances with varied created_at for ordering test
        governance_early = Governance.objects.create(
            governance_category="Early Governance",
            description="Earlier record",
            members=self.user,
            created_at=timezone.now() - timedelta(days=10),
            updated_at=timezone.now() - timedelta(days=10)
        )
        governance_late = Governance.objects.create(
            governance_category="Late Governance",
            description="Later record",
            members=self.user,
            created_at=timezone.now() + timedelta(days=5),
            updated_at=timezone.now() + timedelta(days=5)
        )

        response = self.client.get('/governance')
        self.assertEqual(response.status_code, 200)

        governances = list(response.context['governances'])
        # Earliest created_at should be first
        created_dates = [g.created_at for g in governances]
        self.assertEqual(created_dates, sorted(created_dates))

    def test_template_context_and_rendering(self):
        """Ensure governance data is rendered properly in templates"""
        response = self.client.get('/governance')
        self.assertTemplateUsed(response, 'governance_app/governance_list.html')
        self.assertIn('Integration Test Governance', response.content.decode())
        self.assertIn('Initial governance record for integration tests', response.content.decode())
