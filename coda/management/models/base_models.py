"""
Base Models

This module provides base model classes that consolidate common functionality
and add AI-enhanced capabilities to the management app models.

Following DRY principles and providing consistent model behavior.
"""

import string
import itertools
import logging
from decimal import Decimal
from datetime import datetime, date, timedelta
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

# Import AI services for model enhancement
try:
    from ai_services.ai_integration_service import RealAIService
    AI_SERVICE_AVAILABLE = True
except ImportError:
    AI_SERVICE_AVAILABLE = False
    RealAIService = None

logger = logging.getLogger(__name__)
User = get_user_model()


class BaseTaskModel(models.Model):
    """
    Base model class consolidating common task functionality.
    
    This abstract model provides:
    - Consolidated pay calculations
    - Performance scoring
    - AI-enhanced metrics
    - Consistent validation
    - Common properties and methods
    """
    
    class Meta:
        abstract = True
    
    # Common fields that should be in both Task and TaskHistory models
    point = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Current points earned"
    )
    mxpoint = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum points possible"
    )
    mxearning = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum earnings possible"
    )
    activity_name = models.CharField(
        max_length=255,
        help_text="Name of the activity"
    )
    
    @property
    def calculated_pay(self) -> Decimal:
        """
        Consolidated pay calculation replacing get_pay methods.
        
        This replaces the duplicate get_pay methods from Task and TaskHistory models.
        """
        if self.point > self.mxpoint:
            return Decimal('0.00')
        
        try:
            base_earning = Decimal(self.point / self.mxpoint) * self.mxearning
            late_penalty = self.late_penalty_multiplier
            final_pay = base_earning * late_penalty
            return round(final_pay, 2)
        except (ZeroDivisionError, TypeError):
            return Decimal('0.00')
    
    @property
    def late_penalty_multiplier(self) -> Decimal:
        """
        Consolidated late penalty calculation.
        
        Applies penalty for late submissions.
        """
        if hasattr(self, 'deadline') and hasattr(self, 'submission'):
            if self.submission > self.deadline:
                return Decimal('0.8')  # 20% penalty for late submission
        return Decimal('1.0')
    
    @property
    def performance_score(self) -> float:
        """
        Consolidated performance score calculation.
        
        Returns performance as a percentage (0-100).
        """
        if self.mxpoint > 0:
            return float((self.point / self.mxpoint) * 100)
        return 0.0
    
    @property
    def performance_tier(self) -> str:
        """
        Get performance tier based on score.
        
        Returns: 'Excellent', 'Good', 'Fair', 'Poor'
        """
        score = self.performance_score
        if score >= 90:
            return 'Excellent'
        elif score >= 80:
            return 'Good'
        elif score >= 70:
            return 'Fair'
        else:
            return 'Poor'
    
    @property
    def ai_enhanced_metrics(self) -> dict:
        """
        AI-enhanced metrics for intelligent tasks.
        
        Returns AI-generated insights if available.
        """
        if hasattr(self, 'intelligent_task') and self.intelligent_task:
            return {
                'confidence_score': float(self.intelligent_task.ai_confidence_score),
                'complexity_score': self.intelligent_task.ai_complexity_score,
                'predicted_completion': float(self.intelligent_task.ai_predicted_completion_rate),
                'budget_impact': float(self.intelligent_task.budget_impact_score),
                'ai_generated': self.intelligent_task.ai_generated,
                'model_used': self.intelligent_task.ai_model_used
            }
        return {
            'confidence_score': 0.75,  # Default confidence
            'complexity_score': 2,     # Default medium complexity
            'predicted_completion': 0.85,  # Default 85% completion
            'budget_impact': 0.0,
            'ai_generated': False,
            'model_used': 'default'
        }
    
    def get_enhanced_url(self) -> str:
        """
        Enhanced URL generation with AI routing.
        
        Consolidates task_url logic from Task model with improvements.
        """
        try:
            activity_lower = self.activity_name.lower().translate({ord(c): None for c in string.whitespace})
            
            # Define activity patterns for routing
            one_on_one_activities = ["oneononesessions", "oneonone", "oneonesession"]
            job_support_activities = ["jobsupport", "job_support"]
            
            # Route based on activity type
            if activity_lower in one_on_one_activities:
                return reverse("application:rate")
            elif activity_lower in job_support_activities:
                return reverse("accounts:tracker-list")
            else:
                return reverse("management:new_evidence", args=[self.id])
                
        except Exception as e:
            logger.warning(f"Error generating enhanced URL for task {self.id}: {e}")
            return reverse("management:new_evidence", args=[self.id])
    
    def get_ai_validation(self) -> dict:
        """
        Get AI validation for the task.
        
        Returns validation results from AI service if available.
        """
        if not AI_SERVICE_AVAILABLE:
            return {
                'confidence_score': 0.5,
                'validation_passed': True,
                'recommendations': ['Manual review recommended'],
                'model_used': 'fallback'
            }
        
        try:
            ai_service = RealAIService()
            validation_result = ai_service.get_prediction(
                analysis_type='task_validation',
                input_data={
                    'activity_name': self.activity_name,
                    'points': float(self.point),
                    'max_points': float(self.mxpoint),
                    'earnings': float(self.calculated_pay)
                },
                session_id=f"task_validation_{self.id}_{timezone.now().timestamp()}"
            )
            
            return {
                'confidence_score': validation_result.get('confidence_score', 0.75),
                'validation_passed': validation_result.get('confidence_score', 0.75) >= 0.7,
                'recommendations': validation_result.get('recommendations', []),
                'model_used': validation_result.get('model_used', 'ai')
            }
            
        except Exception as e:
            logger.warning(f"AI validation failed for task {self.id}: {e}")
            return {
                'confidence_score': 0.5,
                'validation_passed': True,
                'recommendations': ['AI validation unavailable'],
                'model_used': 'fallback'
            }
    
    def clean(self):
        """Enhanced validation with AI assistance."""
        super().clean()
        
        # Basic validation
        if self.point < 0:
            raise ValidationError("Points cannot be negative")
        
        if self.mxpoint <= 0:
            raise ValidationError("Maximum points must be greater than zero")
        
        if self.mxearning <= 0:
            raise ValidationError("Maximum earnings must be greater than zero")
        
        if self.point > self.mxpoint:
            raise ValidationError("Points cannot exceed maximum points")
        
        # AI-enhanced validation if available
        if AI_SERVICE_AVAILABLE and hasattr(self, 'intelligent_task') and self.intelligent_task:
            ai_validation = self.get_ai_validation()
            if not ai_validation.get('validation_passed', True):
                raise ValidationError(f"AI validation failed: {ai_validation.get('recommendations', ['Please review task data'])}")
    
    def save(self, *args, **kwargs):
        """Enhanced save with AI processing."""
        # Add AI processing before save
        if not hasattr(self, 'intelligent_task') or not self.intelligent_task:
            self._create_intelligent_task()
        
        super().save(*args, **kwargs)
    
    def _create_intelligent_task(self):
        """Create intelligent task with AI analysis if not exists."""
        try:
            # Check if intelligent task already exists
            if hasattr(self, 'intelligent_task') and self.intelligent_task:
                return
            
            # Import here to avoid circular imports
            from management.models import IntelligentTask
            
            # Get AI analysis if available
            ai_analysis = None
            if AI_SERVICE_AVAILABLE:
                try:
                    ai_service = RealAIService()
                    ai_analysis = ai_service.get_prediction(
                        analysis_type='task_creation_analysis',
                        input_data={
                            'activity_name': self.activity_name,
                            'points': float(self.point),
                            'max_points': float(self.mxpoint),
                            'category': self.category.title if hasattr(self, 'category') and self.category else 'General'
                        },
                        session_id=f"task_creation_{self.id}"
                    )
                except Exception as e:
                    logger.warning(f"AI analysis failed for task {self.id}: {e}")
            
            # Create intelligent task
            IntelligentTask.objects.create(
                task=self,
                ai_generated=False,
                ai_confidence_score=ai_analysis.get('confidence_score', 0.75) if ai_analysis else 0.75,
                ai_model_used=ai_analysis.get('model_used', 'gpt4_primary') if ai_analysis else 'default',
                ai_complexity_score=ai_analysis.get('complexity_score', 2) if ai_analysis else 2,
                auto_evidence_enabled=ai_analysis.get('auto_evidence_enabled', False) if ai_analysis else False
            )
            
        except Exception as e:
            logger.error(f"Failed to create intelligent task for {self.id}: {e}")
    
    @classmethod
    def get_performance_statistics(cls, queryset=None):
        """
        Get performance statistics for a queryset of tasks.
        
        Returns comprehensive performance metrics.
        """
        if queryset is None:
            queryset = cls.objects.all()
        
        try:
            total_tasks = queryset.count()
            if total_tasks == 0:
                return {
                    'total_tasks': 0,
                    'average_performance': 0.0,
                    'completion_rate': 0.0,
                    'performance_distribution': {}
                }
            
            # Calculate statistics
            total_points = sum(task.point for task in queryset)
            total_max_points = sum(task.mxpoint for task in queryset)
            completed_tasks = sum(1 for task in queryset if task.point >= task.mxpoint * Decimal('0.8'))
            
            average_performance = float(total_points / total_max_points) if total_max_points > 0 else 0.0
            completion_rate = completed_tasks / total_tasks
            
            # Performance distribution
            performance_distribution = {
                'excellent': sum(1 for task in queryset if task.performance_score >= 90),
                'good': sum(1 for task in queryset if 80 <= task.performance_score < 90),
                'fair': sum(1 for task in queryset if 70 <= task.performance_score < 80),
                'poor': sum(1 for task in queryset if task.performance_score < 70)
            }
            
            return {
                'total_tasks': total_tasks,
                'average_performance': average_performance,
                'completion_rate': completion_rate,
                'performance_distribution': performance_distribution,
                'total_points_earned': float(total_points),
                'total_points_possible': float(total_max_points)
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance statistics: {e}")
            return {
                'total_tasks': 0,
                'average_performance': 0.0,
                'completion_rate': 0.0,
                'performance_distribution': {},
                'error': str(e)
            }


class BaseEvidenceModel(models.Model):
    """
    Base model class for evidence-related models.
    
    Provides common functionality for evidence validation and AI processing.
    """
    
    class Meta:
        abstract = True
    
    # Common evidence fields
    link_name = models.CharField(max_length=255, default="General")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    @property
    def evidence_quality_score(self) -> float:
        """
        Calculate evidence quality score.
        
        Returns a score from 0-1 based on evidence completeness and quality.
        """
        score = 0.0
        
        # Check for description
        if self.description and len(self.description.strip()) > 10:
            score += 0.3
        
        # Check for link
        if hasattr(self, 'link') and self.link:
            score += 0.3
        
        # Check for document
        if hasattr(self, 'doc') and self.doc:
            score += 0.4
        
        return min(score, 1.0)
    
    @property
    def evidence_completeness(self) -> dict:
        """
        Get evidence completeness breakdown.
        
        Returns detailed completeness information.
        """
        return {
            'has_description': bool(self.description and len(self.description.strip()) > 10),
            'has_link': bool(hasattr(self, 'link') and self.link),
            'has_document': bool(hasattr(self, 'doc') and self.doc),
            'quality_score': self.evidence_quality_score,
            'completeness_percentage': int(self.evidence_quality_score * 100)
        }
    
    def get_ai_validation(self) -> dict:
        """
        Get AI validation for evidence.
        
        Returns AI validation results if available.
        """
        if not AI_SERVICE_AVAILABLE:
            return {
                'validation_passed': True,
                'confidence_score': 0.5,
                'recommendations': ['Manual review recommended'],
                'model_used': 'fallback'
            }
        
        try:
            ai_service = RealAIService()
            validation_result = ai_service.get_prediction(
                analysis_type='evidence_validation',
                input_data={
                    'link_name': self.link_name,
                    'description': self.description,
                    'quality_score': self.evidence_quality_score,
                    'has_link': bool(hasattr(self, 'link') and self.link),
                    'has_document': bool(hasattr(self, 'doc') and self.doc)
                },
                session_id=f"evidence_validation_{self.id}_{timezone.now().timestamp()}"
            )
            
            return {
                'validation_passed': validation_result.get('confidence_score', 0.5) >= 0.7,
                'confidence_score': validation_result.get('confidence_score', 0.5),
                'recommendations': validation_result.get('recommendations', []),
                'model_used': validation_result.get('model_used', 'ai')
            }
            
        except Exception as e:
            logger.warning(f"AI evidence validation failed for {self.id}: {e}")
            return {
                'validation_passed': True,
                'confidence_score': 0.5,
                'recommendations': ['AI validation unavailable'],
                'model_used': 'fallback'
            }
    
    def clean(self):
        """Enhanced validation for evidence."""
        super().clean()
        
        # Basic validation
        if not self.link_name or len(self.link_name.strip()) < 2:
            raise ValidationError("Link name must be at least 2 characters long")
        
        # AI-enhanced validation if available
        if AI_SERVICE_AVAILABLE:
            ai_validation = self.get_ai_validation()
            if not ai_validation.get('validation_passed', True):
                raise ValidationError(f"AI validation suggests reviewing evidence: {ai_validation.get('recommendations', ['Please check evidence quality'])}")


class ModelMixin:
    """
    Mixin class providing common model functionality.
    
    Can be mixed into any model to provide enhanced capabilities.
    """
    
    def get_ai_insights(self) -> dict:
        """
        Get AI insights for the model instance.
        
        Returns AI-generated insights if available.
        """
        if not AI_SERVICE_AVAILABLE:
            return {
                'insights_available': False,
                'message': 'AI service not available',
                'recommendations': ['Manual review recommended']
            }
        
        try:
            ai_service = RealAIService()
            insights = ai_service.get_prediction(
                analysis_type='model_insights',
                input_data=self._prepare_insights_data(),
                session_id=f"model_insights_{self.__class__.__name__}_{self.pk}_{timezone.now().timestamp()}"
            )
            
            return {
                'insights_available': True,
                'confidence_score': insights.get('confidence_score', 0.75),
                'recommendations': insights.get('recommendations', []),
                'model_used': insights.get('model_used', 'ai'),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"AI insights failed for {self.__class__.__name__} {self.pk}: {e}")
            return {
                'insights_available': False,
                'message': 'AI insights unavailable',
                'recommendations': ['Manual review recommended'],
                'error': str(e)
            }
    
    def _prepare_insights_data(self) -> dict:
        """
        Prepare data for AI insights analysis.
        
        Should be overridden by models that use this mixin.
        """
        return {
            'model_type': self.__class__.__name__,
            'instance_id': self.pk,
            'timestamp': timezone.now().isoformat()
        }
    
    def log_activity(self, activity: str, details: dict = None):
        """
        Log activity for this model instance.
        
        Useful for tracking changes and user interactions.
        """
        logger.info(f"Activity: {activity}, Model: {self.__class__.__name__}, ID: {self.pk}, Details: {details}")
    
    def get_performance_metrics(self) -> dict:
        """
        Get performance metrics for this model instance.
        
        Should be overridden by models that have performance-related data.
        """
        return {
            'model_type': self.__class__.__name__,
            'instance_id': self.pk,
            'metrics_available': False,
            'message': 'Performance metrics not implemented for this model'
        }
