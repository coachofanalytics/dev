"""
Simple AI Service for Performance Predictions

This service provides basic AI-powered predictions without complex ML dependencies.
It focuses on practical predictions using our existing data patterns.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, F

from management.models import TaskHistory
from accounts.models import CustomerUser


class SimpleAIService:
    """Simple AI service for performance predictions and optimization."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def predict_employee_performance(self, employee_id: int, task_category_id: int = None) -> Dict[str, Any]:
        """Predict performance for a specific employee."""
        try:
            self.logger.info(f"Predicting performance for employee {employee_id}")
            
            # Get employee
            try:
                employee = CustomerUser.objects.get(id=employee_id)
            except CustomerUser.DoesNotExist:
                return {
                    'success': False,
                    'message': f'Employee {employee_id} not found',
                    'confidence': 0.0
                }
            
            # Get historical data
            historical_data = self._get_employee_historical_data(employee_id, task_category_id)
            
            if len(historical_data) < 2:
                return {
                    'success': False,
                    'message': 'Insufficient historical data for prediction',
                    'confidence': 0.0,
                    'recommendation': 'Need at least 2 completed tasks for prediction'
                }
            
            # Calculate prediction
            prediction_result = self._calculate_performance_prediction(historical_data, employee)
            
            return {
                'success': True,
                'employee_id': employee_id,
                'employee_name': f"{employee.first_name} {employee.last_name}",
                'predicted_completion_rate': prediction_result['predicted_rate'],
                'confidence': prediction_result['confidence'],
                'historical_average': prediction_result['historical_average'],
                'task_count': len(historical_data),
                'trend': prediction_result['trend'],
                'insights': prediction_result['insights'],
                'recommendations': prediction_result['recommendations']
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting employee performance: {e}")
            return {
                'success': False,
                'message': f'Prediction failed: {str(e)}',
                'confidence': 0.0
            }
    
    def predict_optimal_task_assignment(self, task_category_id: int, available_employees: List[int] = None) -> Dict[str, Any]:
        """Predict optimal employee assignment for a task category."""
        try:
            self.logger.info(f"Predicting optimal assignment for task category {task_category_id}")
            
            # Get available employees
            if available_employees is None:
                available_employees = list(CustomerUser.objects.filter(is_active=True).values_list('id', flat=True))
            
            if not available_employees:
                return {
                    'success': False,
                    'message': 'No available employees for assignment',
                    'recommendations': []
                }
            
            # Predict performance for each employee
            predictions = []
            for employee_id in available_employees:
                try:
                    prediction_result = self.predict_employee_performance(employee_id, task_category_id)
                    
                    if prediction_result['success']:
                        predictions.append({
                            'employee_id': employee_id,
                            'employee_name': prediction_result['employee_name'],
                            'predicted_completion_rate': prediction_result['predicted_completion_rate'],
                            'confidence': prediction_result['confidence'],
                            'historical_performance': prediction_result['historical_average'],
                            'task_experience': prediction_result['task_count'],
                            'trend': prediction_result['trend']
                        })
                except Exception as e:
                    self.logger.warning(f"Failed to predict for employee {employee_id}: {e}")
                    continue
            
            if not predictions:
                return {
                    'success': False,
                    'message': 'No valid predictions generated',
                    'recommendations': []
                }
            
            # Sort by predicted performance
            predictions.sort(key=lambda x: x['predicted_completion_rate'], reverse=True)
            
            # Generate recommendations
            recommendations = self._generate_assignment_recommendations(predictions)
            
            return {
                'success': True,
                'task_category_id': task_category_id,
                'total_candidates': len(available_employees),
                'valid_predictions': len(predictions),
                'top_performers': predictions[:5],
                'recommendations': recommendations,
                'assignment_strategy': self._get_assignment_strategy(predictions)
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting optimal task assignment: {e}")
            return {
                'success': False,
                'message': f'Assignment prediction failed: {str(e)}',
                'recommendations': []
            }
    
    def predict_department_performance(self, department_name: str, time_horizon_days: int = 30) -> Dict[str, Any]:
        """Predict department performance."""
        try:
            self.logger.info(f"Predicting department performance for {department_name}")
            
            # Get department employees
            department_employees = self._get_department_employees(department_name)
            
            if not department_employees:
                return {
                    'success': False,
                    'message': f'No employees found in department {department_name}',
                    'predictions': []
                }
            
            # Predict performance for each employee
            employee_predictions = []
            for employee in department_employees:
                prediction = self.predict_employee_performance(employee.id)
                if prediction['success']:
                    employee_predictions.append({
                        'employee_id': employee.id,
                        'employee_name': prediction['employee_name'],
                        'predicted_completion_rate': prediction['predicted_completion_rate'],
                        'confidence': prediction['confidence'],
                        'trend': prediction['trend']
                    })
            
            if not employee_predictions:
                return {
                    'success': False,
                    'message': 'No valid employee predictions for department',
                    'predictions': []
                }
            
            # Calculate department-level metrics
            avg_predicted_rate = sum(p['predicted_completion_rate'] for p in employee_predictions) / len(employee_predictions)
            avg_confidence = sum(p['confidence'] for p in employee_predictions) / len(employee_predictions)
            
            # Generate insights
            insights = self._generate_department_insights(department_name, employee_predictions)
            
            return {
                'success': True,
                'department_name': department_name,
                'time_horizon_days': time_horizon_days,
                'total_employees': len(department_employees),
                'predicted_employees': len(employee_predictions),
                'predicted_completion_rate': avg_predicted_rate,
                'prediction_confidence': avg_confidence,
                'employee_predictions': employee_predictions,
                'insights': insights,
                'recommendations': self._generate_department_recommendations(department_name, avg_predicted_rate, insights)
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting department performance: {e}")
            return {
                'success': False,
                'message': f'Department prediction failed: {str(e)}',
                'predictions': []
            }
    
    def _get_employee_historical_data(self, employee_id: int, task_category_id: int = None) -> List[Dict[str, Any]]:
        """Get historical performance data for an employee."""
        queryset = TaskHistory.objects.filter(employee_id=employee_id)
        
        if task_category_id:
            queryset = queryset.filter(category_id=task_category_id)
        
        # Get recent data (last 2 years)
        cutoff_date = timezone.now().date() - timedelta(days=730)
        queryset = queryset.filter(daf_date__gte=cutoff_date)
        
        historical_data = []
        for task in queryset:
            if task.mxpoint and task.mxpoint > 0:
                historical_data.append({
                    'completion_rate': float(task.point) / float(task.mxpoint),
                    'category_id': task.category.id if task.category else None,
                    'earnings': float(task.mxearning),
                    'date': task.daf_date,
                    'days_since': (timezone.now().date() - task.daf_date).days if task.daf_date else 0
                })
        
        return historical_data
    
    def _calculate_performance_prediction(self, historical_data: List[Dict[str, Any]], employee: CustomerUser) -> Dict[str, Any]:
        """Calculate performance prediction based on historical data."""
        completion_rates = [d['completion_rate'] for d in historical_data]
        historical_average = sum(completion_rates) / len(completion_rates)
        
        # Calculate trend (recent vs older performance)
        if len(completion_rates) >= 4:
            recent_data = completion_rates[-2:]  # Last 2 tasks
            older_data = completion_rates[:-2]   # Earlier tasks
            recent_avg = sum(recent_data) / len(recent_data)
            older_avg = sum(older_data) / len(older_data)
            trend = recent_avg - older_avg
        else:
            trend = 0.0
        
        # Predict future performance with trend adjustment
        predicted_rate = historical_average + (trend * 0.3)  # 30% trend influence
        predicted_rate = max(0.0, min(1.0, predicted_rate))  # Clamp between 0 and 1
        
        # Calculate confidence based on data quality
        confidence = min(0.95, 0.3 + (len(historical_data) * 0.1))
        
        # Generate insights
        insights = []
        if predicted_rate > 0.8:
            insights.append(f"{employee.first_name} is predicted to be a high performer")
        elif predicted_rate < 0.5:
            insights.append(f"{employee.first_name} may need additional support")
        
        if trend > 0.1:
            insights.append("Performance is improving over time")
        elif trend < -0.1:
            insights.append("Performance is declining over time")
        
        if len(historical_data) > 10:
            insights.append("Employee has extensive task history")
        elif len(historical_data) < 5:
            insights.append("Limited task history - predictions less reliable")
        
        # Generate recommendations
        recommendations = []
        if predicted_rate > 0.8:
            recommendations.append("Consider for challenging tasks")
            recommendations.append("Mentor other team members")
        elif predicted_rate < 0.5:
            recommendations.append("Provide additional training")
            recommendations.append("Assign simpler tasks initially")
        
        if trend < -0.1:
            recommendations.append("Investigate performance decline")
        
        if len(historical_data) < 5:
            recommendations.append("Gather more performance data")
        
        return {
            'predicted_rate': predicted_rate,
            'confidence': confidence,
            'historical_average': historical_average,
            'trend': trend,
            'insights': insights,
            'recommendations': recommendations
        }
    
    def _generate_assignment_recommendations(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate task assignment recommendations."""
        recommendations = []
        
        if predictions:
            # Primary recommendation
            top_performer = predictions[0]
            recommendations.append({
                'type': 'primary_assign',
                'employee_id': top_performer['employee_id'],
                'employee_name': top_performer['employee_name'],
                'reason': f"Highest predicted completion rate ({top_performer['predicted_completion_rate']:.1%})",
                'confidence': top_performer['confidence']
            })
            
            # Backup recommendation
            if len(predictions) > 1:
                backup = predictions[1]
                recommendations.append({
                    'type': 'backup_assign',
                    'employee_id': backup['employee_id'],
                    'employee_name': backup['employee_name'],
                    'reason': f"Strong alternative with {backup['predicted_completion_rate']:.1%} predicted rate",
                    'confidence': backup['confidence']
                })
            
            # Team recommendation
            if len(predictions) >= 3:
                team_members = predictions[:3]
                recommendations.append({
                    'type': 'team_assign',
                    'reason': f"Team assignment with top 3 performers (avg: {sum(p['predicted_completion_rate'] for p in team_members)/3:.1%})",
                    'team_members': [{'name': p['employee_name'], 'rate': p['predicted_completion_rate']} for p in team_members]
                })
        
        return recommendations
    
    def _get_assignment_strategy(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get assignment strategy based on predictions."""
        if not predictions:
            return {'strategy': 'no_data', 'confidence': 0.0}
        
        avg_prediction = sum(p['predicted_completion_rate'] for p in predictions) / len(predictions)
        avg_confidence = sum(p['confidence'] for p in predictions) / len(predictions)
        
        if avg_prediction > 0.7:
            strategy = 'high_confidence'
        elif avg_prediction > 0.5:
            strategy = 'moderate_confidence'
        else:
            strategy = 'low_confidence'
        
        return {
            'strategy': strategy,
            'confidence': avg_confidence,
            'avg_predicted_rate': avg_prediction
        }
    
    def _get_department_employees(self, department_name: str) -> List[CustomerUser]:
        """Get employees in a department (using category mapping)."""
        category_mapping = {
            'IT': 1,
            'HR': 2,
            'Finance': 3,
            'Marketing': 4,
            'Operations': 5,
            'Other': 999
        }
        
        category = category_mapping.get(department_name)
        if category is not None:
            return list(CustomerUser.objects.filter(category=category))
        
        return []
    
    def _generate_department_insights(self, department_name: str, employee_predictions: List[Dict[str, Any]]) -> List[str]:
        """Generate department-level insights."""
        insights = []
        
        if employee_predictions:
            avg_prediction = sum(p['predicted_completion_rate'] for p in employee_predictions) / len(employee_predictions)
            insights.append(f"Department {department_name} predicted average completion rate: {avg_prediction:.1%}")
            
            high_performers = [p for p in employee_predictions if p['predicted_completion_rate'] > 0.8]
            if high_performers:
                insights.append(f"{len(high_performers)} high performers identified in department")
            
            improving_employees = [p for p in employee_predictions if p.get('trend', 0) > 0.1]
            if improving_employees:
                insights.append(f"{len(improving_employees)} employees showing improving performance")
        
        return insights
    
    def _generate_department_recommendations(self, department_name: str, predicted_rate: float, insights: List[str]) -> List[str]:
        """Generate department-level recommendations."""
        recommendations = []
        
        if predicted_rate > 0.7:
            recommendations.append(f"Department {department_name} is performing well")
            recommendations.append("Consider expanding team capacity")
        elif predicted_rate < 0.5:
            recommendations.append(f"Department {department_name} needs performance improvement")
            recommendations.append("Implement training programs")
        
        return recommendations


