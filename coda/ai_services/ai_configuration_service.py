"""
AI Configuration Service for managing AI model integrations
Provides centralized configuration management for AI services
"""

import json
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from .models import AIModelConfiguration, AIModelTypes, DiasporaAnalysisData

logger = logging.getLogger(__name__)

class AIConfigurationService:
    """Service for managing AI model configurations and health monitoring"""

    def __init__(self):
        self.cache_timeout = 300  # 5 minutes cache
        self.default_configs = self._get_default_configurations()
    
    def _get_default_configurations(self) -> List[Dict]:
        """Get default AI model configurations"""
        return [
            {
                'model_name': AIModelTypes.GPT4_PRIMARY,
                'is_active': True,
                'priority_order': 1,
                'api_endpoint': 'https://api.openai.com/v1/chat/completions',
                'api_key': getattr(settings, 'OPENAI_API_KEY', None),
                'max_tokens': 1000,
                'temperature': 0.3,
                'timeout_seconds': 30,
                'description': 'Primary GPT-4 model for high-quality analysis'
            },
            {
                'model_name': AIModelTypes.GPT35_FALLBACK,
                'is_active': True,
                'priority_order': 2,
                'api_endpoint': 'https://api.openai.com/v1/chat/completions',
                'api_key': getattr(settings, 'OPENAI_API_KEY', None),
                'max_tokens': 1000,
                'temperature': 0.3,
                'timeout_seconds': 30,
                'description': 'Fallback GPT-3.5 model for cost-effective analysis'
            },
            {
                'model_name': AIModelTypes.CLAUDE3_BACKUP,
                'is_active': False,  # Disabled by default
                'priority_order': 3,
                'api_endpoint': 'https://api.anthropic.com/v1/messages',
                'api_key': getattr(settings, 'CLAUDE_API_KEY', None),
                'max_tokens': 1000,
                'temperature': 0.3,
                'timeout_seconds': 30,
                'description': 'Claude-3 backup model for alternative analysis'
            },
            {
                'model_name': AIModelTypes.LOCAL_OFFLINE,
                'is_active': True,
                'priority_order': 4,
                'api_endpoint': None,
                'api_key': None,
                'max_tokens': 1000,
                'temperature': 0.3,
                'timeout_seconds': 5,
                'description': 'Local offline model for fallback scenarios'
            }
        ]
    
    def initialize_default_configurations(self) -> bool:
        """Initialize default AI configurations in database"""
        try:
            for config_data in self.default_configs:
                config, created = AIModelConfiguration.objects.get_or_create(
                    model_name=config_data['model_name'],
                    defaults=config_data
                )
                if created:
                    logger.info(f"Created default configuration for {config_data['model_name']}")
                else:
                    logger.info(f"Configuration for {config_data['model_name']} already exists")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing default configurations: {e}")
            return False
    
    def get_ai_service_status(self) -> Dict:
        """Get comprehensive AI service status"""
        cache_key = "ai_service_status"
        cached_status = cache.get(cache_key)
        if cached_status:
            return cached_status
        
        try:
            configs = AIModelConfiguration.objects.filter(is_active=True).order_by('priority_order')
            
            status = {
                'overall_status': 'healthy',
                'services': {},
                'total_configurations': configs.count(),
                'active_configurations': configs.filter(is_active=True).count(),
                'last_checked': timezone.now().isoformat(),
                'performance_metrics': self._get_performance_metrics()
            }
            
            # Check each AI service
            for config in configs:
                service_status = self._check_service_health(config)
                status['services'][config.model_name] = service_status
            
            # Determine overall status
            available_services = sum(1 for service in status['services'].values() 
                                   if service['status'] == 'available')
            total_services = len(status['services'])
            
            if available_services == 0:
                status['overall_status'] = 'unhealthy'
            elif available_services < total_services:
                status['overall_status'] = 'degraded'
            
            # Cache the status
            cache.set(cache_key, status, self.cache_timeout)
            
            return status
                
        except Exception as e:
            logger.error(f"Error getting AI service status: {e}")
            return {
                'overall_status': 'error',
                'error': str(e),
                'last_checked': timezone.now().isoformat()
            }
    
    def _check_service_health(self, config: AIModelConfiguration) -> Dict:
        """Check health of individual AI service"""
        try:
            if config.model_name == AIModelTypes.LOCAL_OFFLINE:
                return {
                    'status': 'available',
                    'response_time': 0.1,
                    'last_checked': timezone.now().isoformat(),
                    'description': config.description or 'Local offline model'
                }
            
            # For real AI services, check if API key is configured
            if not config.api_key:
                return {
                    'status': 'unavailable',
                    'reason': 'API key not configured',
                    'last_checked': timezone.now().isoformat(),
                    'description': config.description or f'{config.model_name} model'
                }
            
            # Check recent usage
            recent_usage = DiasporaAnalysisData.objects.filter(
                model_used=config.model_name,
                created_at__gte=timezone.now() - timezone.timedelta(hours=1)
            ).count()
            
            return {
                'status': 'available',
                'api_key_configured': True,
                'recent_usage': recent_usage,
                'last_checked': timezone.now().isoformat(),
                'description': config.description or f'{config.model_name} model'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'reason': str(e),
                'last_checked': timezone.now().isoformat(),
                'description': config.description or f'{config.model_name} model'
            }
    
    def _get_performance_metrics(self) -> Dict:
        """Get AI performance metrics"""
        try:
            # Get metrics from last 24 hours
            last_24h = timezone.now() - timezone.timedelta(hours=24)
            
            recent_analyses = DiasporaAnalysisData.objects.filter(
                created_at__gte=last_24h,
                is_active=True
            )
            
            total_analyses = recent_analyses.count()
            real_ai_analyses = recent_analyses.filter(is_real_ai=True).count()
            fallback_analyses = recent_analyses.filter(is_real_ai=False).count()
            
            avg_confidence = recent_analyses.aggregate(
                avg_confidence=models.Avg('confidence_score')
            )['avg_confidence'] or 0
            
            avg_processing_time = recent_analyses.aggregate(
                avg_time=models.Avg('processing_time')
            )['avg_time'] or 0
            
            return {
                'total_analyses_24h': total_analyses,
                'real_ai_analyses_24h': real_ai_analyses,
                'fallback_analyses_24h': fallback_analyses,
                'real_ai_percentage': round((real_ai_analyses / total_analyses * 100), 2) if total_analyses > 0 else 0,
                'avg_confidence_score': round(avg_confidence, 3),
                'avg_processing_time': round(avg_processing_time, 2),
                'success_rate': round((total_analyses - fallback_analyses) / total_analyses * 100, 2) if total_analyses > 0 else 0
            }
                
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {
                'error': str(e),
                'total_analyses_24h': 0,
                'real_ai_analyses_24h': 0,
                'fallback_analyses_24h': 0,
                'real_ai_percentage': 0,
                'avg_confidence_score': 0,
                'avg_processing_time': 0,
                'success_rate': 0
            }
    
    def get_migration_plan(self) -> Dict:
        """Get AI service migration plan for scaling"""
        try:
            current_status = self.get_ai_service_status()
            
            migration_plan = {
                'current_capacity': self._assess_current_capacity(),
                'recommended_upgrades': self._get_recommended_upgrades(),
                'scaling_strategy': self._get_scaling_strategy(),
                'cost_analysis': self._get_cost_analysis(),
                'implementation_timeline': self._get_implementation_timeline()
            }
            
            return migration_plan
            
        except Exception as e:
            logger.error(f"Error getting migration plan: {e}")
            return {
                'error': str(e),
                'current_capacity': 'Unknown',
                'recommended_upgrades': [],
                'scaling_strategy': 'Manual assessment required',
                'cost_analysis': 'Unable to calculate',
                'implementation_timeline': 'TBD'
            }
    
    def _assess_current_capacity(self) -> Dict:
        """Assess current AI service capacity"""
        try:
            # Get usage statistics
            total_analyses = DiasporaAnalysisData.objects.filter(is_active=True).count()
            daily_analyses = DiasporaAnalysisData.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=1),
                is_active=True
            ).count()
            
            # Estimate capacity based on usage patterns
            if daily_analyses < 100:
                capacity_level = 'Low'
                capacity_description = 'Suitable for demo and small-scale usage'
            elif daily_analyses < 500:
                capacity_level = 'Medium'
                capacity_description = 'Suitable for moderate usage and testing'
            elif daily_analyses < 1000:
                capacity_level = 'High'
                capacity_description = 'Suitable for production usage'
            else:
                capacity_level = 'Enterprise'
                capacity_description = 'Requires enterprise-grade infrastructure'
            
            return {
                'level': capacity_level,
                'description': capacity_description,
                'daily_analyses': daily_analyses,
                'total_analyses': total_analyses,
                'estimated_monthly_capacity': daily_analyses * 30
            }
                
        except Exception as e:
            logger.error(f"Error assessing capacity: {e}")
            return {
                'level': 'Unknown',
                'description': 'Unable to assess capacity',
                'daily_analyses': 0,
                'total_analyses': 0,
                'estimated_monthly_capacity': 0
            }
    
    def _get_recommended_upgrades(self) -> List[Dict]:
        """Get recommended AI service upgrades"""
        recommendations = []
        
        try:
            current_status = self.get_ai_service_status()
            
            # Check if OpenAI is configured
            openai_status = current_status['services'].get(AIModelTypes.GPT4_PRIMARY, {})
            if openai_status.get('status') != 'available':
                recommendations.append({
                    'service': 'OpenAI GPT-4',
                    'priority': 'High',
                    'description': 'Configure OpenAI API key for primary AI analysis',
                    'benefit': 'High-quality AI analysis with real-time processing',
                    'effort': 'Low',
                    'cost_impact': 'Medium'
                })
            
            # Check if Claude is available
            claude_status = current_status['services'].get(AIModelTypes.CLAUDE3_BACKUP, {})
            if claude_status.get('status') != 'available':
                recommendations.append({
                    'service': 'Claude-3 Backup',
                    'priority': 'Medium',
                    'description': 'Add Claude-3 as backup AI service',
                    'benefit': 'Improved reliability and alternative analysis approach',
                    'effort': 'Medium',
                    'cost_impact': 'Low'
                })
            
            # Check performance metrics
            performance = current_status.get('performance_metrics', {})
            if performance.get('avg_processing_time', 0) > 5.0:
                recommendations.append({
                    'service': 'Performance Optimization',
                    'priority': 'Medium',
                    'description': 'Optimize AI processing times',
                    'benefit': 'Faster response times and better user experience',
                    'effort': 'High',
                    'cost_impact': 'Low'
                })
            
            # Check fallback usage
            if performance.get('real_ai_percentage', 100) < 80:
                recommendations.append({
                    'service': 'AI Service Reliability',
                    'priority': 'High',
                    'description': 'Improve AI service reliability to reduce fallback usage',
                    'benefit': 'More consistent AI analysis quality',
                    'effort': 'Medium',
                    'cost_impact': 'Medium'
                })
            
        except Exception as e:
            logger.error(f"Error getting recommended upgrades: {e}")
            recommendations.append({
                'service': 'System Assessment',
                'priority': 'High',
                'description': 'Complete system assessment required',
                'benefit': 'Identify specific improvement areas',
                'effort': 'High',
                'cost_impact': 'Unknown'
            })
        
        return recommendations
    
    def _get_scaling_strategy(self) -> Dict:
        """Get AI service scaling strategy"""
        return {
            'phase_1': {
                'name': 'Foundation',
                'description': 'Establish reliable AI service infrastructure',
                'duration': '1-2 weeks',
                'components': [
                    'Configure primary AI service (OpenAI)',
                    'Implement robust error handling',
                    'Set up monitoring and alerting'
                ]
            },
            'phase_2': {
                'name': 'Enhancement',
                'description': 'Add backup services and optimize performance',
                'duration': '2-3 weeks',
                'components': [
                    'Add Claude-3 backup service',
                    'Implement intelligent fallback strategies',
                    'Optimize processing times'
                ]
            },
            'phase_3': {
                'name': 'Scale',
                'description': 'Prepare for high-volume usage',
                'duration': '3-4 weeks',
                'components': [
                    'Implement load balancing',
                    'Add caching strategies',
                    'Set up auto-scaling'
                ]
            }
        }
    
    def _get_cost_analysis(self) -> Dict:
        """Get AI service cost analysis"""
        return {
            'current_costs': {
                'openai_gpt4': '$0.03 per 1K tokens (input) + $0.06 per 1K tokens (output)',
                'openai_gpt35': '$0.0015 per 1K tokens (input) + $0.002 per 1K tokens (output)',
                'claude3': '$0.003 per 1K tokens (input) + $0.015 per 1K tokens (output)',
                'fallback': '$0 (local processing)'
            },
            'estimated_monthly_costs': {
                'low_usage': '$50-100',
                'medium_usage': '$200-500',
                'high_usage': '$500-1500',
                'enterprise': '$1500+'
            },
            'cost_optimization_tips': [
                'Use GPT-3.5 for simple analyses to reduce costs',
                'Implement intelligent caching to avoid duplicate requests',
                'Optimize prompts to reduce token usage',
                'Use fallback data for demo purposes'
            ]
        }
    
    def _get_implementation_timeline(self) -> Dict:
        """Get implementation timeline for AI improvements"""
        return {
            'week_1': [
                'Configure OpenAI API keys',
                'Test primary AI service integration',
                'Implement basic error handling'
            ],
            'week_2': [
                'Add Claude-3 backup service',
                'Implement intelligent fallback strategies',
                'Set up performance monitoring'
            ],
            'week_3': [
                'Optimize AI processing times',
                'Implement caching strategies',
                'Add comprehensive logging'
            ],
            'week_4': [
                'Performance testing and optimization',
                'Documentation and training',
                'Production deployment'
            ]
        }
    
    def update_configuration(self, model_name: str, config_data: Dict) -> bool:
        """Update AI model configuration"""
        try:
            config = AIModelConfiguration.objects.get(model_name=model_name)
            
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            config.updated_at = timezone.now()
            config.save()
            
            # Clear cache
            cache.delete("ai_service_status")
            
            logger.info(f"Updated configuration for {model_name}")
            return True
            
        except AIModelConfiguration.DoesNotExist:
            logger.error(f"Configuration for {model_name} not found")
            return False
        except Exception as e:
            logger.error(f"Error updating configuration for {model_name}: {e}")
            return False
    
    def get_configuration_summary(self) -> Dict:
        """Get summary of all AI configurations"""
        try:
            configs = AIModelConfiguration.objects.all().order_by('priority_order')
            
            summary = {
                'total_configurations': configs.count(),
                'active_configurations': configs.filter(is_active=True).count(),
                'configurations': []
            }
            
            for config in configs:
                summary['configurations'].append({
                    'model_name': config.model_name,
                    'is_active': config.is_active,
                    'priority_order': config.priority_order,
                    'api_key_configured': bool(config.api_key),
                    'max_tokens': config.max_tokens,
                    'temperature': config.temperature,
                    'timeout_seconds': config.timeout_seconds,
                    'created_at': config.created_at.isoformat(),
                    'updated_at': config.updated_at.isoformat()
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting configuration summary: {e}")
        return {
                'error': str(e),
                'total_configurations': 0,
                'active_configurations': 0,
                'configurations': []
            }