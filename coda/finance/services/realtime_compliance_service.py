"""
Real-time Compliance Service for CODA Finance System

Provides real-time compliance monitoring, automatic notifications, and live updates
for the 33% compliance rule and salary inclusion in budget approvals.

Features:
- Real-time compliance threshold monitoring
- Automatic email notifications when employees reach 33%
- WebSocket updates for live dashboard refreshes
- Compliance status change tracking
- Integration with salary and budget systems

Created: October 2025
Phase: Advanced Real-time Features
"""

import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Q, Sum
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from management.models import TaskHistory, Task
from management.utils import calculate_total_pay
from management.services.employee_compliance_service import EmployeeComplianceService
from finance.services.integrated_budget_service import IntegratedBudgetService

User = get_user_model()
logger = logging.getLogger(__name__)


class RealtimeComplianceService:
    """
    Service for real-time compliance monitoring and notifications.
    
    Monitors employee task completion and automatically sends notifications
    when compliance thresholds are reached or missed.
    """
    
    def __init__(self):
        self.compliance_service = EmployeeComplianceService()
        self.integrated_service = IntegratedBudgetService()
        self.logger = logging.getLogger(__name__)
    
    def monitor_compliance_changes(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Monitor all employees for compliance status changes.
        
        Returns employees who have newly reached compliance threshold or
        dropped below it since last check.
        """
        try:
            self.logger.info(f"Monitoring compliance changes for {target_month}/{target_year}")
            
            # Get current compliance status for all employees
            current_compliance = self._get_all_employee_compliance(target_month, target_year)
            
            # Get previous compliance status (from cache or last check)
            previous_compliance = self._get_previous_compliance_status(target_month, target_year)
            
            # Compare and identify changes
            compliance_changes = self._identify_compliance_changes(
                current_compliance, previous_compliance
            )
            
            # Send notifications for changes
            notification_results = self._process_compliance_notifications(compliance_changes)
            
            # Update cached compliance status
            self._update_cached_compliance_status(target_month, target_year, current_compliance)
            
            return {
                'monitored_employees': len(current_compliance),
                'compliance_changes': compliance_changes,
                'notifications_sent': notification_results,
                'monitoring_timestamp': timezone.now(),
                'period': f"{target_month}/{target_year}"
            }
            
        except Exception as e:
            self.logger.error(f"Error monitoring compliance changes: {e}")
            return {'error': str(e)}
    
    def check_employee_compliance_threshold(self, employee: User, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Check if a specific employee has reached the 33% compliance threshold.
        
        Returns detailed compliance information and triggers notifications if needed.
        """
        try:
            # Get employee's TaskHistory records
            task_history_records = TaskHistory.objects.filter(
                employee=employee,
                daf_date__month=target_month,
                daf_date__year=target_year
            )
            
            if not task_history_records.exists():
                return {
                    'employee': employee,
                    'compliance_rate': 0.0,
                    'is_compliant': False,
                    'threshold_reached': False,
                    'message': 'No task history found for this period'
                }
            
            # Calculate compliance
            total_points = sum(task.point for task in task_history_records)
            total_max_points = sum(task.mxpoint for task in task_history_records)
            
            if total_max_points == 0:
                return {
                    'employee': employee,
                    'compliance_rate': 0.0,
                    'is_compliant': False,
                    'threshold_reached': False,
                    'message': 'No maximum points assigned'
                }
            
            compliance_rate = (total_points / total_max_points) * 100
            is_compliant = compliance_rate >= 33.0
            
            # Check if this is a new compliance achievement
            previous_status = self._get_employee_previous_compliance_status(employee, target_month, target_year)
            threshold_reached = is_compliant and not previous_status.get('was_compliant', False)
            
            # Calculate salary if compliant
            salary_amount = calculate_total_pay(task_history_records) if is_compliant else Decimal('0.00')
            
            result = {
                'employee': employee,
                'employee_id': employee.id,
                'username': employee.username,
                'full_name': employee.get_full_name(),
                'total_points': total_points,
                'total_max_points': total_max_points,
                'compliance_rate': round(compliance_rate, 2),
                'is_compliant': is_compliant,
                'threshold_reached': threshold_reached,
                'salary_amount': salary_amount,
                'task_count': task_history_records.count(),
                'checked_at': timezone.now()
            }
            
            # Send notification if threshold was just reached
            if threshold_reached:
                notification_result = self._send_compliance_achievement_notification(employee, result)
                result['notification_sent'] = notification_result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error checking employee compliance threshold: {e}")
            return {'error': str(e)}
    
    def send_compliance_reminder_notifications(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Send reminder notifications to non-compliant employees.
        
        This can be called periodically (e.g., daily) to remind employees
        to complete their tasks to reach the 33% threshold.
        """
        try:
            self.logger.info(f"Sending compliance reminder notifications for {target_month}/{target_year}")
            
            # Get all non-compliant employees
            non_compliant_employees = self._get_non_compliant_employees(target_month, target_year)
            
            notifications_sent = []
            for employee_data in non_compliant_employees:
                try:
                    notification_result = self._send_compliance_reminder_notification(
                        employee_data['employee'], employee_data
                    )
                    notifications_sent.append({
                        'employee': employee_data['employee'].username,
                        'notification_sent': notification_result['success'],
                        'sent_at': timezone.now()
                    })
                except Exception as e:
                    self.logger.error(f"Error sending reminder to {employee_data['employee'].username}: {e}")
                    notifications_sent.append({
                        'employee': employee_data['employee'].username,
                        'notification_sent': False,
                        'error': str(e)
                    })
            
            return {
                'notifications_attempted': len(non_compliant_employees),
                'notifications_sent': len([n for n in notifications_sent if n['notification_sent']]),
                'notifications_failed': len([n for n in notifications_sent if not n['notification_sent']]),
                'notification_details': notifications_sent,
                'sent_at': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error sending compliance reminder notifications: {e}")
            return {'error': str(e)}
    
    def get_realtime_dashboard_data(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Get real-time data for dashboard updates.
        
        This method provides the latest compliance and salary data
        that can be used for live dashboard refreshes via AJAX or WebSocket.
        """
        try:
            # Get current compliance summary
            compliance_summary = self.compliance_service.get_compliance_summary()
            
            # Get salary data
            salary_data = self.integrated_service.get_salary_dashboard_data(target_month, target_year)
            
            # Get budget summary
            budget_summary = self.integrated_service.get_monthly_budget_summary(target_month, target_year)
            
            # Get recent compliance changes (last 24 hours)
            recent_changes = self._get_recent_compliance_changes(target_month, target_year)
            
            return {
                'timestamp': timezone.now(),
                'period': f"{target_month}/{target_year}",
                'compliance_summary': compliance_summary,
                'salary_data': salary_data,
                'budget_summary': budget_summary,
                'recent_changes': recent_changes,
                'is_rule_active': compliance_summary.get('is_rule_active', False)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting realtime dashboard data: {e}")
            return {'error': str(e)}
    
    def _get_all_employee_compliance(self, target_month: int, target_year: int) -> List[Dict[str, Any]]:
        """Get compliance status for all active employees."""
        employees = User.objects.filter(is_active=True, is_staff=True)
        compliance_data = []
        
        for employee in employees:
            compliance_info = self.check_employee_compliance_threshold(employee, target_month, target_year)
            if 'error' not in compliance_info:
                compliance_data.append(compliance_info)
        
        return compliance_data
    
    def _get_previous_compliance_status(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """Get cached previous compliance status."""
        # In a real implementation, this would read from Redis or database cache
        # For now, return empty dict (first run)
        return {}
    
    def _identify_compliance_changes(self, current: List[Dict], previous: Dict[str, Any]) -> Dict[str, Any]:
        """Identify employees whose compliance status has changed."""
        changes = {
            'newly_compliant': [],
            'newly_non_compliant': [],
            'compliance_improved': [],
            'compliance_declined': []
        }
        
        for employee_data in current:
            employee_id = employee_data['employee_id']
            current_compliant = employee_data['is_compliant']
            current_rate = employee_data['compliance_rate']
            
            # Check if status changed
            was_compliant = previous.get(str(employee_id), {}).get('was_compliant', False)
            previous_rate = previous.get(str(employee_id), {}).get('compliance_rate', 0)
            
            if current_compliant and not was_compliant:
                changes['newly_compliant'].append(employee_data)
            elif not current_compliant and was_compliant:
                changes['newly_non_compliant'].append(employee_data)
            elif current_rate > previous_rate:
                changes['compliance_improved'].append(employee_data)
            elif current_rate < previous_rate:
                changes['compliance_declined'].append(employee_data)
        
        return changes
    
    def _process_compliance_notifications(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Process and send notifications for compliance changes."""
        notification_results = {
            'achievement_notifications': 0,
            'decline_notifications': 0,
            'improvement_notifications': 0
        }
        
        # Send notifications for newly compliant employees
        for employee_data in changes['newly_compliant']:
            try:
                result = self._send_compliance_achievement_notification(
                    employee_data['employee'], employee_data
                )
                if result['success']:
                    notification_results['achievement_notifications'] += 1
            except Exception as e:
                self.logger.error(f"Error sending achievement notification: {e}")
        
        # Send notifications for compliance declines
        for employee_data in changes['newly_non_compliant']:
            try:
                result = self._send_compliance_decline_notification(
                    employee_data['employee'], employee_data
                )
                if result['success']:
                    notification_results['decline_notifications'] += 1
            except Exception as e:
                self.logger.error(f"Error sending decline notification: {e}")
        
        return notification_results
    
    def _send_compliance_achievement_notification(self, employee: User, compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification when employee reaches compliance threshold."""
        try:
            subject = f"🎉 Congratulations! You've reached the 33% compliance threshold"
            
            context = {
                'employee': employee,
                'compliance_data': compliance_data,
                'salary_amount': compliance_data.get('salary_amount', 0),
                'compliance_rate': compliance_data.get('compliance_rate', 0),
                'current_date': timezone.now().date()
            }
            
            message = render_to_string('finance/email/compliance_achievement.html', context)
            
            send_mail(
                subject=subject,
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[employee.email],
                html_message=message,
                fail_silently=False
            )
            
            self.logger.info(f"Compliance achievement notification sent to {employee.username}")
            return {'success': True, 'sent_at': timezone.now()}
            
        except Exception as e:
            self.logger.error(f"Error sending compliance achievement notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_compliance_reminder_notification(self, employee: User, compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send reminder notification to non-compliant employee."""
        try:
            subject = f"📋 Reminder: Complete your tasks to reach 33% compliance"
            
            context = {
                'employee': employee,
                'compliance_data': compliance_data,
                'compliance_rate': compliance_data.get('compliance_rate', 0),
                'current_date': timezone.now().date()
            }
            
            message = render_to_string('finance/email/compliance_reminder.html', context)
            
            send_mail(
                subject=subject,
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[employee.email],
                html_message=message,
                fail_silently=False
            )
            
            self.logger.info(f"Compliance reminder notification sent to {employee.username}")
            return {'success': True, 'sent_at': timezone.now()}
            
        except Exception as e:
            self.logger.error(f"Error sending compliance reminder notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_compliance_decline_notification(self, employee: User, compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification when employee drops below compliance threshold."""
        try:
            subject = f"⚠️ Important: Your compliance has dropped below 33%"
            
            context = {
                'employee': employee,
                'compliance_data': compliance_data,
                'compliance_rate': compliance_data.get('compliance_rate', 0),
                'current_date': timezone.now().date()
            }
            
            message = render_to_string('finance/email/compliance_decline.html', context)
            
            send_mail(
                subject=subject,
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[employee.email],
                html_message=message,
                fail_silently=False
            )
            
            self.logger.info(f"Compliance decline notification sent to {employee.username}")
            return {'success': True, 'sent_at': timezone.now()}
            
        except Exception as e:
            self.logger.error(f"Error sending compliance decline notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_non_compliant_employees(self, target_month: int, target_year: int) -> List[Dict[str, Any]]:
        """Get all non-compliant employees for reminder notifications."""
        all_compliance = self._get_all_employee_compliance(target_month, target_year)
        return [emp for emp in all_compliance if not emp['is_compliant']]
    
    def _update_cached_compliance_status(self, target_month: int, target_year: int, compliance_data: List[Dict[str, Any]]) -> None:
        """Update cached compliance status for future comparisons."""
        # In a real implementation, this would update Redis or database cache
        # For now, we'll just log the update
        self.logger.info(f"Updated cached compliance status for {target_month}/{target_year}")
    
    def _get_employee_previous_compliance_status(self, employee: User, target_month: int, target_year: int) -> Dict[str, Any]:
        """Get previous compliance status for a specific employee."""
        # In a real implementation, this would read from cache
        # For now, return default values
        return {'was_compliant': False, 'compliance_rate': 0}
    
    def _get_recent_compliance_changes(self, target_month: int, target_year: int) -> List[Dict[str, Any]]:
        """Get compliance changes from the last 24 hours."""
        # In a real implementation, this would query a compliance change log
        # For now, return empty list
        return []
