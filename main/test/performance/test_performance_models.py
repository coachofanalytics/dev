import time
from django.test import TestCase
from main.models import Scholarship
from datetime import timedelta
from django.utils import timezone
import random


class ScholarshipModelPerformanceTest(TestCase):
    """Performance tests for Scholarship model operations"""
    
    def setUp(self):
        self.bulk_size = 1000  # Number of records for bulk operations
    
    def test_bulk_create_performance(self):
        """Test performance of bulk scholarship creation"""
        scholarships_data = [
            Scholarship(
                title=f"Performance Test Scholarship {i}",
                provider=f"Provider {i % 100}",
                level=random.choice(['Undergraduate', 'Masters', 'PhD', 'Vocational']),
                field=random.choice(['STEM', 'Humanities', 'Business', 'Arts']),
                location=random.choice(['Kenya', 'Global', 'UK', 'USA']),
                amount=f"{random.randint(1000, 20000)} USD",
                deadline=timezone.now().date() + timedelta(days=random.randint(1, 365)),
                status=random.choice(['Open', 'Closing Soon', 'Closed'])
            )
            for i in range(self.bulk_size)
        ]
        
        start_time = time.time()
        Scholarship.objects.bulk_create(scholarships_data)
        end_time = time.time()
        
        creation_time = end_time - start_time
        print(f"Bulk created {self.bulk_size} scholarships in {creation_time:.2f} seconds")
        
        # Performance assertion - should complete in reasonable time
        self.assertLess(creation_time, 5.0, "Bulk creation took too long")
        self.assertEqual(Scholarship.objects.count(), self.bulk_size)
    
    def test_bulk_update_performance(self):
        """Test performance of bulk scholarship updates"""
        # Create test data
        scholarships = [
            Scholarship(
                title=f"Update Test {i}",
                provider="Test Provider",
                level="Undergraduate",
                field="STEM",
                location="Kenya",
                amount="1000 USD",
                deadline=timezone.now().date() + timedelta(days=100),
                status="Open"
            )
            for i in range(self.bulk_size)
        ]
        Scholarship.objects.bulk_create(scholarships)
        
        # Test bulk update performance
        start_time = time.time()
        updated_count = Scholarship.objects.filter(status="Open").update(status="Closed")
        end_time = time.time()
        
        update_time = end_time - start_time
        print(f"Bulk updated {updated_count} scholarships in {update_time:.2f} seconds")
        
        self.assertLess(update_time, 2.0, "Bulk update took too long")
        self.assertEqual(updated_count, self.bulk_size)
    
    def test_complex_queryset_performance(self):
        """Test performance of complex queryset operations"""
        # Create diverse test data
        for i in range(500):
            Scholarship.objects.create(
                title=f"Complex Query Test {i}",
                provider=f"University {i % 50}",
                level=random.choice(['Undergraduate', 'Masters', 'PhD']),
                field=random.choice(['STEM', 'Business']),
                location=random.choice(['Kenya', 'Global', 'USA']),
                amount=f"{random.randint(1000, 15000)} USD",
                deadline=timezone.now().date() + timedelta(days=random.randint(1, 180)),
                status=random.choice(['Open', 'Closing Soon'])
            )
        
        # Test complex filtering with multiple conditions
        start_time = time.time()
        
        complex_queryset = Scholarship.objects.filter(
            status="Open",
            level__in=['Undergraduate', 'Masters'],
            field="STEM",
            deadline__gte=timezone.now().date(),
            amount__icontains="USD"
        ).order_by('deadline')[:100]
        
        results = list(complex_queryset)
        end_time = time.time()
        
        query_time = end_time - start_time
        print(f"Complex query executed in {query_time:.2f} seconds, returned {len(results)} results")
        
        self.assertLess(query_time, 1.0, "Complex query took too long")
        self.assertLessEqual(len(results), 100)
    
    def test_ordering_performance(self):
        """Test performance of ordering operations"""
        # Create test data with varied deadlines
        for i in range(1000):
            Scholarship.objects.create(
                title=f"Ordering Test {i}",
                provider="Test Provider",
                level="Undergraduate",
                field="STEM",
                location="Kenya",
                amount="1000 USD",
                deadline=timezone.now().date() + timedelta(days=1000 - i),  # Varied deadlines
                status="Open"
            )
        
        # Test ordering performance
        start_time = time.time()
        ordered_scholarships = list(Scholarship.objects.all().order_by('deadline'))
        end_time = time.time()
        
        ordering_time = end_time - start_time
        print(f"Ordered {len(ordered_scholarships)} scholarships in {ordering_time:.2f} seconds")
        
        self.assertLess(ordering_time, 2.0, "Ordering operation took too long")
        
        # Verify ordering is correct
        deadlines = [s.deadline for s in ordered_scholarships]
        self.assertEqual(deadlines, sorted(deadlines))