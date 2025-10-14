"""
Base Views

This module provides base view classes and common view patterns
for consistent behavior across the management app.

Following DRY principles and providing AI-enhanced functionality.
"""

import logging
from typing import Dict, Any, Optional
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

# Import our utilities service
from management.services.utilities_service import UtilitiesService

# Import models
from management.models import Task, TaskHistory, TaskLinks, TaskCategory
from accounts.models import CustomerUser

logger = logging.getLogger(__name__)


class BaseTaskView(LoginRequiredMixin, View):
    """
    Base view class consolidating common task view logic.
    
    This class provides:
    - Common context data preparation
    - AI integration handling
    - Error handling and logging
    - Form processing with AI validation
    - Performance monitoring
    """
    
    def __init__(self):
        super().__init__()
        self.utilities_service = UtilitiesService()
        self.logger = logger
        
        # Initialize AI services
        try:
            from ai_services.ai_integration_service import RealAIService
            self.ai_service = RealAIService()
            self.ai_service_available = True
        except ImportError:
            self.ai_service = None
            self.ai_service_available = False
        
        try:
            from finance.services.ai_budget_suggestion_service import AIBudgetSuggestionService
            self.budget_service = AIBudgetSuggestionService()
            self.budget_service_available = True
        except ImportError:
            self.budget_service = None
            self.budget_service_available = False
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Consolidate common context data preparation.
        
        Provides consistent context data across all task-related views.
        """
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}
        
        # Add common context data
        context.update({
            'ai_service_available': self.ai_service_available,
            'budget_service_available': self.budget_service_available,
            'current_user': getattr(self.request, 'user', None),
            'current_time': timezone.now(),
            'service_health': self.utilities_service.get_service_health_status()
        })
        
        # Add AI insights if available
        if self.ai_service_available:
            try:
                context['ai_insights'] = self._get_ai_insights()
            except Exception as e:
                self.logger.warning(f"Failed to get AI insights: {e}")
                context['ai_insights'] = None
        
        # Add budget data if available
        if self.budget_service_available:
            try:
                context['budget_data'] = self._get_budget_data()
            except Exception as e:
                self.logger.warning(f"Failed to get budget data: {e}")
                context['budget_data'] = None
        
        return context
    
    def handle_ai_integration(self, analysis_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consolidated AI integration handling.
        
        Provides consistent AI service integration with error handling and fallback.
        
        Args:
            analysis_type: Type of AI analysis to perform
            input_data: Data to send to AI service
            
        Returns:
            Dict with AI analysis results or fallback data
        """
        if not self.ai_service_available:
            return self._get_fallback_data(analysis_type)
        
        try:
            session_id = f"{analysis_type}_{self.request.user.id}_{timezone.now().timestamp()}"
            result = self.ai_service.get_prediction(
                analysis_type=analysis_type,
                input_data=input_data,
                session_id=session_id
            )
            
            self.logger.info(f"AI integration successful for {analysis_type}")
            return result
            
        except Exception as e:
            self.logger.error(f"AI integration failed for {analysis_type}: {e}")
            return self._get_fallback_data(analysis_type)
    
    def process_form_with_ai(self, form, task: Optional[Task] = None) -> Dict[str, Any]:
        """
        Consolidated form processing with AI validation.
        
        Processes forms with AI validation and provides consistent error handling.
        
        Args:
            form: Django form instance
            task: Optional task instance for context
            
        Returns:
            Dict with form processing results
        """
        if not form.is_valid():
            return {
                'success': False,
                'form': form,
                'message': 'Form validation failed',
                'ai_validation': None
            }
        
        # Add AI validation if available
        ai_validation = None
        if self.ai_service_available:
            try:
                ai_validation = self.handle_ai_integration(
                    analysis_type='form_validation',
                    input_data={
                        'form_data': form.cleaned_data,
                        'task_id': task.id if task else None,
                        'user_id': self.request.user.id
                    }
                )
                
                # Check AI validation confidence
                confidence = ai_validation.get('confidence_score', 0)
                if confidence < 0.7:
                    form.add_error(None, "AI validation suggests reviewing your input.")
                    return {
                        'success': False,
                        'form': form,
                        'message': 'AI validation failed',
                        'ai_validation': ai_validation
                    }
                    
            except Exception as e:
                self.logger.warning(f"AI form validation failed: {e}")
        
        # Process form if validation passes
        try:
            with transaction.atomic():
                instance = form.save()
                
                # Log successful form processing
                self.utilities_service.log_operation(
                    operation='form_processing',
                    employee_id=self.request.user.id,
                    details={
                        'form_type': form.__class__.__name__,
                        'task_id': task.id if task else None,
                        'ai_validation_used': bool(ai_validation)
                    }
                )
                
                return {
                    'success': True,
                    'instance': instance,
                    'message': 'Form processed successfully',
                    'ai_validation': ai_validation
                }
                
        except Exception as e:
            self.logger.error(f"Form processing failed: {e}")
            return {
                'success': False,
                'form': form,
                'message': f'Form processing failed: {str(e)}',
                'ai_validation': ai_validation
            }
    
    def _get_ai_insights(self) -> Optional[Dict[str, Any]]:
        """Get AI insights for the current context."""
        try:
            if not self.ai_service_available:
                return None
            
            # Get basic AI insights
            return self.handle_ai_integration(
                analysis_type='general_insights',
                input_data={
                    'user_id': self.request.user.id,
                    'current_view': self.__class__.__name__,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            self.logger.warning(f"Failed to get AI insights: {e}")
            return None
    
    def _get_budget_data(self) -> Optional[Dict[str, Any]]:
        """Get budget data for the current context."""
        try:
            if not self.budget_service_available:
                return None
            
            # Get budget insights if user has department
            if hasattr(self.request.user, 'department') and self.request.user.department:
                return self.budget_service.get_intelligent_suggestions(
                    company=getattr(self.request.user.department, 'company', None),
                    department=self.request.user.department,
                    horizon='monthly'
                )
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to get budget data: {e}")
            return None
    
    def _get_fallback_data(self, analysis_type: str) -> Dict[str, Any]:
        """Get fallback data when AI services are unavailable."""
        fallback_data = {
            'confidence_score': 0.5,
            'model_used': 'fallback',
            'analysis_type': analysis_type,
            'timestamp': timezone.now().isoformat(),
            'message': 'AI service unavailable, using fallback data'
        }
        
        # Provide specific fallback data based on analysis type
        if analysis_type == 'form_validation':
            fallback_data.update({
                'validation_passed': True,
                'recommendations': ['Manual review recommended']
            })
        elif analysis_type == 'task_performance_analysis':
            fallback_data.update({
                'performance_summary': 'Good performance',
                'recommendations': ['Continue current approach']
            })
        elif analysis_type == 'general_insights':
            fallback_data.update({
                'insights': ['System functioning normally'],
                'recommendations': ['Regular monitoring recommended']
            })
        
        return fallback_data


class TaskListView(BaseTaskView, ListView):
    """
    Consolidated task list view replacing multiple similar views.
    
    Provides:
    - Unified task listing with AI filtering
    - Consistent pagination and sorting
    - AI-enhanced context data
    - Performance optimization
    """
    
    model = Task
    template_name = 'management/daf/consolidated_task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Enhanced queryset with AI filtering and optimization."""
        base_queryset = super().get_queryset()
        
        # Apply user-specific filtering
        if not self.request.user.is_superuser:
            base_queryset = base_queryset.filter(employee=self.request.user)
        
        # Apply AI-enhanced filtering if available
        ai_filter = self.request.GET.get('ai_filter')
        if ai_filter and self.ai_service_available:
            try:
                filtered_queryset = self._apply_ai_filter(base_queryset, ai_filter)
                if filtered_queryset is not None:
                    base_queryset = filtered_queryset
            except Exception as e:
                self.logger.warning(f"AI filtering failed: {e}")
        
        # Apply category filtering
        category_filter = self.request.GET.get('category')
        if category_filter:
            base_queryset = base_queryset.filter(category_id=category_filter)
        
        # Apply status filtering
        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            base_queryset = base_queryset.filter(is_active=True)
        elif status_filter == 'completed':
            base_queryset = base_queryset.filter(is_active=False)
        
        return base_queryset.select_related('employee', 'category', 'groupname').prefetch_related('tasklinks_set')
    
    def get_context_data(self, **kwargs):
        """Enhanced context with AI insights and performance data."""
        context = super().get_context_data(**kwargs)
        
        # Add task-specific context
        tasks = context.get('tasks', [])
        context.update({
            'total_tasks': tasks.count() if hasattr(tasks, 'count') else len(tasks),
            'active_tasks': tasks.filter(is_active=True).count() if hasattr(tasks, 'filter') else 0,
            'categories': TaskCategory.objects.all(),
            'ai_filter_options': self._get_ai_filter_options(),
        })
        
        # Add task-specific AI insights
        if tasks and self.ai_service_available:
            try:
                context['task_insights'] = self.utilities_service.get_tasks_with_ai_enhancement(
                    employee=self.request.user,
                    selected_month=timezone.now().month,
                    selected_year=timezone.now().year,
                    pay_type='tasks'
                )
            except Exception as e:
                self.logger.warning(f"Failed to get task insights: {e}")
                context['task_insights'] = None
        
        return context
    
    def _apply_ai_filter(self, queryset, ai_filter: str):
        """Apply AI-enhanced filtering to queryset."""
        try:
            # Get AI filtering recommendations
            ai_analysis = self.handle_ai_integration(
                analysis_type='task_filtering',
                input_data={
                    'filter_type': ai_filter,
                    'user_id': self.request.user.id,
                    'current_tasks': list(queryset.values_list('id', flat=True)[:10])
                }
            )
            
            # Apply filtering based on AI recommendations
            if ai_analysis.get('filter_criteria'):
                criteria = ai_analysis['filter_criteria']
                if 'category_ids' in criteria:
                    queryset = queryset.filter(category_id__in=criteria['category_ids'])
                if 'priority_levels' in criteria:
                    queryset = queryset.filter(point__gte=criteria['priority_levels'])
            
            return queryset
            
        except Exception as e:
            self.logger.warning(f"AI filtering failed: {e}")
            return None
    
    def _get_ai_filter_options(self) -> List[Dict[str, str]]:
        """Get AI filter options for the template."""
        return [
            {'value': 'high_priority', 'label': 'High Priority Tasks'},
            {'value': 'near_deadline', 'label': 'Near Deadline'},
            {'value': 'recommended', 'label': 'AI Recommended'},
            {'value': 'performance_boost', 'label': 'Performance Boost'},
        ]


class PayslipView(BaseTaskView, TemplateView):
    """
    Consolidated payslip view with AI enhancement.
    
    Provides:
    - Comprehensive payroll calculation
    - AI-enhanced insights and predictions
    - Budget integration
    - Performance analytics
    """
    
    template_name = 'management/daf/consolidated_payslip.html'
    
    def get_context_data(self, **kwargs):
        """Enhanced context with comprehensive payroll data."""
        context = super().get_context_data(**kwargs)
        
        # Get selected month and year
        selected_month = int(self.request.GET.get('month', timezone.now().month))
        selected_year = int(self.request.GET.get('year', timezone.now().year))
        
        # Get comprehensive payroll data using enhanced utilities
        payroll_data = self.utilities_service.calculate_comprehensive_payroll(
            employee=self.request.user,
            month=selected_month,
            year=selected_year
        )
        
        # Get tasks data with AI enhancement
        tasks_data = self.utilities_service.get_tasks_with_ai_enhancement(
            employee=self.request.user,
            selected_month=selected_month,
            selected_year=selected_year,
            pay_type='payslip'
        )
        
        # Add comprehensive context
        context.update({
            'payroll_data': payroll_data,
            'tasks_data': tasks_data,
            'selected_month': selected_month,
            'selected_year': selected_year,
            'month_name': timezone.datetime(selected_year, selected_month, 1).strftime('%B'),
            'performance_summary': self._get_performance_summary(tasks_data.get('tasks')),
        })
        
        return context
    
    def _get_performance_summary(self, tasks) -> Dict[str, Any]:
        """Get performance summary from tasks."""
        if not tasks:
            return {
                'total_tasks': 0,
                'completion_rate': 0,
                'average_score': 0,
                'performance_tier': 'No Data'
            }
        
        try:
            metrics = self.utilities_service._calculate_performance_metrics(tasks)
            return {
                'total_tasks': metrics['total_tasks'],
                'completion_rate': metrics['completion_rate'],
                'average_score': metrics['average_score'],
                'performance_tier': 'High' if metrics['average_score'] >= 0.9 else 'Medium' if metrics['average_score'] >= 0.7 else 'Low'
            }
        except Exception as e:
            self.logger.error(f"Error calculating performance summary: {e}")
            return {
                'total_tasks': 0,
                'completion_rate': 0,
                'average_score': 0,
                'performance_tier': 'Error'
            }


class EvidenceView(BaseTaskView, CreateView):
    """
    Consolidated evidence view with AI validation.
    
    Provides:
    - AI-enhanced evidence validation
    - GoToMeeting integration
    - Quality scoring
    - Automated recommendations
    """
    
    model = TaskLinks
    template_name = 'management/daf/consolidated_evidence_form.html'
    fields = ['link_name', 'description', 'link', 'linkpassword', 'doc']
    
    def get_context_data(self, **kwargs):
        """Enhanced context with AI validation and task information."""
        context = super().get_context_data(**kwargs)
        
        # Get task information
        task_id = self.kwargs.get('task_id')
        task = get_object_or_404(Task, id=task_id)
        
        # Get AI validation recommendations if available
        ai_recommendations = None
        if self.ai_service_available:
            try:
                ai_recommendations = self.handle_ai_integration(
                    analysis_type='evidence_recommendations',
                    input_data={
                        'task_activity': task.activity_name,
                        'task_category': task.category.title if task.category else 'General',
                        'user_id': self.request.user.id
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to get AI evidence recommendations: {e}")
        
        context.update({
            'task': task,
            'ai_recommendations': ai_recommendations,
            'existing_evidence': task.tasklinks_set.filter(is_active=True),
        })
        
        return context
    
    def form_valid(self, form):
        """Process form with AI validation."""
        # Set the task and added_by fields
        task_id = self.kwargs.get('task_id')
        task = get_object_or_404(Task, id=task_id)
        
        form.instance.task = task
        form.instance.added_by = self.request.user
        
        # Process with AI validation
        result = self.process_form_with_ai(form, task)
        
        if result['success']:
            messages.success(self.request, 'Evidence submitted successfully!')
            
            # Log successful evidence submission
            self.utilities_service.log_operation(
                operation='evidence_submission',
                employee_id=self.request.user.id,
                details={
                    'task_id': task.id,
                    'evidence_type': form.instance.link_name,
                    'ai_validation_used': bool(result.get('ai_validation'))
                }
            )
            
            return redirect('management:taskdetail', pk=task.id)
        else:
            messages.error(self.request, result['message'])
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle invalid form with proper error messages."""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class UserEvidenceView(BaseTaskView, ListView):
    """
    Consolidated user evidence view with AI insights.
    
    Provides:
    - User's evidence history
    - AI quality analysis
    - Performance tracking
    - Improvement recommendations
    """
    
    model = TaskLinks
    template_name = 'management/daf/consolidated_user_evidence.html'
    context_object_name = 'evidence_list'
    paginate_by = 15
    
    def get_queryset(self):
        """Get user's evidence with AI quality analysis."""
        base_queryset = TaskLinks.objects.filter(
            added_by=self.request.user,
            is_active=True
        ).select_related('task', 'task__category').order_by('-created_at')
        
        return base_queryset
    
    def get_context_data(self, **kwargs):
        """Enhanced context with AI quality analysis."""
        context = super().get_context_data(**kwargs)
        
        # Get evidence quality analysis if AI is available
        evidence_quality = None
        if self.ai_service_available and context.get('evidence_list'):
            try:
                evidence_quality = self._analyze_evidence_quality(context['evidence_list'])
            except Exception as e:
                self.logger.warning(f"Failed to analyze evidence quality: {e}")
        
        context.update({
            'evidence_quality': evidence_quality,
            'total_evidence': context['evidence_list'].count() if hasattr(context['evidence_list'], 'count') else len(context['evidence_list']),
        })
        
        return context
    
    def _analyze_evidence_quality(self, evidence_list) -> Dict[str, Any]:
        """Analyze evidence quality using AI."""
        try:
            # Prepare evidence data for AI analysis
            evidence_data = []
            for evidence in evidence_list[:10]:  # Limit to recent evidence
                evidence_data.append({
                    'link_name': evidence.link_name,
                    'description': evidence.description,
                    'has_document': bool(evidence.doc),
                    'has_link': bool(evidence.link),
                    'task_activity': evidence.task.activity_name if evidence.task else 'Unknown'
                })
            
            ai_analysis = self.handle_ai_integration(
                analysis_type='evidence_quality_analysis',
                input_data={
                    'evidence_data': evidence_data,
                    'user_id': self.request.user.id
                }
            )
            
            return {
                'quality_score': ai_analysis.get('quality_score', 0.75),
                'recommendations': ai_analysis.get('recommendations', []),
                'strengths': ai_analysis.get('strengths', []),
                'improvement_areas': ai_analysis.get('improvement_areas', [])
            }
            
        except Exception as e:
            self.logger.warning(f"Evidence quality analysis failed: {e}")
            return {
                'quality_score': 0.75,
                'recommendations': ['Continue current approach'],
                'strengths': ['Good evidence submission'],
                'improvement_areas': ['Consider adding more detailed descriptions']
            }
