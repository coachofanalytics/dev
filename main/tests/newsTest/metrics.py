"""
Test Metrics Collection and Reporting
Tracks test execution, coverage, and system operational status
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class TestMetricsCollector:
    """Collects and reports test execution metrics"""

    def __init__(self):
        self.metrics_file = Path('test_metrics.json')
        self.metrics = self._load_metrics()

    def _load_metrics(self) -> Dict:
        """Load existing metrics or create new"""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return {
            'timestamp': None,
            'total_tests': 270,
            'categories': {
                'unit_testing': {'total': 60, 'passed': 0, 'failed': 0, 'skipped': 0},
                'integration_testing': {'total': 40, 'passed': 0, 'failed': 0, 'skipped': 0},
                'regression_testing': {'total': 70, 'passed': 0, 'failed': 0, 'skipped': 0},
                'system_testing': {'total': 50, 'passed': 0, 'failed': 0, 'skipped': 0},
                'performance_testing': {'total': 50, 'passed': 0, 'failed': 0, 'skipped': 0},
            },
            'coverage': {
                'main': 0.0,
                'models': 0.0,
                'signals': 0.0,
                'admin': 0.0,
                'views': 0.0,
            }
        }

    def save_metrics(self):
        """Save metrics to file"""
        self.metrics['timestamp'] = datetime.now().isoformat()
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)

    def update_category_results(self, category: str, passed: int, failed: int, skipped: int = 0):
        """Update test results for a category"""
        if category in self.metrics['categories']:
            self.metrics['categories'][category].update({
                'passed': passed,
                'failed': failed,
                'skipped': skipped
            })

    def update_coverage(self, module: str, percentage: float):
        """Update coverage percentage for a module"""
        if module in self.metrics['coverage']:
            self.metrics['coverage'][module] = percentage

    def get_operational_percentage(self) -> float:
        """Calculate overall operational percentage (tests passing)"""
        total_passed = sum(
            cat['passed'] for cat in self.metrics['categories'].values()
        )
        total_tests = self.metrics['total_tests']
        return (total_passed / total_tests * 100) if total_tests > 0 else 0

    def get_category_percentage(self, category: str) -> float:
        """Get operational percentage for specific category"""
        if category not in self.metrics['categories']:
            return 0
        cat = self.metrics['categories'][category]
        total = cat['total']
        passed = cat['passed']
        return (passed / total * 100) if total > 0 else 0

    def print_report(self):
        """Print formatted test metrics report"""
        print("\n" + "=" * 70)
        print("TEST SUITE METRICS REPORT")
        print("=" * 70)
        print(f"Last Updated: {self.metrics['timestamp']}")
        print(f"Total Tests: {self.metrics['total_tests']}")
        print()

        print("CATEGORY BREAKDOWN:")
        print("-" * 70)
        for category, data in self.metrics['categories'].items():
            total = data['total']
            passed = data['passed']
            failed = data['failed']
            percentage = (passed / total * 100) if total > 0 else 0
            
            status = "✅" if percentage == 100 else "⚠️ " if percentage >= 80 else "❌"
            print(f"{status} {category:25} | {passed}/{total} passed | {percentage:6.1f}%")

        print()
        print(f"OVERALL OPERATIONAL: {self.get_operational_percentage():.1f}%")
        print()

        print("CODE COVERAGE:")
        print("-" * 70)
        for module, percentage in self.metrics['coverage'].items():
            status = "✅" if percentage >= 95 else "⚠️ " if percentage >= 80 else "❌"
            print(f"{status} {module:25} | {percentage:6.1f}%")

        print("=" * 70 + "\n")

    def get_status_badge(self) -> str:
        """Get status badge for documentation"""
        percentage = self.get_operational_percentage()
        if percentage >= 95:
            return f"✅ OPERATIONAL: {percentage:.1f}%"
        elif percentage >= 80:
            return f"⚠️  CAUTION: {percentage:.1f}%"
        else:
            return f"❌ NEEDS WORK: {percentage:.1f}%"


def create_metrics_dashboard():
    """Create a metrics dashboard"""
    collector = TestMetricsCollector()
    
    # Sample metrics (in real scenario, these would come from test run)
    collector.update_category_results('unit_testing', 60, 0)
    collector.update_category_results('integration_testing', 40, 0)
    collector.update_category_results('regression_testing', 70, 0)
    collector.update_category_results('system_testing', 50, 0)
    collector.update_category_results('performance_testing', 50, 0)
    
    collector.update_coverage('main', 95.2)
    collector.update_coverage('models', 98.5)
    collector.update_coverage('signals', 92.3)
    collector.update_coverage('admin', 87.6)
    collector.update_coverage('views', 91.4)
    
    collector.save_metrics()
    collector.print_report()
    
    return collector


if __name__ == '__main__':
    collector = create_metrics_dashboard()
