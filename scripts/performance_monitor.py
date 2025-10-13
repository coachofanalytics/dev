#!/usr/bin/env python3
"""
Performance monitoring script for CODA automation system
"""

import os
import sys
import time
import psutil
import django
from django.core.management import execute_from_command_line
from django.conf import settings
from django.db import connection
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda.settings')
django.setup()

from accounts.models import Department
from finance.models import BudgetRequest, ApprovalPolicy, DisbursementRequest, AutomationAuditLog, BudgetCategory
from finance.services.automation_service import (
    BudgetRequestService, ApprovalEngineService, DisbursementService, AutomationAuditService
)


class PerformanceMonitor:
    """Performance monitoring for CODA automation system"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            'database_queries': 0,
            'api_requests': 0,
            'email_sends': 0,
            'errors': 0,
            'response_times': [],
            'memory_usage': [],
            'cpu_usage': []
        }
    
    def start_monitoring(self):
        """Start performance monitoring"""
        print("🔍 Starting performance monitoring...")
        self.start_time = time.time()
    
    def stop_monitoring(self):
        """Stop performance monitoring and generate report"""
        end_time = time.time()
        duration = end_time - self.start_time
        
        print(f"\n📊 Performance Report - Duration: {duration:.2f} seconds")
        print("=" * 60)
        
        # Database metrics
        print(f"📊 Database Queries: {self.metrics['database_queries']}")
        print(f"🌐 API Requests: {self.metrics['api_requests']}")
        print(f"📧 Email Sends: {self.metrics['email_sends']}")
        print(f"❌ Errors: {self.metrics['errors']}")
        
        # Response time metrics
        if self.metrics['response_times']:
            avg_response_time = sum(self.metrics['response_times']) / len(self.metrics['response_times'])
            max_response_time = max(self.metrics['response_times'])
            min_response_time = min(self.metrics['response_times'])
            
            print(f"\n⏱️  Response Times:")
            print(f"   Average: {avg_response_time:.2f}ms")
            print(f"   Maximum: {max_response_time:.2f}ms")
            print(f"   Minimum: {min_response_time:.2f}ms")
        
        # Memory metrics
        if self.metrics['memory_usage']:
            avg_memory = sum(self.metrics['memory_usage']) / len(self.metrics['memory_usage'])
            max_memory = max(self.metrics['memory_usage'])
            
            print(f"\n💾 Memory Usage:")
            print(f"   Average: {avg_memory:.2f}MB")
            print(f"   Maximum: {max_memory:.2f}MB")
        
        # CPU metrics
        if self.metrics['cpu_usage']:
            avg_cpu = sum(self.metrics['cpu_usage']) / len(self.metrics['cpu_usage'])
            max_cpu = max(self.metrics['cpu_usage'])
            
            print(f"\n🖥️  CPU Usage:")
            print(f"   Average: {avg_cpu:.2f}%")
            print(f"   Maximum: {max_cpu:.2f}%")
        
        # Performance recommendations
        self._generate_recommendations()
    
    def _generate_recommendations(self):
        """Generate performance recommendations"""
        print(f"\n💡 Performance Recommendations:")
        
        if self.metrics['database_queries'] > 100:
            print("   ⚠️  High database query count - consider query optimization")
        
        if self.metrics['response_times'] and max(self.metrics['response_times']) > 1000:
            print("   ⚠️  Slow response times - consider caching or optimization")
        
        if self.metrics['memory_usage'] and max(self.metrics['memory_usage']) > 500:
            print("   ⚠️  High memory usage - consider memory optimization")
        
        if self.metrics['cpu_usage'] and max(self.metrics['cpu_usage']) > 80:
            print("   ⚠️  High CPU usage - consider load balancing")
        
        if self.metrics['errors'] > 0:
            print(f"   ⚠️  {self.metrics['errors']} errors detected - review error logs")
    
    def record_database_query(self):
        """Record database query"""
        self.metrics['database_queries'] += 1
    
    def record_api_request(self, response_time):
        """Record API request"""
        self.metrics['api_requests'] += 1
        self.metrics['response_times'].append(response_time)
    
    def record_email_send(self):
        """Record email send"""
        self.metrics['email_sends'] += 1
    
    def record_error(self):
        """Record error"""
        self.metrics['errors'] += 1
    
    def record_system_metrics(self):
        """Record system metrics"""
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        
        self.metrics['memory_usage'].append(memory_info.used / 1024 / 1024)  # MB
        self.metrics['cpu_usage'].append(cpu_percent)


def test_database_performance():
    """Test database performance"""
    print("🗄️  Testing database performance...")
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Test database queries
    start_time = time.time()
    
    # Test model queries
    departments = list(Department.objects.all())
    categories = list(BudgetCategory.objects.all())
    policies = list(ApprovalPolicy.objects.all())
    requests = list(BudgetRequest.objects.all())
    disbursements = list(DisbursementRequest.objects.all())
    audit_logs = list(AutomationAuditLog.objects.all())
    
    # Test complex queries
    BudgetRequest.objects.filter(status='submitted').select_related('requester', 'department')
    ApprovalPolicy.objects.filter(is_active=True).prefetch_related('applicable_departments')
    DisbursementRequest.objects.filter(status='pending').select_related('budget_request')
    
    end_time = time.time()
    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
    
    monitor.record_database_query()
    monitor.record_api_request(response_time)
    monitor.record_system_metrics()
    
    print(f"   ✅ Database queries completed in {response_time:.2f}ms")
    
    monitor.stop_monitoring()


def test_service_performance():
    """Test service performance"""
    print("🔧 Testing service performance...")
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Test service operations
    budget_service = BudgetRequestService()
    approval_service = ApprovalEngineService()
    disbursement_service = DisbursementService()
    audit_service = AutomationAuditService()
    
    # Test budget request creation
    start_time = time.time()
    
    try:
        request_data = {
            'amount': '100.00',
            'purpose': 'Performance test request',
            'department': Department.objects.first().id,
            'required_date': (timezone.now().date() + timedelta(days=30)).isoformat(),
            'budget_category': BudgetCategory.objects.first().id,
            'priority': 'low',
            'cost_center': 'PERF001',
            'attachments': []
        }
        
        budget_request = budget_service.create_request(
            User.objects.first(), 
            request_data
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        monitor.record_api_request(response_time)
        monitor.record_system_metrics()
        
        print(f"   ✅ Budget request creation: {response_time:.2f}ms")
        
    except Exception as e:
        monitor.record_error()
        print(f"   ❌ Budget request creation failed: {str(e)}")
    
    # Test approval processing
    start_time = time.time()
    
    try:
        policy = ApprovalPolicy.objects.first()
        if policy:
            approval_service.get_applicable_policy(budget_request)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            monitor.record_api_request(response_time)
            monitor.record_system_metrics()
            
            print(f"   ✅ Approval processing: {response_time:.2f}ms")
        
    except Exception as e:
        monitor.record_error()
        print(f"   ❌ Approval processing failed: {str(e)}")
    
    # Test audit logging
    start_time = time.time()
    
    try:
        audit_service.log_action(
            action='performance_test',
            action_type='create',
            user=User.objects.first(),
            object=budget_request,
            details={'test': 'performance'}
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        monitor.record_api_request(response_time)
        monitor.record_system_metrics()
        
        print(f"   ✅ Audit logging: {response_time:.2f}ms")
        
    except Exception as e:
        monitor.record_error()
        print(f"   ❌ Audit logging failed: {str(e)}")
    
    monitor.stop_monitoring()


def test_email_performance():
    """Test email performance"""
    print("📧 Testing email performance...")
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Test email template rendering
    start_time = time.time()
    
    try:
        from django.template.loader import render_to_string
        
        context = {
            'user': User.objects.first(),
            'request': BudgetRequest.objects.first(),
            'site_name': 'CODA',
            'site_url': 'http://localhost:8000',
            'timestamp': timezone.now()
        }
        
        html = render_to_string('emails/budget_request_submitted.html', context)
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        monitor.record_api_request(response_time)
        monitor.record_email_send()
        monitor.record_system_metrics()
        
        print(f"   ✅ Email template rendering: {response_time:.2f}ms")
        
    except Exception as e:
        monitor.record_error()
        print(f"   ❌ Email template rendering failed: {str(e)}")
    
    monitor.stop_monitoring()


def test_concurrent_operations():
    """Test concurrent operations"""
    print("🔄 Testing concurrent operations...")
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    import threading
    import queue
    
    results = queue.Queue()
    
    def create_budget_request(thread_id):
        """Create budget request in thread"""
        try:
            start_time = time.time()
            
            request_data = {
                'amount': f'{100 + thread_id}.00',
                'purpose': f'Concurrent test request {thread_id}',
                'department': Department.objects.first().id,
                'required_date': (timezone.now().date() + timedelta(days=30)).isoformat(),
                'budget_category': BudgetCategory.objects.first().id,
                'priority': 'low',
                'cost_center': f'CONC{thread_id:03d}',
                'attachments': []
            }
            
            budget_service = BudgetRequestService()
            budget_request = budget_service.create_request(
                User.objects.first(), 
                request_data
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            results.put(('success', response_time))
            
        except Exception as e:
            results.put(('error', str(e)))
    
    # Create multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=create_budget_request, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Process results
    success_count = 0
    error_count = 0
    total_response_time = 0
    
    while not results.empty():
        result_type, data = results.get()
        if result_type == 'success':
            success_count += 1
            total_response_time += data
            monitor.record_api_request(data)
        else:
            error_count += 1
            monitor.record_error()
    
    if success_count > 0:
        avg_response_time = total_response_time / success_count
        print(f"   ✅ Concurrent operations: {success_count} success, {error_count} errors")
        print(f"   ⏱️  Average response time: {avg_response_time:.2f}ms")
    else:
        print(f"   ❌ All concurrent operations failed")
    
    monitor.record_system_metrics()
    monitor.stop_monitoring()


def test_memory_usage():
    """Test memory usage"""
    print("💾 Testing memory usage...")
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Test memory usage with large datasets
    start_time = time.time()
    
    try:
        # Create large number of objects
        budget_requests = []
        for i in range(100):
            request = BudgetRequest(
                requester=User.objects.first(),
                amount=Decimal('100.00'),
                currency='USD',
                purpose=f'Memory test request {i}',
                department=Department.objects.first(),
                budget_category=BudgetCategory.objects.first(),
                required_date=timezone.now().date() + timedelta(days=30),
                priority='low',
                created_by=User.objects.first(),
                last_modified_by=User.objects.first()
            )
            budget_requests.append(request)
        
        # Bulk create
        BudgetRequest.objects.bulk_create(budget_requests)
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        monitor.record_api_request(response_time)
        monitor.record_system_metrics()
        
        print(f"   ✅ Bulk creation: {response_time:.2f}ms")
        
        # Test memory usage
        memory_info = psutil.virtual_memory()
        print(f"   💾 Memory usage: {memory_info.used / 1024 / 1024:.2f}MB")
        print(f"   💾 Memory available: {memory_info.available / 1024 / 1024:.2f}MB")
        
    except Exception as e:
        monitor.record_error()
        print(f"   ❌ Memory test failed: {str(e)}")
    
    monitor.stop_monitoring()


def generate_performance_report():
    """Generate comprehensive performance report"""
    print("📊 Generating performance report...")
    
    report = {
        'timestamp': timezone.now().isoformat(),
        'system_info': {
            'python_version': sys.version,
            'django_version': django.get_version(),
            'platform': sys.platform
        },
        'database_info': {
            'total_requests': BudgetRequest.objects.count(),
            'total_disbursements': DisbursementRequest.objects.count(),
            'total_audit_logs': AutomationAuditLog.objects.count(),
            'total_policies': ApprovalPolicy.objects.count()
        },
        'performance_metrics': {}
    }
    
    # Test all performance aspects
    test_database_performance()
    test_service_performance()
    test_email_performance()
    test_concurrent_operations()
    test_memory_usage()
    
    # Save report
    report_path = 'performance_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"📄 Performance report saved to: {report_path}")


def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'database':
            test_database_performance()
        elif command == 'services':
            test_service_performance()
        elif command == 'email':
            test_email_performance()
        elif command == 'concurrent':
            test_concurrent_operations()
        elif command == 'memory':
            test_memory_usage()
        elif command == 'all':
            generate_performance_report()
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: database, services, email, concurrent, memory, all")
    else:
        print("🔍 CODA Automation System - Performance Monitor")
        print("\nUsage:")
        print("  python performance_monitor.py database   - Test database performance")
        print("  python performance_monitor.py services   - Test service performance")
        print("  python performance_monitor.py email      - Test email performance")
        print("  python performance_monitor.py concurrent - Test concurrent operations")
        print("  python performance_monitor.py memory     - Test memory usage")
        print("  python performance_monitor.py all        - Run all performance tests")


if __name__ == '__main__':
    main()
