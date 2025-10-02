"""
Data Validation and Monitoring Service

This service provides comprehensive data quality monitoring and validation
for the TaskHistory and related models.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, F
from django.core.exceptions import ValidationError

from management.models import TaskHistory
from accounts.models import CustomerUser


class DataValidationService:
    """Service for validating and monitoring data quality."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_task_history_data(self) -> Dict[str, Any]:
        """Comprehensive validation of TaskHistory data quality."""
        self.logger.info("Starting TaskHistory data validation")
        
        validation_results = {
            'timestamp': timezone.now(),
            'overall_score': 0,
            'issues': [],
            'warnings': [],
            'recommendations': [],
            'metrics': {}
        }
        
        try:
            # 1. Check for NULL dates
            null_dates = self._check_null_dates()
            validation_results['issues'].extend(null_dates['issues'])
            validation_results['warnings'].extend(null_dates['warnings'])
            
            # 2. Check for invalid completion rates
            invalid_rates = self._check_completion_rates()
            validation_results['issues'].extend(invalid_rates['issues'])
            validation_results['warnings'].extend(invalid_rates['warnings'])
            
            # 3. Check for missing relationships
            missing_relations = self._check_missing_relationships()
            validation_results['issues'].extend(missing_relations['issues'])
            validation_results['warnings'].extend(missing_relations['warnings'])
            
            # 4. Check for data consistency
            consistency_issues = self._check_data_consistency()
            validation_results['issues'].extend(consistency_issues['issues'])
            validation_results['warnings'].extend(consistency_issues['warnings'])
            
            # 5. Calculate overall quality score
            validation_results['overall_score'] = self._calculate_quality_score(validation_results)
            
            # 6. Generate recommendations
            validation_results['recommendations'] = self._generate_validation_recommendations(validation_results)
            
            # 7. Generate metrics
            validation_results['metrics'] = self._generate_validation_metrics()
            
            self.logger.info(f"Data validation completed. Overall score: {validation_results['overall_score']}")
            
        except Exception as e:
            self.logger.error(f"Error during data validation: {e}")
            validation_results['issues'].append({
                'type': 'validation_error',
                'severity': 'critical',
                'message': f'Validation process failed: {str(e)}',
                'affected_records': 0
            })
        
        return validation_results
    
    def _check_null_dates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Check for NULL or invalid dates in TaskHistory."""
        issues = []
        warnings = []
        
        # Check for NULL dates
        null_date_count = TaskHistory.objects.filter(daf_date__isnull=True).count()
        if null_date_count > 0:
            issues.append({
                'type': 'null_dates',
                'severity': 'critical',
                'message': f'{null_date_count} records have NULL dates',
                'affected_records': null_date_count,
                'fix_suggestion': 'Run fix_taskhistory_dates management command'
            })
        
        # Check for future dates
        future_date_count = TaskHistory.objects.filter(daf_date__gt=timezone.now().date()).count()
        if future_date_count > 0:
            warnings.append({
                'type': 'future_dates',
                'severity': 'medium',
                'message': f'{future_date_count} records have future dates',
                'affected_records': future_date_count,
                'fix_suggestion': 'Review and correct future dates'
            })
        
        # Check for very old dates (more than 10 years)
        old_cutoff = timezone.now().date() - timedelta(days=3650)
        old_date_count = TaskHistory.objects.filter(daf_date__lt=old_cutoff).count()
        if old_date_count > 0:
            warnings.append({
                'type': 'very_old_dates',
                'severity': 'low',
                'message': f'{old_date_count} records have dates older than 10 years',
                'affected_records': old_date_count,
                'fix_suggestion': 'Review historical data accuracy'
            })
        
        return {'issues': issues, 'warnings': warnings}
    
    def _check_completion_rates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Check for invalid completion rates in TaskHistory."""
        issues = []
        warnings = []
        
        # Check for completion rates > 100%
        over_completion = TaskHistory.objects.filter(
            Q(point__gt=F('mxpoint')) & Q(mxpoint__gt=0)
        ).count()
        
        if over_completion > 0:
            issues.append({
                'type': 'over_completion',
                'severity': 'high',
                'message': f'{over_completion} records have completion rates > 100%',
                'affected_records': over_completion,
                'fix_suggestion': 'Review point and mxpoint values'
            })
        
        # Check for negative completion rates
        negative_completion = TaskHistory.objects.filter(
            Q(point__lt=0) | Q(mxpoint__lt=0)
        ).count()
        
        if negative_completion > 0:
            issues.append({
                'type': 'negative_completion',
                'severity': 'critical',
                'message': f'{negative_completion} records have negative completion values',
                'affected_records': negative_completion,
                'fix_suggestion': 'Fix negative point or mxpoint values'
            })
        
        # Check for zero max points
        zero_max_points = TaskHistory.objects.filter(mxpoint=0).count()
        if zero_max_points > 0:
            warnings.append({
                'type': 'zero_max_points',
                'severity': 'medium',
                'message': f'{zero_max_points} records have zero max points',
                'affected_records': zero_max_points,
                'fix_suggestion': 'Set appropriate max points for tasks'
            })
        
        return {'issues': issues, 'warnings': warnings}
    
    def _check_missing_relationships(self) -> Dict[str, List[Dict[str, Any]]]:
        """Check for missing or invalid relationships."""
        issues = []
        warnings = []
        
        # Check for missing employees
        missing_employees = TaskHistory.objects.filter(employee__isnull=True).count()
        if missing_employees > 0:
            issues.append({
                'type': 'missing_employees',
                'severity': 'critical',
                'message': f'{missing_employees} records have no assigned employee',
                'affected_records': missing_employees,
                'fix_suggestion': 'Assign employees to all tasks'
            })
        
        # Check for missing categories
        missing_categories = TaskHistory.objects.filter(category__isnull=True).count()
        if missing_categories > 0:
            warnings.append({
                'type': 'missing_categories',
                'severity': 'medium',
                'message': f'{missing_categories} records have no category',
                'affected_records': missing_categories,
                'fix_suggestion': 'Assign categories to all tasks'
            })
        
        # Check for invalid employee references
        invalid_employees = TaskHistory.objects.filter(
            employee__isnull=False
        ).exclude(
            employee__in=CustomerUser.objects.all()
        ).count()
        
        if invalid_employees > 0:
            issues.append({
                'type': 'invalid_employees',
                'severity': 'high',
                'message': f'{invalid_employees} records reference non-existent employees',
                'affected_records': invalid_employees,
                'fix_suggestion': 'Fix employee references'
            })
        
        return {'issues': issues, 'warnings': warnings}
    
    def _check_data_consistency(self) -> Dict[str, List[Dict[str, Any]]]:
        """Check for data consistency issues."""
        issues = []
        warnings = []
        
        # Check for duplicate records (same employee, category, date, points)
        duplicates = TaskHistory.objects.values(
            'employee', 'category', 'daf_date', 'point', 'mxpoint'
        ).annotate(count=Count('id')).filter(count__gt=1)
        
        if duplicates.exists():
            duplicate_count = sum(d['count'] - 1 for d in duplicates)
            warnings.append({
                'type': 'potential_duplicates',
                'severity': 'medium',
                'message': f'{duplicate_count} potential duplicate records found',
                'affected_records': duplicate_count,
                'fix_suggestion': 'Review and merge duplicate records'
            })
        
        # Check for earnings consistency
        inconsistent_earnings = TaskHistory.objects.filter(
            Q(mxearning__isnull=True) | Q(mxearning__lt=0)
        ).count()
        
        if inconsistent_earnings > 0:
            warnings.append({
                'type': 'inconsistent_earnings',
                'severity': 'medium',
                'message': f'{inconsistent_earnings} records have inconsistent earnings',
                'affected_records': inconsistent_earnings,
                'fix_suggestion': 'Set appropriate earnings for all tasks'
            })
        
        return {'issues': issues, 'warnings': warnings}
    
    def _calculate_quality_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall data quality score (0-100)."""
        total_records = TaskHistory.objects.count()
        if total_records == 0:
            return 100.0
        
        # Start with perfect score
        score = 100.0
        
        # Deduct points for issues
        for issue in validation_results['issues']:
            severity_penalty = {
                'critical': 20.0,
                'high': 10.0,
                'medium': 5.0,
                'low': 2.0
            }
            penalty = severity_penalty.get(issue['severity'], 5.0)
            affected_ratio = issue['affected_records'] / total_records
            score -= penalty * affected_ratio
        
        # Deduct points for warnings
        for warning in validation_results['warnings']:
            severity_penalty = {
                'critical': 10.0,
                'high': 5.0,
                'medium': 2.0,
                'low': 1.0
            }
            penalty = severity_penalty.get(warning['severity'], 2.0)
            affected_ratio = warning['affected_records'] / total_records
            score -= penalty * affected_ratio
        
        return max(0.0, min(100.0, score))
    
    def _generate_validation_recommendations(self, validation_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []
        
        # High priority recommendations
        critical_issues = [i for i in validation_results['issues'] if i['severity'] == 'critical']
        if critical_issues:
            recommendations.append({
                'priority': 'high',
                'title': 'Address Critical Data Issues',
                'description': f'Fix {len(critical_issues)} critical data quality issues immediately',
                'action': 'Run data fix commands and review data entry processes'
            })
        
        # Medium priority recommendations
        high_issues = [i for i in validation_results['issues'] if i['severity'] == 'high']
        if high_issues:
            recommendations.append({
                'priority': 'medium',
                'title': 'Fix High Priority Issues',
                'description': f'Address {len(high_issues)} high priority data issues',
                'action': 'Review and correct data inconsistencies'
            })
        
        # Data monitoring recommendation
        if validation_results['overall_score'] < 90:
            recommendations.append({
                'priority': 'medium',
                'title': 'Implement Data Quality Monitoring',
                'description': 'Set up automated data quality monitoring',
                'action': 'Schedule regular data validation runs'
            })
        
        return recommendations
    
    def _generate_validation_metrics(self) -> Dict[str, Any]:
        """Generate data quality metrics."""
        total_records = TaskHistory.objects.count()
        
        if total_records == 0:
            return {'total_records': 0}
        
        # Basic metrics
        metrics = {
            'total_records': total_records,
            'records_with_dates': TaskHistory.objects.filter(daf_date__isnull=False).count(),
            'records_with_employees': TaskHistory.objects.filter(employee__isnull=False).count(),
            'records_with_categories': TaskHistory.objects.filter(category__isnull=False).count(),
            'date_coverage_percentage': (TaskHistory.objects.filter(daf_date__isnull=False).count() / total_records) * 100,
            'employee_coverage_percentage': (TaskHistory.objects.filter(employee__isnull=False).count() / total_records) * 100,
            'category_coverage_percentage': (TaskHistory.objects.filter(category__isnull=False).count() / total_records) * 100
        }
        
        # Completion rate metrics
        valid_completion_records = TaskHistory.objects.filter(
            mxpoint__gt=0,
            point__gte=0
        )
        
        if valid_completion_records.exists():
            avg_completion = valid_completion_records.aggregate(
                avg=Avg(F('point') / F('mxpoint'))
            )['avg'] or 0
            
            metrics.update({
                'average_completion_rate': float(avg_completion) * 100,
                'valid_completion_records': valid_completion_records.count()
            })
        
        return metrics
    
    def get_data_quality_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive data quality dashboard data."""
        validation_results = self.validate_task_history_data()
        
        dashboard_data = {
            'overall_score': validation_results['overall_score'],
            'timestamp': validation_results['timestamp'],
            'summary': {
                'total_issues': len(validation_results['issues']),
                'total_warnings': len(validation_results['warnings']),
                'critical_issues': len([i for i in validation_results['issues'] if i['severity'] == 'critical']),
                'high_issues': len([i for i in validation_results['issues'] if i['severity'] == 'high'])
            },
            'metrics': validation_results['metrics'],
            'recent_issues': validation_results['issues'][:5],  # Top 5 issues
            'recent_warnings': validation_results['warnings'][:5],  # Top 5 warnings
            'recommendations': validation_results['recommendations']
        }
        
        return dashboard_data
