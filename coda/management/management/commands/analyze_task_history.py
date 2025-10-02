"""
Management command to analyze TaskHistory data.

This command implements Phase 1 (Week 3-4): Data Collection & Analysis
"""

import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone

from management.services.taskhistory_analyzer import TaskHistoryAnalyzer


class Command(BaseCommand):
    help = 'Analyze TaskHistory data for performance patterns and insights (Phase 1 - Week 3-4)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--months',
            type=int,
            default=12,
            help='Number of months to analyze (default: 12)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Output file path for JSON export (optional)'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'text', 'both'],
            default='text',
            help='Output format: json, text, or both'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        months = options['months']
        output_file = options['output']
        output_format = options['format']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting TaskHistory Analysis (Last {months} months)')
        )
        self.stdout.write('=' * 60)
        
        try:
            # Initialize analyzer
            analyzer = TaskHistoryAnalyzer()
            
            # Perform analysis
            self.stdout.write('\nAnalyzing performance patterns...')
            analysis_result = analyzer.analyze_complete_performance_patterns(months_back=months)
            
            if not analysis_result.get('success'):
                raise CommandError(f"Analysis failed: {analysis_result.get('error', 'Unknown error')}")
            
            # Display results based on format
            if output_format in ['text', 'both']:
                self._display_text_results(analysis_result, verbose)
            
            if output_format in ['json', 'both']:
                if output_file:
                    self._save_json_results(analysis_result, output_file)
                else:
                    self.stdout.write('\nJSON Output:')
                    self.stdout.write(json.dumps(analysis_result, indent=2, default=str))
            
            self.stdout.write(
                self.style.SUCCESS('\nAnalysis completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nAnalysis failed: {str(e)}')
            )
            raise CommandError(f'Analysis failed: {str(e)}')
    
    def _display_text_results(self, analysis_result, verbose=False):
        """Display analysis results in text format."""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.HTTP_INFO('TASKHISTORY PERFORMANCE ANALYSIS'))
        self.stdout.write('=' * 60)
        
        # Summary Statistics
        self.stdout.write('\nSUMMARY STATISTICS:')
        self.stdout.write('-' * 40)
        self.stdout.write(f"Total Records Analyzed: {analysis_result.get('total_records', 0):,}")
        self.stdout.write(f"Analysis Period: {analysis_result.get('months_analyzed', 0)} months")
        self.stdout.write(f"Date Range: {analysis_result.get('date_range', {}).get('start_date')} to {analysis_result.get('date_range', {}).get('end_date')}")
        
        # Employee Performance
        employee_perf = analysis_result.get('employee_performance', {})
        self.stdout.write('\nEMPLOYEE PERFORMANCE:')
        self.stdout.write('-' * 40)
        self.stdout.write(f"Total Employees: {employee_perf.get('total_employees', 0)}")
        self.stdout.write(f"Average Tasks per Employee: {employee_perf.get('average_tasks_per_employee', 0):.1f}")
        self.stdout.write(f"Average Completion Rate: {employee_perf.get('average_completion_rate', 0):.1%}")
        
        # Top Performers
        if verbose and employee_perf.get('top_performers'):
            self.stdout.write('\nTop Performers:')
            for i, performer in enumerate(employee_perf['top_performers'][:5], 1):
                self.stdout.write(
                    f"  {i}. {performer.get('employee__username', 'Unknown')}: "
                    f"{performer.get('total_tasks', 0)} tasks, "
                    f"${performer.get('total_earnings', 0):,.2f} earnings"
                )
        
        # Department Analysis
        dept_analysis = analysis_result.get('department_analysis', {})
        self.stdout.write('\nDEPARTMENT ANALYSIS:')
        self.stdout.write('-' * 40)
        self.stdout.write(f"Total Departments: {dept_analysis.get('total_departments', 0)}")
        
        if dept_analysis.get('top_department'):
            top_dept = dept_analysis['top_department']
            self.stdout.write(
                f"Top Department: {top_dept.get('employee__department__name', 'Unknown')} "
                f"({top_dept.get('total_tasks', 0)} tasks, ${top_dept.get('total_earnings', 0):,.2f})"
            )
        
        # Category Analysis
        category_analysis = analysis_result.get('category_analysis', {})
        self.stdout.write('\nCATEGORY ANALYSIS:')
        self.stdout.write('-' * 40)
        self.stdout.write(f"Total Categories: {category_analysis.get('total_categories', 0)}")
        
        if category_analysis.get('most_common_category'):
            top_cat = category_analysis['most_common_category']
            self.stdout.write(
                f"Most Common: {top_cat.get('category__title', 'Unknown')} "
                f"({top_cat.get('total_tasks', 0)} tasks)"
            )
        
        # Completion Rates
        completion = analysis_result.get('completion_rates', {})
        self.stdout.write('\nCOMPLETION RATES:')
        self.stdout.write('-' * 40)
        self.stdout.write(f"Overall: {completion.get('overall_completion_rate', 0):.1%}")
        self.stdout.write(f"High Performance Tasks: {completion.get('high_performance_percentage', 0):.1%}")
        self.stdout.write(f"Low Performance Tasks: {completion.get('low_performance_percentage', 0):.1%}")
        
        # Earning Patterns
        earnings = analysis_result.get('earning_patterns', {})
        self.stdout.write('\nEARNING PATTERNS:')
        self.stdout.write('-' * 40)
        self.stdout.write(f"Total Earnings: ${earnings.get('total_earnings', 0):,.2f}")
        self.stdout.write(f"Average per Task: ${earnings.get('average_earnings_per_task', 0):,.2f}")
        self.stdout.write(f"Range: ${earnings.get('min_earnings', 0):,.2f} - ${earnings.get('max_earnings', 0):,.2f}")
        
        # Key Insights
        insights = analysis_result.get('key_insights', [])
        if insights:
            self.stdout.write('\nKEY INSIGHTS:')
            self.stdout.write('-' * 40)
            for i, insight in enumerate(insights, 1):
                priority_style = (
                    self.style.ERROR if insight.get('priority') == 'critical'
                    else self.style.WARNING if insight.get('priority') == 'high'
                    else self.style.HTTP_INFO
                )
                self.stdout.write(
                    priority_style(f"{i}. [{insight.get('priority', 'medium').upper()}] {insight.get('title', 'Insight')}")
                )
                self.stdout.write(f"   {insight.get('description', 'No description')}")
        
        # Recommendations
        recommendations = analysis_result.get('actionable_recommendations', [])
        if recommendations:
            self.stdout.write('\nACTIONABLE RECOMMENDATIONS:')
            self.stdout.write('-' * 40)
            for i, rec in enumerate(recommendations, 1):
                priority_style = (
                    self.style.ERROR if rec.get('priority') == 'critical'
                    else self.style.WARNING if rec.get('priority') == 'high'
                    else self.style.HTTP_INFO
                )
                self.stdout.write(
                    priority_style(f"{i}. [{rec.get('priority', 'medium').upper()}] {rec.get('title', 'Recommendation')}")
                )
                self.stdout.write(f"   {rec.get('description', 'No description')}")
                self.stdout.write(f"   Action: {rec.get('action', 'N/A')}")
        
        # AI Enhanced Insights
        ai_insights = analysis_result.get('ai_enhanced_insights')
        if ai_insights:
            self.stdout.write('\nAI-ENHANCED INSIGHTS:')
            self.stdout.write('-' * 40)
            self.stdout.write(f"AI Summary: {ai_insights.get('ai_summary', 'N/A')}")
            self.stdout.write(f"Confidence Score: {ai_insights.get('confidence_score', 0):.1%}")
            self.stdout.write(f"Model Used: {ai_insights.get('model_used', 'Unknown')}")
            
            if verbose and ai_insights.get('ai_recommendations'):
                self.stdout.write('\nAI Recommendations:')
                for rec in ai_insights['ai_recommendations']:
                    self.stdout.write(f"  - {rec}")
    
    def _save_json_results(self, analysis_result, output_file):
        """Save analysis results to JSON file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(analysis_result, f, indent=2, default=str)
            
            self.stdout.write(
                self.style.SUCCESS(f'\nAnalysis results saved to: {output_file}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nFailed to save JSON results: {str(e)}')
            )


