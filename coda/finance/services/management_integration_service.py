"""
Management Integration Service for Finance App

Phase 2: Budget Integration
Service to consume Management Budget Integration APIs for Finance budget estimation.

This service provides a clean interface for Finance services to consume
Management activity data via HTTP APIs or direct service calls.

When both apps are in the same Django project, uses direct service calls.
When apps are separate, uses HTTP API calls.

Phase 3: Enhanced with error recovery, caching, and data validation.
"""

import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta

from finance.services.api_error_recovery import APIErrorRecovery, with_error_recovery

logger = logging.getLogger(__name__)

# Try to import requests for HTTP calls, but make it optional
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests library not available, HTTP API calls will be disabled")


class ManagementIntegrationService:
    """
    Service to integrate Finance app with Management Budget Integration APIs.
    
    Provides methods to consume:
    - Budget Activity Totals API
    - Budget Evidence Validation API
    """
    
    def __init__(self, base_url: Optional[str] = None, use_cache: bool = True):
        """
        Initialize the service.
        
        Args:
            base_url: Base URL for Management app APIs (defaults to settings.SITEURL)
            use_cache: Whether to use response caching (default: True)
        """
        self.base_url = base_url or getattr(settings, 'SITEURL', 'http://localhost:8000')
        self.logger = logging.getLogger(__name__)
        self.use_cache = use_cache
        
        # API endpoints
        self.activity_totals_endpoint = f"{self.base_url}/management/api/budget/activity-totals/"
        self.evidence_validation_endpoint = f"{self.base_url}/management/api/budget/evidence-validation/"
        
        # Error recovery service
        self.error_recovery = APIErrorRecovery(
            max_retries=3,
            initial_delay=1.0,
            backoff_factor=2.0,
            cache_timeout=3600  # 1 hour
        )
    
    @with_error_recovery(max_retries=3, cache_timeout=3600, use_cache=True)
    def get_activity_totals(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None,
        department_id: Optional[int] = None,
        category_id: Optional[int] = None,
        include_evidence: bool = True,
        include_validation: bool = True,
        session: Optional[Any] = None,
        use_direct_call: bool = True
    ) -> Dict[str, Any]:
        """
        Get validated activity totals from Management API.
        
        Phase 2: Supports both direct service calls (same Django project) and HTTP API calls.
        
        Args:
            month: Target month (1-12) - default: last month
            year: Target year (YYYY) - default: current year
            department_id: Optional department filter
            category_id: Optional category filter
            include_evidence: Include evidence counts (default: True)
            include_validation: Include validation status (default: True)
            session: Optional requests.Session for authenticated HTTP requests
            use_direct_call: If True, use direct service call instead of HTTP (default: True)
        
        Returns:
            Dict with activity totals data:
            {
                'success': bool,
                'data': {...},
                'meta': {...},
                'errors': [...]
            }
        """
        # Try direct service call first (same Django project)
        if use_direct_call:
            try:
                from management.views.budget_integration_views import budget_activity_totals_api
                from django.test import RequestFactory
                
                # Create a mock request with a staff user for authentication
                factory = RequestFactory()
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                # Get or create a system user for API calls
                system_user, _ = User.objects.get_or_create(
                    username='system_api',
                    defaults={
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True
                    }
                )
                
                request = factory.get(
                    self.activity_totals_endpoint,
                    {
                        'month': month,
                        'year': year,
                        'department_id': department_id,
                        'category_id': category_id,
                        'include_evidence': 'true' if include_evidence else 'false',
                        'include_validation': 'true' if include_validation else 'false'
                    }
                )
                request.user = system_user  # Set user for authentication
                
                # Call the view directly
                response = budget_activity_totals_api(request)
                
                if hasattr(response, 'content'):
                    import json
                    result = json.loads(response.content.decode('utf-8'))
                else:
                    result = response
                
                self.logger.info(
                    f"Successfully fetched activity totals via direct call for {month}/{year}"
                )
                
                return {
                    'success': True,
                    'data': result.get('data', {}),
                    'meta': result.get('meta', {}),
                    'errors': result.get('errors', []),
                    'source': 'direct_call'
                }
                
            except ImportError as e:
                self.logger.warning(f"Direct service call failed (ImportError): {e}")
                if not REQUESTS_AVAILABLE:
                    return {
                        'success': False,
                        'data': {},
                        'meta': {},
                        'errors': [f'Direct call failed and HTTP API not available: {str(e)}']
                    }
                # Fall through to HTTP API only if requests is available
            except Exception as e:
                error_msg = str(e).lower()
                self.logger.warning(f"Direct service call failed: {e}")
                # Don't fall back to HTTP for auth/permission errors
                if any(keyword in error_msg for keyword in ['login', 'permission', 'authentication', 'unauthorized']):
                    return {
                        'success': False,
                        'data': {},
                        'meta': {},
                        'errors': [f'Direct call failed (authentication/permission issue): {str(e)}']
                    }
                if not REQUESTS_AVAILABLE:
                    return {
                        'success': False,
                        'data': {},
                        'meta': {},
                        'errors': [f'Direct call failed and HTTP API not available: {str(e)}']
                    }
                # Fall through to HTTP API for other errors
        
        # HTTP API call (for separate services or when direct call fails)
        if not REQUESTS_AVAILABLE:
            return {
                'success': False,
                'data': {},
                'meta': {},
                'errors': ['HTTP API calls require requests library']
            }
        
        try:
            # Default to last month if not specified
            if month is None or year is None:
                last_month = date.today() - relativedelta(months=1)
                month = month or last_month.month
                year = year or last_month.year
            
            # Build query parameters
            params = {
                'month': month,
                'year': year,
                'include_evidence': 'true' if include_evidence else 'false',
                'include_validation': 'true' if include_validation else 'false'
            }
            
            if department_id:
                params['department_id'] = department_id
            if category_id:
                params['category_id'] = category_id
            
            # Make API request
            if session:
                response = session.get(self.activity_totals_endpoint, params=params)
            else:
                response = requests.get(self.activity_totals_endpoint, params=params)
            
            response.raise_for_status()
            result = response.json()
            
            self.logger.info(
                f"Successfully fetched activity totals via HTTP API for {month}/{year}"
            )
            
            response_data = {
                'success': True,
                'data': result.get('data', {}),
                'meta': result.get('meta', {}),
                'errors': result.get('errors', []),
                'source': 'http_api'
            }
            
            # Validate data completeness
            if response_data['success']:
                validation = self.error_recovery.validate_data_completeness(
                    response_data['data'],
                    required_fields=['period', 'totals'],
                    min_records=0
                )
                
                if not validation['is_complete']:
                    response_data['warnings'] = response_data.get('warnings', [])
                    response_data['warnings'].extend(validation['warnings'])
                    self.logger.warning(f"Data completeness issues: {validation}")
                
                # Check data freshness
                freshness = self.error_recovery.check_data_freshness(
                    response_data,
                    max_age_hours=24
                )
                
                if not freshness['is_fresh']:
                    response_data['warnings'] = response_data.get('warnings', [])
                    response_data['warnings'].extend(freshness['warnings'])
                    self.logger.warning(f"Data freshness issues: {freshness}")
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Error calling Management Activity Totals API: {e}", exc_info=True)
            return {
                'success': False,
                'data': {},
                'meta': {},
                'errors': [f'API request failed: {str(e)}']
            }
    
    def get_evidence_validation(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None,
        department_id: Optional[int] = None,
        category_id: Optional[int] = None,
        min_confidence: float = 0.8,
        session: Optional[Any] = None,
        use_direct_call: bool = True
    ) -> Dict[str, Any]:
        """
        Get evidence validation data from Management API.
        
        Phase 2: Supports both direct service calls (same Django project) and HTTP API calls.
        
        Args:
            month: Target month (1-12) - default: last month
            year: Target year (YYYY) - default: current year
            department_id: Optional department filter
            category_id: Optional category filter
            min_confidence: Minimum confidence score (default: 0.8)
            session: Optional requests.Session for authenticated HTTP requests
            use_direct_call: If True, use direct service call instead of HTTP (default: True)
        
        Returns:
            Dict with evidence validation data:
            {
                'success': bool,
                'data': {...},
                'meta': {...},
                'errors': [...]
            }
        """
        # Try direct service call first (same Django project)
        if use_direct_call:
            try:
                from management.views.budget_integration_views import budget_evidence_validation_api
                from django.test import RequestFactory
                
                # Create a mock request with a staff user for authentication
                factory = RequestFactory()
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                # Get or create a system user for API calls
                system_user, _ = User.objects.get_or_create(
                    username='system_api',
                    defaults={
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True
                    }
                )
                
                request = factory.get(
                    self.evidence_validation_endpoint,
                    {
                        'month': month,
                        'year': year,
                        'department_id': department_id,
                        'category_id': category_id,
                        'min_confidence': min_confidence
                    }
                )
                request.user = system_user  # Set user for authentication
                
                # Call the view directly
                response = budget_evidence_validation_api(request)
                
                if hasattr(response, 'content'):
                    import json
                    result = json.loads(response.content.decode('utf-8'))
                else:
                    result = response
                
                self.logger.info(
                    f"Successfully fetched evidence validation via direct call for {month}/{year}"
                )
                
                return {
                    'success': True,
                    'data': result.get('data', {}),
                    'meta': result.get('meta', {}),
                    'errors': result.get('errors', []),
                    'source': 'direct_call'
                }
                
            except ImportError as e:
                self.logger.warning(f"Direct service call failed (ImportError): {e}")
                if not REQUESTS_AVAILABLE:
                    return {
                        'success': False,
                        'data': {},
                        'meta': {},
                        'errors': [f'Direct call failed and HTTP API not available: {str(e)}']
                    }
                # Fall through to HTTP API only if requests is available
            except Exception as e:
                error_msg = str(e).lower()
                self.logger.warning(f"Direct service call failed: {e}")
                # Don't fall back to HTTP for auth/permission errors
                if any(keyword in error_msg for keyword in ['login', 'permission', 'authentication', 'unauthorized']):
                    return {
                        'success': False,
                        'data': {},
                        'meta': {},
                        'errors': [f'Direct call failed (authentication/permission issue): {str(e)}']
                    }
                if not REQUESTS_AVAILABLE:
                    return {
                        'success': False,
                        'data': {},
                        'meta': {},
                        'errors': [f'Direct call failed and HTTP API not available: {str(e)}']
                    }
                # Fall through to HTTP API for other errors
        
        # HTTP API call (for separate services or when direct call fails)
        if not REQUESTS_AVAILABLE:
            return {
                'success': False,
                'data': {},
                'meta': {},
                'errors': ['HTTP API calls require requests library']
            }
        
        try:
            # Default to last month if not specified
            if month is None or year is None:
                last_month = date.today() - relativedelta(months=1)
                month = month or last_month.month
                year = year or last_month.year
            
            # Build query parameters
            params = {
                'month': month,
                'year': year,
                'min_confidence': min_confidence
            }
            
            if department_id:
                params['department_id'] = department_id
            if category_id:
                params['category_id'] = category_id
            
            # Make API request
            if session:
                response = session.get(self.evidence_validation_endpoint, params=params)
            else:
                response = requests.get(self.evidence_validation_endpoint, params=params)
            
            response.raise_for_status()
            result = response.json()
            
            self.logger.info(
                f"Successfully fetched evidence validation via HTTP API for {month}/{year}"
            )
            
            return {
                'success': True,
                'data': result.get('data', {}),
                'meta': result.get('meta', {}),
                'errors': result.get('errors', []),
                'source': 'http_api'
            }
            
        except Exception as e:
            self.logger.error(f"Error calling Management Evidence Validation API: {e}", exc_info=True)
            return {
                'success': False,
                'data': {},
                'meta': {},
                'errors': [f'API request failed: {str(e)}']
            }
    
    def get_validated_budget_data(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None,
        department_id: Optional[int] = None,
        category_id: Optional[int] = None,
        session: Optional[requests.Session] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive validated budget data combining activity totals and evidence validation.
        
        This is a convenience method that calls both APIs and combines the results.
        
        Args:
            month: Target month (1-12) - default: last month
            year: Target year (YYYY) - default: current year
            department_id: Optional department filter
            category_id: Optional category filter
            session: Optional requests.Session for authenticated requests
        
        Returns:
            Dict with combined validated budget data:
            {
                'success': bool,
                'activity_totals': {...},
                'evidence_validation': {...},
                'validation_summary': {...},
                'errors': [...]
            }
        """
        try:
            # Get activity totals
            activity_result = self.get_activity_totals(
                month=month,
                year=year,
                department_id=department_id,
                category_id=category_id,
                include_evidence=True,
                include_validation=True,
                session=session
            )
            
            # Get evidence validation
            evidence_result = self.get_evidence_validation(
                month=month,
                year=year,
                department_id=department_id,
                category_id=category_id,
                session=session
            )
            
            # Combine results
            combined_errors = []
            if not activity_result['success']:
                combined_errors.extend(activity_result.get('errors', []))
            if not evidence_result['success']:
                combined_errors.extend(evidence_result.get('errors', []))
            
            # Build validation summary
            validation_summary = {
                'is_valid': activity_result['success'] and evidence_result['success'],
                'activity_data_available': activity_result['success'],
                'evidence_data_available': evidence_result['success'],
                'period': activity_result.get('data', {}).get('period') or evidence_result.get('data', {}).get('period'),
                'total_errors': len(combined_errors)
            }
            
            # Add validation status if available
            if activity_result['success']:
                validation_status = activity_result.get('data', {}).get('validation_status', {})
                if validation_status:
                    validation_summary['compliance_rate'] = validation_status.get('completion_rate')
                    validation_summary['is_validated'] = validation_status.get('is_validated')
                    validation_summary['evidence_coverage'] = validation_status.get('evidence_coverage')
            
            return {
                'success': activity_result['success'] and evidence_result['success'],
                'activity_totals': activity_result.get('data', {}),
                'evidence_validation': evidence_result.get('data', {}),
                'validation_summary': validation_summary,
                'errors': combined_errors
            }
            
        except Exception as e:
            self.logger.error(f"Error in get_validated_budget_data: {e}", exc_info=True)
            return {
                'success': False,
                'activity_totals': {},
                'evidence_validation': {},
                'validation_summary': {},
                'errors': [f'Unexpected error: {str(e)}']
            }

