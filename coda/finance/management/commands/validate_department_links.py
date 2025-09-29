"""
Simple link validation for department dashboard
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from django.urls import reverse, NoReverseMatch
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()


def validate_department_links():
    """Validate all department dashboard links"""
    print("🔍 Validating Department Dashboard Links...")
    
    # Test URLs that should work
    test_urls = {
        'Finance': [
            '/finance/',
            '/finance/finance-dashboard/coda/',
            '/finance/budget/coda/',
            '/finance/finance_report/',
            '/finance/investment_report/',
            '/finance/statements/',
            '/finance/pay/',
            '/finance/send_invoice/collection/',
            '/finance/payments/info/None/',
            '/finance/transact/',
            '/finance/enhanced-budget-dashboard/coda/',
            '/finance/investment-planning/coda/',
            '/finance/multi-year-planning/coda/',
            '/finance/weekly-planning/coda/',
            '/finance/monthly-planning/coda/',
            '/finance/yearly-planning/coda/',
            '/finance/consolidation-report/coda/',
            '/finance/automation/',
        ],
        'Management': [
            '/management/companyagenda/',
            '/management/meetings/company/',
            '/management/meetings/history/',
            '/management/newmeeting/',
            '/management/policies/',
            '/management/benefits/',
            '/management/policy/',
            '/management/payroll/',
            '/management/payslip/',
            '/management/tasks/',
            '/management/newtask/',
            '/management/newcategory/',
            '/management/newtaskgroup/',
        ],
        'HR': [
            '/management/departments/',
            '/management/assess/',
            '/management/assessment/employee/',
            '/management/employee_contract/',
            '/management/read_employee_contract/',
            '/management/confirm_employee_contract/',
            '/management/score_report/',
            '/management/backgroundchecklist/',
            '/professional_services/newjob/',
            '/professional_services/job_tracker/',
            '/professional_services/iuploads/',
            '/professional_services/train/',
        ],
        'IT': [
            '/main/it/',
            '/main/project/',
            '/ai_services/diaspora/advanced-analytics/',
            '/ai_services/diaspora/ai-configuration/',
            '/ai_services/diaspora/ai-health/',
            '/ai_services/diaspora/',
        ],
        'Marketing': [
            '/marketing/',
        ],
        'Security': [
            '/ai_services/diaspora/ai-health/',
            '/ai_services/diaspora/advanced-analytics/',
            '/ai_services/diaspora/ai-configuration/',
            '/management/policies/',
        ],
        'Health': [
            '/main/help/',
            '/main/contact/',
        ],
        'Other': [
            '/main/help/',
            '/main/contact/',
            '/main/system/maintenance/',
            '/main/help/new-features/',
        ]
    }
    
    # Create test client
    client = Client()
    
    # Create test user
    try:
        user, created = User.objects.get_or_create(
            username='test_admin',
            defaults={
                'email': 'admin@test.com',
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Test',
                'last_name': 'Admin'
            }
        )
        client.force_login(user)
        print(f"✅ Test user created: {user.username}")
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return
    
    # Test each department
    total_links = 0
    working_links = 0
    
    for department, urls in test_urls.items():
        print(f"\n📊 Testing {department} Department:")
        department_working = 0
        department_total = len(urls)
        total_links += department_total
        
        for url in urls:
            try:
                response = client.get(url)
                if response.status_code == 200:
                    print(f"  ✅ {url}")
                    working_links += 1
                    department_working += 1
                elif response.status_code == 302:
                    print(f"  ↪️  {url} (redirects)")
                    working_links += 1
                    department_working += 1
                elif response.status_code == 403:
                    print(f"  🔒 {url} (forbidden - may be expected)")
                    working_links += 1
                    department_working += 1
                elif response.status_code == 404:
                    print(f"  ❌ {url} (404 - not found)")
                else:
                    print(f"  ⚠️  {url} (status: {response.status_code})")
            except Exception as e:
                print(f"  ❌ {url} (error: {e})")
        
        success_rate = (department_working / department_total * 100) if department_total > 0 else 0
        print(f"  📈 {department}: {department_working}/{department_total} links working ({success_rate:.1f}%)")
    
    # Overall summary
    overall_success_rate = (working_links / total_links * 100) if total_links > 0 else 0
    print(f"\n🎯 Overall Summary:")
    print(f"  Total Links Tested: {total_links}")
    print(f"  Working Links: {working_links}")
    print(f"  Success Rate: {overall_success_rate:.1f}%")
    
    if overall_success_rate >= 80:
        print("  ✅ Department dashboard links are working well!")
    elif overall_success_rate >= 60:
        print("  ⚠️  Some department links need attention")
    else:
        print("  ❌ Significant link issues need to be fixed")
    
    # Recommendations
    print(f"\n📋 Recommendations:")
    print("  1. Fix any 404 errors by updating URL patterns")
    print("  2. Verify role-based access for restricted links")
    print("  3. Test with different user roles")
    print("  4. Update any broken internal links")
    
    return working_links, total_links


if __name__ == '__main__':
    validate_department_links()
