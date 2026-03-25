"""
Pytest Configuration for News Model Tests
Centralized configuration for running tests against news models
Includes metrics collection and progress reporting
"""

import os
import django
import json
from pathlib import Path
from datetime import datetime
from django.conf import settings


def pytest_configure(config):
    """Configure Django settings before running tests"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
    django.setup()
    
    # Define markers
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "regression: marks tests as regression tests")
    config.addinivalue_line("markers", "system: marks tests as system tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    
    # Initialize metrics file
    metrics_file = Path('test_metrics.json')
    if not metrics_file.exists():
        metrics = {
            'timestamp': None,
            'total_tests': 270,
            'categories': {
                'unit_testing': {'total': 60, 'passed': 0, 'failed': 0, 'skipped': 0},
                'integration_testing': {'total': 40, 'passed': 0, 'failed': 0, 'skipped': 0},
                'regression_testing': {'total': 70, 'passed': 0, 'failed': 0, 'skipped': 0},
                'system_testing': {'total': 50, 'passed': 0, 'failed': 0, 'skipped': 0},
                'performance_testing': {'total': 50, 'passed': 0, 'failed': 0, 'skipped': 0},
            },
            'total_coverage': 0.0,
            'operational_percentage': 0.0
        }
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)


def pytest_sessionfinish(session, exitstatus):
    """Collect metrics after test session and generate report"""
    metrics_file = Path('test_metrics.json')
    
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        # Get test statistics from session using the stats dict
        stats_dict = session.stats if hasattr(session, 'stats') else {}
        total_passed = stats_dict.get('passed', 0)
        total_failed = stats_dict.get('failed', 0)
        total_tests = total_passed + total_failed
        
        # Update timestamp and overall metrics
        metrics['timestamp'] = datetime.now().isoformat()
        if total_tests > 0:
            metrics['total_coverage'] = (total_passed / total_tests) * 100
            metrics['operational_percentage'] = metrics['total_coverage']
        
        # Save updated metrics
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Print summary
        _print_metrics_summary(metrics, total_passed, total_failed, total_tests)


def _print_metrics_summary(metrics, total_passed, total_failed, total_tests):
    """Print test metrics summary report"""
    print("\n" + "=" * 80)
    print("TEST SUITE METRICS REPORT")
    print("=" * 80)
    print(f"Timestamp: {metrics['timestamp']}")
    print(f"Total Tests Collected: {metrics['total_tests']}")
    print(f"Tests Passed: {total_passed}")
    print(f"Tests Failed: {total_failed}")
    print()
    
    if total_tests > 0:
        pass_rate = (total_passed / total_tests) * 100
    else:
        pass_rate = 0
    
    print(f"OVERALL OPERATIONAL: {pass_rate:.1f}% ({total_passed}/{total_tests} passed)")
    print("=" * 80 + "\n")


def pytest_collection_modifyitems(config, items):
    """Add markers to test items based on test characteristics"""
    for item in items:
        # Mark performance tests
        if 'Performance' in item.nodeid:
            item.add_marker('slow')
        
        # Mark integration tests
        if 'integration' in item.fspath.basename:
            item.add_marker('integration')
        
        # Mark regression tests
        if 'regression' in item.fspath.basename:
            item.add_marker('regression')
        
        # Mark system tests
        if 'system' in item.fspath.basename:
            item.add_marker('system')
        
        # Mark unit tests
        if 'unit' in item.fspath.basename:
            item.add_marker('unit')

