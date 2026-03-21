import os
import sys
import django
from datetime import datetime
from io import StringIO
import subprocess
import re

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.test.runner import DiscoverRunner


def generate_summary_report():
    """
    Generate a formatted summary report with test statistics
    showing pass rates and verdict
    """
    
    report_path = os.path.join(
        os.path.dirname(__file__),
        'summary_report.txt'
    )
    
    report_content = StringIO()
    
    # Header
    report_content.write("=" * 60 + "\n")
    report_content.write("PROJECT:    News Django Application\n")
    report_content.write(f"DATE:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_content.write("DEVELOPER:  DC48K Development Team\n")
    report_content.write("=" * 60 + "\n\n")
    
    # Run tests and capture results
    test_output = StringIO()
    test_results = {
        'unit': {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0},
        'integration': {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0},
        'regression': {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0},
        'system': {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0},
        'performance': {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0},
    }
    
    failing_tests = []
    total_executed = 0
    total_passed = 0
    total_failed = 0
    total_errors = 0
    
    try:
        # Run each test category
        test_modules = {
            'unit': 'news.tests.unit',
            'integration': 'news.tests.integration',
            'regression': 'news.tests.regression',
            'system': 'news.tests.system',
            'performance': 'news.tests.performance',
        }
        
        for test_type, test_label in test_modules.items():
            runner = DiscoverRunner(verbosity=2, stream=test_output, interactive=False)
            result = runner.run_tests([test_label])
            
            # Parse results from output
            output_str = test_output.getvalue()
            
            # Count tests from output
            # Look for patterns like "Ran X test" or "test ... ok"
            ran_match = re.search(r'Ran (\d+) test', output_str)
            if ran_match:
                num_tests = int(ran_match.group(1))
                test_results[test_type]['total'] = num_tests
                total_executed += num_tests
            
            if result == 0:
                test_results[test_type]['passed'] = test_results[test_type]['total']
                total_passed += test_results[test_type]['total']
            else:
                # Some tests failed
                failed_match = re.findall(r'FAIL: (test_\w+)', output_str)
                error_match = re.findall(r'ERROR: (test_\w+)', output_str)
                
                num_failed = len(failed_match)
                num_errors = len(error_match)
                
                test_results[test_type]['failed'] = num_failed
                test_results[test_type]['errors'] = num_errors
                test_results[test_type]['passed'] = (
                    test_results[test_type]['total'] - num_failed - num_errors
                )
                
                total_failed += num_failed
                total_errors += num_errors
                total_passed += test_results[test_type]['passed']
                
                for test_name in failed_match:
                    failing_tests.append(f"  - {test_type}/{test_name} FAILED")
                for test_name in error_match:
                    failing_tests.append(f"  - {test_type}/{test_name} ERROR")
        
    except Exception as e:
        report_content.write(f"ERROR RUNNING TESTS: {str(e)}\n")
        import traceback
        report_content.write(traceback.format_exc())
        report_content.write("\n\n")
    
    # Calculate statistics
    if total_executed == 0:
        report_content.write("Warning: No tests were executed. Check test configuration.\n\n")
    else:
        pass_rate = (total_passed / total_executed * 100) if total_executed > 0 else 0
        
        # Test statistics table
        report_content.write("Test Suite Statistics:\n")
        report_content.write("-" * 60 + "\n")
        report_content.write(f"{'Test Type':<15} | {'Total':<7} | {'Passed':<7} | {'Failed':<7} | {'Errors':<6} | {'Pass %':<6}\n")
        report_content.write("-" * 60 + "\n")
        
        for test_type in ['unit', 'integration', 'regression', 'system', 'performance']:
            data = test_results[test_type]
            if data['total'] > 0:
                pct = (data['passed'] / data['total'] * 100) if data['total'] > 0 else 0
                report_content.write(
                    f"{test_type:<15} | {data['total']:<7} | {data['passed']:<7} | "
                    f"{data['failed']:<7} | {data['errors']:<6} | {pct:>5.1f}%\n"
                )
        
        report_content.write("-" * 60 + "\n")
        
        if total_executed > 0:
            overall_pct = (total_passed / total_executed * 100)
            report_content.write(f"{'TOTAL':<15} | {total_executed:<7} | {total_passed:<7} | "
                               f"{total_failed:<7} | {total_errors:<6} | {overall_pct:>5.1f}%\n")
        
        report_content.write("\n")
        
        # Failing tests section
        if failing_tests:
            report_content.write("FAILING TESTS:\n")
            report_content.write("-" * 60 + "\n")
            for test_name in failing_tests:
                report_content.write(test_name + "\n")
            report_content.write("\n")
        
        # Verdict
        report_content.write("=" * 60 + "\n")
        if pass_rate == 100:
            report_content.write("VERDICT: ✓ READY FOR RELEASE\n")
            report_content.write("All tests passed successfully. Application is ready for deployment.\n")
        else:
            report_content.write("VERDICT: ✗ BLOCKED — See failing tests\n")
            report_content.write(f"Pass Rate: {overall_pct:.1f}% (Target: 100%)\n")
            report_content.write(f"Failing: {total_failed} FAILED, {total_errors} ERRORS\n")
        report_content.write("=" * 60 + "\n")
    
    # Write to file
    with open(report_path, 'w') as f:
        f.write(report_content.getvalue())
    
    print(f"✓ Summary report generated: {report_path}")
    print(report_content.getvalue())
    
    return report_path


if __name__ == '__main__':
    generate_summary_report()
