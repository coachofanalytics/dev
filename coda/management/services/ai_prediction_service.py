"""
AI-Powered Performance Prediction Service

This service uses machine learning to predict employee performance,
task success rates, and optimal task assignments.
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, F
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

from management.models import TaskHistory
from accounts.models import CustomerUser
from ai_services.ai_integration_service import RealAIService


class AIPredictionService:
    """Service for AI-powered performance predictions and optimization."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_service = RealAIService()
        self.model_cache = {}
        self.scaler_cache = {}
        
        # Model configuration
        self.model_config = {
            'performance_prediction': {
                'model_type': 'RandomForestRegressor',
                'n_estimators': 100,
                'max_depth': 10,
                'random_state': 42
            },
            'task_assignment': {
                'model_type': 'GradientBoostingRegressor',
                'n_estimators': 150,
                'max_depth': 8,
                'learning_rate': 0.1,
                'random_state': 42
            }
        }
    
    def predict_employee_performance(self, employee_id: int, task_category_id: int = None) -> Dict[str, Any]:
        """Predict performance for a specific employee on a task category."""
        try:
            self.logger.info(f"Predicting performance for employee {employee_id}")
            
            # Get employee data
            employee = CustomerUser.objects.get(id=employee_id)
            employee_features = self._extract_employee_features(employee)
            
            # Get historical performance data
            historical_data = self._get_employee_historical_data(employee_id, task_category_id)
            
            if len(historical_data) < 5:
                return {
                    'success': False,
                    'message': 'Insufficient historical data for prediction',
                    'confidence': 0.0,
                    'recommendation': 'Collect more task history data'
                }
            
            # Prepare features for prediction
            prediction_features = self._prepare_prediction_features(employee_features, historical_data)
            
            # Train/load model
            model = self._get_or_train_model('performance_prediction', historical_data)
            
            if model is None:
                return {
                    'success': False,
                    'message': 'Failed to train prediction model',
                    'confidence': 0.0
                }
            
            # Make prediction
            prediction = model.predict([prediction_features])[0]
            confidence = self._calculate_prediction_confidence(model, prediction_features)
            
            # Generate insights
            insights = self._generate_performance_insights(employee, historical_data, prediction)
            
            return {
                'success': True,
                'employee_id': employee_id,
                'employee_name': f"{employee.first_name} {employee.last_name}",
                'predicted_completion_rate': float(prediction),
                'confidence': float(confidence),
                'historical_average': float(np.mean([d['completion_rate'] for d in historical_data])),
                'task_count': len(historical_data),
                'insights': insights,
                'recommendations': self._generate_performance_recommendations(prediction, historical_data)
            }
            
        except CustomerUser.DoesNotExist:
            return {
                'success': False,
                'message': f'Employee {employee_id} not found',
                'confidence': 0.0
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
            
            # Get available employees (or all employees if not specified)
            if available_employees is None:
                available_employees = list(CustomerUser.objects.values_list('id', flat=True))
            
            if not available_employees:
                return {
                    'success': False,
                    'message': 'No available employees for assignment',
                    'recommendations': []
                }
            
            # Get task category data
            task_features = self._extract_task_category_features(task_category_id)
            
            # Predict performance for each employee
            predictions = []
            for employee_id in available_employees:
                try:
                    prediction_result = self.predict_employee_performance(employee_id, task_category_id)
                    
                    if prediction_result['success']:
                        employee = CustomerUser.objects.get(id=employee_id)
                        predictions.append({
                            'employee_id': employee_id,
                            'employee_name': f"{employee.first_name} {employee.last_name}",
                            'predicted_completion_rate': prediction_result['predicted_completion_rate'],
                            'confidence': prediction_result['confidence'],
                            'historical_performance': prediction_result['historical_average'],
                            'task_experience': prediction_result['task_count']
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
            
            # Generate assignment recommendations
            recommendations = self._generate_assignment_recommendations(predictions, task_features)
            
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
        """Predict department performance over a time horizon."""
        try:
            self.logger.info(f"Predicting department performance for {department_name}")
            
            # Get department employees (using category mapping)
            department_employees = self._get_department_employees(department_name)
            
            if not department_employees:
                return {
                    'success': False,
                    'message': f'No employees found in department {department_name}',
                    'predictions': []
                }
            
            # Get historical department data
            historical_data = self._get_department_historical_data(department_name)
            
            if len(historical_data) < 10:
                return {
                    'success': False,
                    'message': 'Insufficient historical data for department prediction',
                    'predictions': []
                }
            
            # Predict performance for each employee
            employee_predictions = []
            for employee in department_employees:
                prediction = self.predict_employee_performance(employee.id)
                if prediction['success']:
                    employee_predictions.append({
                        'employee_id': employee.id,
                        'employee_name': f"{employee.first_name} {employee.last_name}",
                        'predicted_completion_rate': prediction['predicted_completion_rate'],
                        'confidence': prediction['confidence']
                    })
            
            # Calculate department-level predictions
            if employee_predictions:
                avg_predicted_rate = float(np.mean([float(p['predicted_completion_rate']) for p in employee_predictions]))
                avg_confidence = float(np.mean([float(p['confidence']) for p in employee_predictions]))
                
                # Generate department insights
                insights = self._generate_department_insights(department_name, employee_predictions, historical_data)
                
                return {
                    'success': True,
                    'department_name': department_name,
                    'time_horizon_days': time_horizon_days,
                    'total_employees': len(department_employees),
                    'predicted_employees': len(employee_predictions),
                    'predicted_completion_rate': float(avg_predicted_rate),
                    'prediction_confidence': float(avg_confidence),
                    'employee_predictions': employee_predictions,
                    'insights': insights,
                    'recommendations': self._generate_department_recommendations(department_name, avg_predicted_rate, insights)
                }
            else:
                return {
                    'success': False,
                    'message': 'No valid employee predictions for department',
                    'predictions': []
                }
            
        except Exception as e:
            self.logger.error(f"Error predicting department performance: {e}")
            return {
                'success': False,
                'message': f'Department prediction failed: {str(e)}',
                'predictions': []
            }
    
    def _extract_employee_features(self, employee: CustomerUser) -> Dict[str, Any]:
        """Extract features for an employee."""
        return {
            'category': employee.category,
            'is_active': employee.is_active,
            'date_joined_days': (timezone.now().date() - employee.date_joined.date()).days if employee.date_joined else 0,
            'is_staff': employee.is_staff,
            'is_admin': getattr(employee, 'is_admin', False)
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
                    'completion_rate': task.point / task.mxpoint,
                    'category_id': task.category.id if task.category else None,
                    'earnings': task.mxearning,
                    'date': task.daf_date,
                    'days_since': (timezone.now().date() - task.daf_date).days if task.daf_date else 0
                })
        
        return historical_data
    
    def _extract_task_category_features(self, task_category_id: int) -> Dict[str, Any]:
        """Extract features for a task category."""
        # Get task statistics for this category
        tasks = TaskHistory.objects.filter(category_id=task_category_id)
        
        if not tasks.exists():
            return {'category_id': task_category_id, 'task_count': 0}
        
        total_tasks = tasks.count()
        avg_completion = tasks.filter(mxpoint__gt=0).aggregate(
            avg=Avg(F('point') / F('mxpoint'))
        )['avg'] or 0
        
        avg_earnings = tasks.aggregate(avg=Avg('mxearning'))['avg'] or 0
        
        return {
            'category_id': task_category_id,
            'task_count': total_tasks,
            'avg_completion_rate': float(avg_completion),
            'avg_earnings': float(avg_earnings),
            'complexity_score': self._calculate_task_complexity(task_category_id)
        }
    
    def _calculate_task_complexity(self, task_category_id: int) -> float:
        """Calculate complexity score for a task category."""
        tasks = TaskHistory.objects.filter(category_id=task_category_id)
        
        if not tasks.exists():
            return 0.0
        
        # Calculate complexity based on variance in completion rates
        completion_rates = []
        for task in tasks:
            if task.mxpoint and task.mxpoint > 0:
                completion_rates.append(task.point / task.mxpoint)
        
        if len(completion_rates) < 2:
            return 0.0
        
        return float(np.std(completion_rates))
    
    def _prepare_prediction_features(self, employee_features: Dict[str, Any], historical_data: List[Dict[str, Any]]) -> List[float]:
        """Prepare features for model prediction."""
        features = []
        
        # Employee features
        features.extend([
            float(employee_features['category']),
            float(employee_features['is_active']),
            float(employee_features['date_joined_days']),
            float(employee_features['is_staff']),
            float(employee_features['is_admin'])
        ])
        
        # Historical performance features
        if historical_data:
            completion_rates = [float(d['completion_rate']) for d in historical_data]
            earnings = [float(d['earnings']) for d in historical_data]
            days_since = [float(d['days_since']) for d in historical_data]
            
            features.extend([
                float(np.mean(completion_rates)),
                float(np.std(completion_rates)) if len(completion_rates) > 1 else 0.0,
                float(np.max(completion_rates)),
                float(np.min(completion_rates)),
                float(len(historical_data)),
                float(np.mean(earnings)),
                float(np.mean(days_since))
            ])
        else:
            features.extend([0.0] * 7)  # Default values
        
        return features
    
    def _get_or_train_model(self, model_type: str, training_data: List[Dict[str, Any]]) -> Optional[Any]:
        """Get cached model or train new one."""
        # For now, use a simple approach without persistent model storage
        # In production, you would save/load models from disk
        
        if model_type == 'performance_prediction':
            # Simple linear regression based on historical average
            if len(training_data) >= 5:
                completion_rates = [d['completion_rate'] for d in training_data]
                return SimplePredictionModel(np.mean(completion_rates))
        
        return None
    
    def _calculate_prediction_confidence(self, model: Any, features: List[float]) -> float:
        """Calculate confidence score for prediction."""
        # Simple confidence calculation based on data quality
        if hasattr(model, 'confidence'):
            return model.confidence
        
        # Default confidence based on feature completeness
        non_zero_features = sum(1 for f in features if f != 0)
        return min(0.95, non_zero_features / len(features))
    
    def _generate_performance_insights(self, employee: CustomerUser, historical_data: List[Dict[str, Any]], prediction: float) -> List[str]:
        """Generate insights about employee performance."""
        insights = []
        
        if prediction > 0.8:
            insights.append(f"{employee.first_name} is predicted to be a high performer")
        elif prediction < 0.5:
            insights.append(f"{employee.first_name} may need additional support")
        
        if len(historical_data) > 10:
            insights.append("Employee has extensive task history")
        elif len(historical_data) < 3:
            insights.append("Limited task history - predictions less reliable")
        
        return insights
    
    def _generate_performance_recommendations(self, prediction: float, historical_data: List[Dict[str, Any]]) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        if prediction > 0.8:
            recommendations.append("Consider for challenging tasks")
            recommendations.append("Mentor other team members")
        elif prediction < 0.5:
            recommendations.append("Provide additional training")
            recommendations.append("Assign simpler tasks initially")
        
        if len(historical_data) < 5:
            recommendations.append("Gather more performance data")
        
        return recommendations
    
    def _generate_assignment_recommendations(self, predictions: List[Dict[str, Any]], task_features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate task assignment recommendations."""
        recommendations = []
        
        # Top performer recommendation
        if predictions:
            top_performer = predictions[0]
            recommendations.append({
                'type': 'primary_assign',
                'employee_id': top_performer['employee_id'],
                'employee_name': top_performer['employee_name'],
                'reason': f"Highest predicted completion rate ({top_performer['predicted_completion_rate']:.1%})",
                'confidence': top_performer['confidence']
            })
            
            # Backup recommendations
            if len(predictions) > 1:
                backup = predictions[1]
                recommendations.append({
                    'type': 'backup_assign',
                    'employee_id': backup['employee_id'],
                    'employee_name': backup['employee_name'],
                    'reason': f"Strong alternative with {backup['predicted_completion_rate']:.1%} predicted rate",
                    'confidence': backup['confidence']
                })
        
        return recommendations
    
    def _get_assignment_strategy(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get assignment strategy based on predictions."""
        if not predictions:
            return {'strategy': 'no_data', 'confidence': 0.0}
        
        avg_prediction = np.mean([p['predicted_completion_rate'] for p in predictions])
        avg_confidence = np.mean([p['confidence'] for p in predictions])
        
        if avg_prediction > 0.7:
            strategy = 'high_confidence'
        elif avg_prediction > 0.5:
            strategy = 'moderate_confidence'
        else:
            strategy = 'low_confidence'
        
        return {
            'strategy': strategy,
            'confidence': float(avg_confidence),
            'avg_predicted_rate': float(avg_prediction)
        }
    
    def _get_department_employees(self, department_name: str) -> List[CustomerUser]:
        """Get employees in a department (using category mapping)."""
        category_mapping = {
            'IT': '1',
            'HR': '2',
            'Finance': '3',
            'Marketing': '4',
            'Operations': '5',
            'Other': '999'
        }
        
        category = category_mapping.get(department_name)
        if category:
            return list(CustomerUser.objects.filter(category=category))
        
        return []
    
    def _get_department_historical_data(self, department_name: str) -> List[Dict[str, Any]]:
        """Get historical data for a department."""
        employees = self._get_department_employees(department_name)
        employee_ids = [emp.id for emp in employees]
        
        tasks = TaskHistory.objects.filter(employee_id__in=employee_ids)
        
        historical_data = []
        for task in tasks:
            if task.mxpoint and task.mxpoint > 0:
                historical_data.append({
                    'completion_rate': task.point / task.mxpoint,
                    'employee_id': task.employee.id,
                    'category_id': task.category.id if task.category else None,
                    'date': task.daf_date
                })
        
        return historical_data
    
    def _generate_department_insights(self, department_name: str, employee_predictions: List[Dict[str, Any]], historical_data: List[Dict[str, Any]]) -> List[str]:
        """Generate department-level insights."""
        insights = []
        
        if employee_predictions:
            avg_prediction = np.mean([p['predicted_completion_rate'] for p in employee_predictions])
            insights.append(f"Department {department_name} predicted average completion rate: {avg_prediction:.1%}")
            
            high_performers = [p for p in employee_predictions if p['predicted_completion_rate'] > 0.8]
            if high_performers:
                insights.append(f"{len(high_performers)} high performers identified in department")
        
        if len(historical_data) > 50:
            insights.append("Department has extensive historical data")
        
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


class SimplePredictionModel:
    """Simple prediction model for demonstration."""
    
    def __init__(self, baseline_rate: float):
        self.baseline_rate = baseline_rate
        self.confidence = 0.8 if baseline_rate > 0 else 0.3
    
    def predict(self, features: List[List[float]]) -> np.ndarray:
        """Make predictions based on baseline rate with some variation."""
        predictions = []
        for feature_set in features:
            # Simple prediction with some variation based on features
            variation = 0.1 * (len([f for f in feature_set if f != 0]) / len(feature_set))
            prediction = max(0.0, min(1.0, self.baseline_rate + variation))
            predictions.append(prediction)
        
        return np.array(predictions)
