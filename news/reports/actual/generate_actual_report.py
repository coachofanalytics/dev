import os
import sys
import django
from io import StringIO
from datetime import datetime
import subprocess

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.test.utils import get_runner
from django.conf import settings
from django.test import TestCase
from django.core.management import call_command


def generate_actual_report():
    """
    Run the full test suite and generate actual_report.txt
    with detailed test results including name, status, time, and errors
    """
    
    # Prepare output file
    report_output = StringIO()
    report_path = os.path.join(
        os.path.dirname(__file__),
        'actual_report.txt'
    )
    
    report_output.write("=" * 70 + "\n")
    report_output.write(f"NEWS APP - ACTUAL TEST REPORT\n")
    report_output.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_output.write("=" * 70 + "\n\n")
    
    # Run tests using pytest (or Django test runner)
    print("Running tests...")
    
    # Capture test output
    test_output = StringIO()
    
    try:
        # Use Django's test runner
        from django.test.runner import DiscoverRunner
        runner = DiscoverRunner(verbosity=2, stream=test_output)
        test_labels = ['news.tests']
        result = runner.run_tests(test_labels)
        
        # Parse output
        output_str = test_output.getvalue()
        
        # Write raw output to report
        report_output.write("TEST EXECUTION OUTPUT:\n")
        report_output.write("-" * 70 + "\n")
        report_output.write(output_str)
        report_output.write("\n")
        report_output.write("-" * 70 + "\n\n")
        
        # Summary
        if result == 0:
            report_output.write("STATUS: ALL TESTS PASSED ✓\n")
            report_output.write(f"Failed tests: 0\n")
            report_output.write(f"Errors: 0\n")
        else:
            report_output.write(f"STATUS: TESTS FAILED ✗\n")
            report_output.write(f"Exit code: {result}\n")
        
    except Exception as e:
        report_output.write(f"ERROR RUNNING TESTS: {str(e)}\n")
        import traceback
        report_output.write(traceback.format_exc())
    
    # Write to file
    with open(report_path, 'w') as f:
        f.write(report_output.getvalue())
    
    print(f"✓ Actual report generated: {report_path}")
    print(report_output.getvalue())
    
    return report_path


if __name__ == '__main__':
    generate_actual_report()
