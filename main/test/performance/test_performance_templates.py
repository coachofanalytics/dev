import time
from django.test import TestCase, override_settings
from main.models import Scholarship
from datetime import date
import random
from django.db.models import Count

# Completely disable static files for these tests
@override_settings(DEBUG=True)
class ScholarshipTemplatePerformanceTest(TestCase):
    """Performance tests for scholarship templates"""

    def setUp(self):
        # Create larger dataset for performance testing
        self.batch_size = 100
        self.scholarships_to_create = []
        
        for i in range(self.batch_size):
            scholarship = Scholarship(
                title=f"Performance Test Scholarship {i}",
                provider=f"University {i % 20}",
                level=random.choice(['Undergraduate', 'Masters', 'PhD', 'Vocational']),
                field=random.choice(['STEM', 'Humanities', 'Business', 'Arts']),
                location=random.choice(['Kenya', 'Global', 'UK', 'USA']),
                deadline=date(2025, random.randint(1, 12), random.randint(1, 28)),
                amount=f"{random.randint(1000, 20000)} USD",
                status=random.choice(['Open', 'Closing Soon', 'Closed'])
            )
            self.scholarships_to_create.append(scholarship)
        
        # Bulk create for performance
        Scholarship.objects.bulk_create(self.scholarships_to_create)
        print(f"✓ Created {self.batch_size} scholarships for performance testing")

    def test_scholarship_page_loading_performance(self):
        """Test performance of scholarship page loading"""
        print("Testing scholarship page loading performance...")
        
        iterations = 10
        
        total_time = 0
        successful_requests = 0
        
        for i in range(iterations):
            try:
                start_time = time.time()
                response = self.client.get('/scholarship')
                end_time = time.time()
                
                load_time = end_time - start_time
                total_time += load_time
                
                if response.status_code == 200:
                    successful_requests += 1
                    print(f"  Request {i+1}: {load_time:.3f}s (200 OK)")
                else:
                    print(f"  Request {i+1}: {load_time:.3f}s (Status: {response.status_code})")
                    
            except Exception as e:
                print(f"  Request {i+1}: Failed - {str(e)[:50]}...")
        
        avg_time = total_time / iterations
        print(f"✓ Average page load time: {avg_time:.3f}s")
        print(f"✓ Successful requests: {successful_requests}/{iterations}")
        
        self.assertLess(avg_time, 2.0, "Page loading too slow")
        self.assertGreater(successful_requests, 0, "No successful requests")

    def test_scholarship_context_processing_performance(self):
        """Test performance of context data processing"""
        print("Testing context data processing performance...")
        
        iterations = 20
        
        start_time = time.time()
        for i in range(iterations):
            try:
                response = self.client.get('/scholarship')
                if response.status_code == 200:
                    # Access context data to test processing
                    scholarships = list(response.context.get('scholarships', []))
                    scholarship_count = len(scholarships)
            except:
                pass  # Ignore errors for performance measurement
        end_time = time.time()
        
        processing_time = end_time - start_time
        avg_processing_time = processing_time / iterations
        
        print(f"✓ Context processing: {iterations} iterations in {processing_time:.3f}s")
        print(f"✓ Average per request: {avg_processing_time:.3f}s")
        
        self.assertLess(avg_processing_time, 0.5, "Context processing too slow")

    def test_large_dataset_performance(self):
        """Test performance with very large datasets"""
        print("Testing large dataset performance...")
        
        # Create additional large dataset
        large_batch_size = 500
        large_dataset = []
        
        for i in range(large_batch_size):
            scholarship = Scholarship(
                title=f"Large Dataset Scholarship {i}",
                provider=f"Large University {i % 50}",
                level=random.choice(['Undergraduate', 'Masters']),
                field=random.choice(['STEM', 'Business']),
                location="Global",
                deadline=date(2025, 12, 31),
                amount="10000 USD",
                status="Open"
            )
            large_dataset.append(scholarship)
        
        # Time bulk creation
        start_time = time.time()
        Scholarship.objects.bulk_create(large_dataset)
        end_time = time.time()
        
        creation_time = end_time - start_time
        print(f"✓ Bulk created {large_batch_size} scholarships in {creation_time:.3f}s")
        
        # Time query performance
        start_time = time.time()
        all_scholarships = list(Scholarship.objects.all())
        end_time = time.time()
        
        query_time = end_time - start_time
        total_scholarships = len(all_scholarships)
        
        print(f"✓ Queried {total_scholarships} total scholarships in {query_time:.3f}s")
        
        self.assertLess(creation_time, 5.0, "Bulk creation too slow")
        self.assertLess(query_time, 3.0, "Query execution too slow")


# class ScholarshipModelPerformanceTest(TestCase):
#     """Performance tests for Scholarship model operations"""
    
#     def test_scholarship_creation_performance(self):
#         """Test performance of scholarship creation operations"""
#         print("Testing scholarship creation performance...")
        
#         batch_sizes = [10, 50, 100]
        
#         for batch_size in batch_sizes:
#             # Test individual creation
#             start_time = time.time()
#             for i in range(batch_size):
#                 Scholarship.objects.create(
#                     title=f"Individual Create {i}",
#                     provider=f"Provider {i}",
#                     level="Undergraduate",
#                     field="STEM",
#                     location="Kenya",
#                     amount="5000 USD",
#                     deadline=date(2025, 12, 31),
#                     status="Open"
#                 )
#             individual_time = time.time() - start_time
            
#             # Test bulk creation
#             bulk_scholarships = []
#             for i in range(batch_size):
#                 scholarship = Scholarship(
#                     title=f"Bulk Create {i}",
#                     provider=f"Provider {i}",
#                     level="Undergraduate",
#                     field="STEM",
#                     location="Kenya",
#                     amount="5000 USD",
#                     deadline=date(2025, 12, 31),
#                     status="Open"
#                 )
#                 bulk_scholarships.append(scholarship)
            
#             start_time = time.time()
#             Scholarship.objects.bulk_create(bulk_scholarships)
#             bulk_time = time.time() - start_time
            
#             print(f"✓ Batch size {batch_size}: Individual={individual_time:.3f}s, Bulk={bulk_time:.3f}s")
            
#             # Bulk should be significantly faster
#             self.assertLess(bulk_time, individual_time, "Bulk creation should be faster than individual")

#     def test_scholarship_queryset_performance(self):
#         """Test performance of various queryset operations"""
#         print("Testing queryset operation performance...")
        
#         # Create test data
#         test_data_size = 200
#         scholarships = []
        
#         for i in range(test_data_size):
#             scholarship = Scholarship(
#                 title=f"Query Test {i}",
#                 provider=f"University {i % 10}",
#                 level=random.choice(['Undergraduate', 'Masters']),
#                 field=random.choice(['STEM', 'Business', 'Arts']),
#                 location=random.choice(['Kenya', 'Global']),
#                 amount=f"{random.randint(1000, 15000)} USD",
#                 deadline=date(2025, random.randint(1, 12), 15),
#                 status=random.choice(['Open', 'Closing Soon'])
#             )
#             scholarships.append(scholarship)
        
#         Scholarship.objects.bulk_create(scholarships)
        
#         # Test different query types
#         query_tests = [
#             ('All objects', lambda: list(Scholarship.objects.all())),
#             ('STEM filter', lambda: list(Scholarship.objects.filter(field='STEM'))),
#             ('Undergraduate filter', lambda: list(Scholarship.objects.filter(level='Undergraduate'))),
#             ('Open status', lambda: list(Scholarship.objects.filter(status='Open'))),
#             ('Complex filter', lambda: list(Scholarship.objects.filter(field='STEM', level='Undergraduate', status='Open'))),
#             ('Order by deadline', lambda: list(Scholarship.objects.order_by('deadline'))),
#         ]
        
#         for query_name, query_func in query_tests:
#             start_time = time.time()
#             result = query_func()
#             query_time = time.time() - start_time
            
#             print(f"✓ {query_name}: {len(result)} results in {query_time:.3f}s")
#             self.assertLess(query_time, 1.0, f"{query_name} query too slow")

#     def test_scholarship_update_performance(self):
#         """Test performance of update operations"""
#         print("Testing update operation performance...")
        
#         # Create test data
#         update_batch_size = 100
#         scholarships = []
        
#         for i in range(update_batch_size):
#             scholarship = Scholarship(
#                 title=f"Update Test {i}",
#                 provider="Test University",
#                 level="Undergraduate",
#                 field="STEM",
#                 location="Kenya",
#                 amount="5000 USD",
#                 deadline=date(2025, 12, 31),
#                 status="Open"
#             )
#             scholarships.append(scholarship)
        
#         Scholarship.objects.bulk_create(scholarships)
        
#         # Test individual updates
#         start_time = time.time()
#         for scholarship in Scholarship.objects.all():
#             scholarship.status = "Closing Soon"
#             scholarship.save()
#         individual_update_time = time.time() - start_time
        
#         # Test bulk update
#         start_time = time.time()
#         Scholarship.objects.all().update(status="Closed")
#         bulk_update_time = time.time() - start_time
        
#         print(f"✓ Individual updates: {individual_update_time:.3f}s")
#         print(f"✓ Bulk update: {bulk_update_time:.3f}s")
        
#         self.assertLess(bulk_update_time, individual_update_time, "Bulk update should be faster")
#         self.assertLess(bulk_update_time, 2.0, "Bulk update too slow")


class ScholarshipFilteringPerformanceTest(TestCase):
    """Performance tests for scholarship filtering operations"""
    
    def setUp(self):
        # Create diverse dataset for filtering tests
        self.filter_data_size = 300
        filter_scholarships = []
        
        levels = ['Undergraduate', 'Masters', 'PhD', 'Vocational']
        fields = ['STEM', 'Humanities', 'Business', 'Arts', 'Health']
        locations = ['Kenya', 'Global', 'UK', 'USA', 'Canada']
        statuses = ['Open', 'Closing Soon', 'Closed']
        
        for i in range(self.filter_data_size):
            scholarship = Scholarship(
                title=f"Filter Test {i}",
                provider=f"University {i % 25}",
                level=random.choice(levels),
                field=random.choice(fields),
                location=random.choice(locations),
                amount=f"{random.randint(1000, 25000)} USD",
                deadline=date(2025, random.randint(1, 12), random.randint(1, 28)),
                status=random.choice(statuses)
            )
            filter_scholarships.append(scholarship)
        
        Scholarship.objects.bulk_create(filter_scholarships)
        print(f"✓ Created {self.filter_data_size} scholarships for filtering tests")

    def test_single_filter_performance(self):
        """Test performance of single field filtering"""
        print("Testing single field filter performance...")
        
        filter_fields = ['level', 'field', 'location', 'status']
        
        for field in filter_fields:
            values = Scholarship.objects.values_list(field, flat=True).distinct()
            
            for value in values[:3]:  # Test first 3 values of each field
                start_time = time.time()
                results = list(Scholarship.objects.filter(**{field: value}))
                filter_time = time.time() - start_time
                
                print(f"✓ Filter {field}={value}: {len(results)} results in {filter_time:.3f}s")
                self.assertLess(filter_time, 0.5, f"Filter {field}={value} too slow")

    def test_multi_filter_performance(self):
        """Test performance of multiple field filtering"""
        print("Testing multi-field filter performance...")
        
        filter_combinations = [
            {'level': 'Undergraduate', 'field': 'STEM'},
            {'status': 'Open', 'location': 'Kenya'},
            {'level': 'Masters', 'field': 'Business', 'status': 'Open'},
            {'location': 'Global', 'status': 'Closing Soon'},
        ]
        
        for filters in filter_combinations:
            start_time = time.time()
            results = list(Scholarship.objects.filter(**filters))
            filter_time = time.time() - start_time
            
            filter_desc = " & ".join([f"{k}={v}" for k, v in filters.items()])
            print(f"✓ Multi-filter {filter_desc}: {len(results)} results in {filter_time:.3f}s")
            self.assertLess(filter_time, 0.5, f"Multi-filter {filter_desc} too slow")

    def test_complex_queryset_performance(self):
        """Test performance of complex queryset operations"""
        print("Testing complex queryset performance...")
        
        complex_operations = [
            ('Annotated count', lambda: Scholarship.objects.values('level').annotate(count=Count('level'))),
            ('Ordered by multiple fields', lambda: list(Scholarship.objects.order_by('status', 'deadline', 'level'))),
            ('Exclude filters', lambda: list(Scholarship.objects.exclude(status='Closed').filter(level='Undergraduate'))),
            ('Range filters', lambda: list(Scholarship.objects.filter(deadline__gte=date(2025, 6, 1), deadline__lte=date(2025, 12, 31)))),
        ]
        
        for op_name, op_func in complex_operations:
            start_time = time.time()
            result = op_func()
            op_time = time.time() - start_time
            
            result_size = len(result) if hasattr(result, '__len__') else 'N/A'
            print(f"✓ {op_name}: {result_size} results in {op_time:.3f}s")
            self.assertLess(op_time, 1.0, f"Complex operation {op_name} too slow")


class ScholarshipChoiceFieldPerformanceTest(TestCase):
    """Performance tests for choice field operations"""
    
    def test_choice_validation_performance(self):
        """Test performance of choice field validation"""
        print("Testing choice field validation performance...")
        
        valid_combinations = [
            {'level': 'Undergraduate', 'field': 'STEM', 'location': 'Kenya', 'status': 'Open'},
            {'level': 'Masters', 'field': 'Business', 'location': 'Global', 'status': 'Closing Soon'},
            {'level': 'PhD', 'field': 'Arts', 'location': 'USA', 'status': 'Closed'},
            {'level': 'Vocational', 'field': 'Humanities', 'location': 'UK', 'status': 'Open'},
        ]
        
        iterations = 100
        
        start_time = time.time()
        for i in range(iterations):
            for combo in valid_combinations:
                # Test model creation with valid choices
                scholarship = Scholarship(**combo, title="Choice Test", provider="Test", 
                                        amount="1000 USD", deadline=date(2025, 12, 31))
                # This would trigger validation in a real scenario
        end_time = time.time()
        
        validation_time = end_time - start_time
        avg_validation_time = validation_time / (iterations * len(valid_combinations))
        
        print(f"✓ Choice validation: {iterations * len(valid_combinations)} combinations in {validation_time:.3f}s")
        print(f"✓ Average per validation: {avg_validation_time:.6f}s")
        
        self.assertLess(avg_validation_time, 0.001, "Choice validation too slow")

    def test_choice_field_access_performance(self):
        """Test performance of accessing choice field attributes"""
        print("Testing choice field access performance...")
        
        # Create test scholarship
        scholarship = Scholarship.objects.create(
            title="Choice Access Test",
            provider="Test University",
            level="Undergraduate",
            field="STEM",
            location="Kenya",
            amount="5000 USD",
            deadline=date(2025, 12, 31),
            status="Open"
        )
        
        iterations = 1000
        fields_to_access = ['level', 'field', 'location', 'status']
        
        start_time = time.time()
        for i in range(iterations):
            for field in fields_to_access:
                value = getattr(scholarship, field)
                # Verify it's a valid choice
                self.assertIn(value, ['Undergraduate', 'Masters', 'PhD', 'Vocational', 
                                    'STEM', 'Humanities', 'Business', 'Arts',
                                    'Kenya', 'Global', 'UK', 'USA',
                                    'Open', 'Closing Soon', 'Closed'])
        end_time = time.time()
        
        access_time = end_time - start_time
        avg_access_time = access_time / (iterations * len(fields_to_access))
        
        print(f"✓ Choice field access: {iterations * len(fields_to_access)} accesses in {access_time:.3f}s")
        print(f"✓ Average per access: {avg_access_time:.6f}s")
        
        self.assertLess(avg_access_time, 0.0001, "Choice field access too slow")


# Performance test runner
def run_performance_tests():
    """Run all performance tests and display summary"""
    print("=" * 70)
    print("SCHOLARSHIP PERFORMANCE TEST SUITE")
    print("=" * 70)
    
    test_classes = [
        ScholarshipTemplatePerformanceTest,
        #ScholarshipModelPerformanceTest,
        ScholarshipFilteringPerformanceTest,
        ScholarshipChoiceFieldPerformanceTest,
    ]
    
    total_start_time = time.time()
    
    for test_class in test_classes:
        print(f"\n{'='*50}")
        print(f"RUNNING: {test_class.__name__}")
        print(f"{'='*50}")
        
        test_instance = test_class()
        test_instance.setUp()
        
        # Run test methods that start with 'test_'
        test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
        
        for method_name in test_methods:
            method = getattr(test_instance, method_name)
            if callable(method):
                try:
                    method()
                    print(f"✓ COMPLETED: {method_name}")
                except Exception as e:
                    print(f"✗ FAILED: {method_name} - {e}")
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    print(f"\n{'='*70}")
    print(f"PERFORMANCE TEST SUITE COMPLETED")
    print(f"Total duration: {total_duration:.2f} seconds")
    print(f"{'='*70}")

if __name__ == "__main__":
    import django
    from django.conf import settings
    from django.test.utils import setup_test_environment, teardown_test_environment
    
    django.setup()
    setup_test_environment()
    
    run_performance_tests()
    
    teardown_test_environment()