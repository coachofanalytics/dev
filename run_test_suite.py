#!/usr/bin/env python
"""
Unified test runner and report generator for news app tests
"""
import os
import sys
import django
from datetime import datetime
from io import StringIO

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.test.runner import DiscoverRunner
from django.conf import settings

def run_tests_and_generate_reports():
    """Run tests and generate both actual and summary reports"""
    
    print("="*70)
    print("NEWS APP TEST SUITE EXECUTION")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Test results storage
    test_results = {
        'unit': [],
        'integration': [],
        'regression': [],
        'system': [],
        'performance': [],
    }
    
    passed = failed = errors = 0
    
    test_modules = {
        'unit': 'news.tests.unit',
        'integration': 'news.tests.integration',
        'regression': 'news.tests.regression',
        'system': 'news.tests.system',
        'performance': 'news.tests.performance',
    }
    
    for test_type, test_label in test_modules.items():
        print(f"\n[{test_type.upper()}] Running tests from {test_label}...")
        output = StringIO()
        runner = DiscoverRunner(verbosity=2, stream=output, interactive=False, keepdb=False)
        result = runner.run_tests([test_label])
        
        if result == 0:
            print(f"✓ All {test_type} tests passed")
        else:
            print(f"✗ Some {test_type} tests failed (exit code: {result})")
        
        output_text = output.getvalue()
        test_results[test_type] = output_text
    
    print("\n" + "="*70)
    print("TEST EXECUTION COMPLETE")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Generate reports
    print("\nGenerating reports...")
    generate_actual_report(test_results)
    generate_summary_report(test_results)
    
    print("✓ Reports generated successfully!")
    print("  - reports/actual/actual_report.txt")
    print("  - reports/summary/summary_report.txt")

def generate_actual_report(test_results):
    """Generate detailed actual report"""
    report_path = os.path.join(os.path.dirname(__file__), '../actual/actual_report.txt')
    
    with open(report_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("NEWS APP - ACTUAL TEST REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n\n")
        
        for test_type, output in test_results.items():
            f.write(f"\n[{test_type.upper()}] Test Results:\n")
            f.write("-"*70 + "\n")
            f.write(output)
            f.write("\n")

def generate_summary_report(test_results):
    """Generate formatted summary report"""
    report_path = os.path.join(os.path.dirname(__file__), '../summary/summary_report.txt')
    
    # Parse test counts
    stats = {}
    total_tests = total_passed = 0
    
    for test_type, output in test_results.items():
        # Simple parsing - look for "Ran X tests" pattern
        import re
        match = re.search(r'Ran (\d+) test', output)
        if match:
            num_tests = int(match.group(1))
            stats[test_type] = {
                'total': num_tests,
                'passed': num_tests if 'FAILED' not in output and 'ERROR' not in output else 0,
                'failed': 1 if 'FAILED' in output else 0,
                'errors': 1 if 'ERROR' in output else 0,
            }
            total_tests += num_tests
            if stats[test_type]['passed'] > 0:
                total_passed += stats[test_type]['total']
        else:
            stats[test_type] = {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0}
    
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    with open(report_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("PROJECT:    News Django Application\n")
        f.write(f"DATE:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("DEVELOPER:  DC48K Development Team\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("Test Suite Statistics:\n")
        f.write("-" * 60 + "\n")
        f.write(f"{'Test Type':<15} | {'Total':<7} | {'Passed':<7} | {'Failed':<7} | {'Pass %':<6}\n")
        f.write("-" * 60 + "\n")
        
        for test_type in ['unit', 'integration', 'regression', 'system', 'performance']:
            if test_type in stats:
                data = stats[test_type]
                pct = (data['passed'] / data['total'] * 100) if data['total'] > 0 else 0
                f.write(f"{test_type:<15} | {data['total']:<7} | {data['passed']:<7} | "
                       f"{data['failed']:<7} | {pct:>5.1f}%\n")
        
        f.write("-" * 60 + "\n")
        f.write(f"{'TOTAL':<15} | {total_tests:<7} | {total_passed:<7} | "
               f"{total_tests - total_passed:<7} | {pass_rate:>5.1f}%\n")
        f.write("\n")
        
        f.write("=" * 60 + "\n")
        if pass_rate >= 100:
            f.write("VERDICT: ✓ READY FOR RELEASE\n")
            f.write("All tests passed successfully. Application is ready for deployment.\n")
        elif pass_rate >= 90:
            f.write(f"VERDICT: ◐ MOSTLY READY (Pass Rate: {pass_rate:.1f}%)\n")
            f.write("Minor test failures present but application may be deployable.\n")
        else:
            f.write("VERDICT: ✗ BLOCKED — See failing tests\n")
            f.write(f"Pass Rate: {pass_rate:.1f}% (Target: 100%)\n")
        f.write("=" * 60 + "\n")

if __name__ == '__main__':
    run_tests_and_generate_reports()
