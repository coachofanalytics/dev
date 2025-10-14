"""
Management command to validate data quality and generate reports.

This command runs comprehensive data validation and provides actionable insights.
"""

import json
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from management.services.data_validation_service import DataValidationService


class Command(BaseCommand):
    help = 'Validate data quality and generate comprehensive reports'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            choices=['text', 'json', 'detailed'],
            default='text',
            help='Output format: text, json, or detailed'
        )
        parser.add_argument(
            '--output-file',
            type=str,
            help='Save results to file (JSON format)'
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=80.0,
            help='Quality score threshold for warnings (default: 80.0)'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        format_type = options['format']
        output_file = options.get('output_file')
        threshold = options['threshold']
        
        self.stdout.write(
            self.style.SUCCESS('Starting Data Quality Validation')
        )
        self.stdout.write('=' * 60)
        
        try:
            # Initialize validation service
            validation_service = DataValidationService()
            
            # Run validation
            self.stdout.write('Running comprehensive data validation...')
            validation_results = validation_service.validate_task_history_data()
            
            # Check if quality score meets threshold
            quality_score = validation_results['overall_score']
            if quality_score < threshold:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Data quality score ({quality_score:.1f}) is below threshold ({threshold})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Data quality score ({quality_score:.1f}) meets threshold ({threshold})'
                    )
                )
            
            # Output results based on format
            if format_type == 'json':
                self._output_json(validation_results)
            elif format_type == 'detailed':
                self._output_detailed(validation_results)
            else:
                self._output_text(validation_results)
            
            # Save to file if requested
            if output_file:
                self._save_to_file(validation_results, output_file)
            
            # Summary
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Data validation completed successfully! '
                    f'Quality Score: {quality_score:.1f}/100'
                )
            )
            
            # Action items
            critical_issues = len([i for i in validation_results['issues'] if i['severity'] == 'critical'])
            if critical_issues > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f'🚨 {critical_issues} critical issues require immediate attention'
                    )
                )
            
            total_issues = len(validation_results['issues']) + len(validation_results['warnings'])
            if total_issues > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'📋 {total_issues} total issues and warnings found'
                    )
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nData validation failed: {str(e)}')
            )
            raise CommandError(f'Data validation failed: {str(e)}')
    
    def _output_text(self, results):
        """Output results in human-readable text format."""
        self.stdout.write('\nDATA QUALITY VALIDATION RESULTS')
        self.stdout.write('=' * 60)
        
        # Overall score
        self.stdout.write(f'Overall Quality Score: {results["overall_score"]:.1f}/100')
        self.stdout.write(f'Validation Timestamp: {results["timestamp"]}')
        
        # Summary
        self.stdout.write(f'\nSUMMARY:')
        self.stdout.write(f'  Issues: {len(results["issues"])}')
        self.stdout.write(f'  Warnings: {len(results["warnings"])}')
        self.stdout.write(f'  Recommendations: {len(results["recommendations"])}')
        
        # Critical issues
        critical_issues = [i for i in results['issues'] if i['severity'] == 'critical']
        if critical_issues:
            self.stdout.write(f'\n🚨 CRITICAL ISSUES:')
            for issue in critical_issues:
                self.stdout.write(f'  • {issue["message"]}')
                self.stdout.write(f'    Fix: {issue["fix_suggestion"]}')
        
        # High priority issues
        high_issues = [i for i in results['issues'] if i['severity'] == 'high']
        if high_issues:
            self.stdout.write(f'\n⚠️  HIGH PRIORITY ISSUES:')
            for issue in high_issues:
                self.stdout.write(f'  • {issue["message"]}')
                self.stdout.write(f'    Fix: {issue["fix_suggestion"]}')
        
        # Top warnings
        if results['warnings']:
            self.stdout.write(f'\n📋 TOP WARNINGS:')
            for warning in results['warnings'][:5]:
                self.stdout.write(f'  • {warning["message"]}')
        
        # Recommendations
        if results['recommendations']:
            self.stdout.write(f'\n💡 RECOMMENDATIONS:')
            for rec in results['recommendations']:
                self.stdout.write(f'  [{rec["priority"].upper()}] {rec["title"]}')
                self.stdout.write(f'    {rec["description"]}')
                self.stdout.write(f'    Action: {rec["action"]}')
        
        # Metrics
        if results['metrics']:
            self.stdout.write(f'\n📊 DATA METRICS:')
            metrics = results['metrics']
            self.stdout.write(f'  Total Records: {metrics.get("total_records", 0):,}')
            self.stdout.write(f'  Date Coverage: {metrics.get("date_coverage_percentage", 0):.1f}%')
            self.stdout.write(f'  Employee Coverage: {metrics.get("employee_coverage_percentage", 0):.1f}%')
            self.stdout.write(f'  Category Coverage: {metrics.get("category_coverage_percentage", 0):.1f}%')
            
            if 'average_completion_rate' in metrics:
                self.stdout.write(f'  Average Completion Rate: {metrics["average_completion_rate"]:.1f}%')
    
    def _output_detailed(self, results):
        """Output detailed results with full information."""
        self._output_text(results)
        
        # Additional detailed information
        self.stdout.write(f'\n🔍 DETAILED ANALYSIS:')
        
        # All issues
        if results['issues']:
            self.stdout.write(f'\nALL ISSUES:')
            for i, issue in enumerate(results['issues'], 1):
                self.stdout.write(f'  {i}. [{issue["severity"].upper()}] {issue["type"]}')
                self.stdout.write(f'     Message: {issue["message"]}')
                self.stdout.write(f'     Affected Records: {issue["affected_records"]:,}')
                self.stdout.write(f'     Fix Suggestion: {issue["fix_suggestion"]}')
        
        # All warnings
        if results['warnings']:
            self.stdout.write(f'\nALL WARNINGS:')
            for i, warning in enumerate(results['warnings'], 1):
                self.stdout.write(f'  {i}. [{warning["severity"].upper()}] {warning["type"]}')
                self.stdout.write(f'     Message: {warning["message"]}')
                self.stdout.write(f'     Affected Records: {warning["affected_records"]:,}')
                self.stdout.write(f'     Fix Suggestion: {warning["fix_suggestion"]}')
    
    def _output_json(self, results):
        """Output results in JSON format."""
        # Convert datetime objects to strings for JSON serialization
        json_results = json.loads(json.dumps(results, default=str))
        self.stdout.write(json.dumps(json_results, indent=2))
    
    def _save_to_file(self, results, output_file):
        """Save results to a JSON file."""
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.stdout.write(f'\n💾 Results saved to: {output_file}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to save results to file: {e}')
            )


