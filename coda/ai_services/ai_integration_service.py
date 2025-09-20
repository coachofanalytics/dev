"""
Real AI Integration Service with Fallback Functionality
This service provides real AI integration with OpenAI, Claude, and other providers
with automatic fallback to realistic dummy data when AI services are unavailable.
"""

import os
import json
import time
import logging
import requests
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from .models import AIModelConfiguration, AIModelTypes

logger = logging.getLogger(__name__)

class RealAIService:
    """Real AI service integration with multiple providers and fallback"""
    
    def __init__(self):
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.claude_api_key = getattr(settings, 'CLAUDE_API_KEY', None)
        self.anthropic_api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        self.ai_configs = self._load_ai_configurations()
        
    def _load_ai_configurations(self) -> List[Dict]:
        """Load AI model configurations from database"""
        try:
            configs = AIModelConfiguration.objects.filter(is_active=True).order_by('priority_order')
            return [
                {
                    'model_name': config.model_name,
                    'api_endpoint': config.api_endpoint,
                    'api_key': config.api_key,
                    'max_tokens': config.max_tokens,
                    'temperature': config.temperature,
                    'timeout_seconds': config.timeout_seconds,
                    'priority_order': config.priority_order
                }
                for config in configs
            ]
        except Exception as e:
            logger.error(f"Error loading AI configurations: {e}")
            return self._get_default_configs()
    
    def _get_default_configs(self) -> List[Dict]:
        """Default AI configurations when database is unavailable"""
        return [
            {
                'model_name': AIModelTypes.GPT4_PRIMARY,
                'api_endpoint': 'https://api.openai.com/v1/chat/completions',
                'api_key': self.openai_api_key,
                'max_tokens': 1000,
                'temperature': 0.3,
                'timeout_seconds': 30,
                'priority_order': 1
            },
            {
                'model_name': AIModelTypes.GPT35_FALLBACK,
                'api_endpoint': 'https://api.openai.com/v1/chat/completions',
                'api_key': self.openai_api_key,
                'max_tokens': 1000,
                'temperature': 0.3,
                'timeout_seconds': 30,
                'priority_order': 2
            }
        ]
    
    def get_prediction(self, analysis_type: str, input_data: Dict, session_id: str) -> Dict:
        """
        Get AI prediction with automatic fallback
        Try: Real AI -> Fallback to realistic dummy data
        """
        start_time = time.time()
        
        try:
            # Try real AI first
            prediction = self._try_real_ai(analysis_type, input_data)
            if prediction:
                prediction.update({
                    'model_used': prediction.get('model_used', AIModelTypes.GPT4_PRIMARY),
                    'processing_time': time.time() - start_time,
                    'fallback_used': False,
                    'confidence_score': prediction.get('confidence_score', 0.85),
                    'is_real_ai': True
                })
                logger.info(f"Real AI prediction successful for {analysis_type}")
                return prediction
        except Exception as e:
            logger.warning(f"Real AI failed for {analysis_type}: {e}")
        
        # Fallback to realistic dummy data
        logger.info(f"Using fallback data for {analysis_type}")
        prediction = self._get_fallback_prediction(analysis_type, input_data)
        prediction.update({
            'model_used': AIModelTypes.LOCAL_OFFLINE,
            'processing_time': time.time() - start_time,
            'fallback_used': True,
            'confidence_score': 0.75,  # Lower confidence for fallback
            'is_real_ai': False
        })
        
        return prediction
    
    def _try_real_ai(self, analysis_type: str, input_data: Dict) -> Optional[Dict]:
        """Try to get real AI prediction from available providers"""
        
        for config in self.ai_configs:
            try:
                if config['model_name'] == AIModelTypes.GPT4_PRIMARY:
                    return self._call_openai_gpt4(config, analysis_type, input_data)
                elif config['model_name'] == AIModelTypes.GPT35_FALLBACK:
                    return self._call_openai_gpt35(config, analysis_type, input_data)
                elif config['model_name'] == AIModelTypes.CLAUDE3_BACKUP:
                    return self._call_claude3(config, analysis_type, input_data)
            except Exception as e:
                logger.warning(f"AI provider {config['model_name']} failed: {e}")
                continue
        
        return None
    
    def _call_openai_gpt4(self, config: Dict, analysis_type: str, input_data: Dict) -> Dict:
        """Call OpenAI GPT-4 API"""
        if not config['api_key']:
            raise ValueError("OpenAI API key not configured")
        
        prompt = self._build_analysis_prompt(analysis_type, input_data)
        
        headers = {
            'Authorization': f'Bearer {config["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-4',
            'messages': [
                {
                    'role': 'system',
                    'content': self._get_system_prompt(analysis_type)
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': config['max_tokens'],
            'temperature': config['temperature']
        }
        
        response = requests.post(
            config['api_endpoint'],
            headers=headers,
            json=payload,
            timeout=config['timeout_seconds']
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            return self._parse_ai_response(content, analysis_type, AIModelTypes.GPT4_PRIMARY)
        else:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
    
    def _call_openai_gpt35(self, config: Dict, analysis_type: str, input_data: Dict) -> Dict:
        """Call OpenAI GPT-3.5 API"""
        if not config['api_key']:
            raise ValueError("OpenAI API key not configured")
        
        prompt = self._build_analysis_prompt(analysis_type, input_data)
        
        headers = {
            'Authorization': f'Bearer {config["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {
                    'role': 'system',
                    'content': self._get_system_prompt(analysis_type)
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': config['max_tokens'],
            'temperature': config['temperature']
        }
        
        response = requests.post(
            config['api_endpoint'],
            headers=headers,
            json=payload,
            timeout=config['timeout_seconds']
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            return self._parse_ai_response(content, analysis_type, AIModelTypes.GPT35_FALLBACK)
        else:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
    
    def _call_claude3(self, config: Dict, analysis_type: str, input_data: Dict) -> Dict:
        """Call Claude-3 API"""
        if not config['api_key']:
            raise ValueError("Claude API key not configured")
        
        prompt = self._build_analysis_prompt(analysis_type, input_data)
        
        headers = {
            'x-api-key': config['api_key'],
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': 'claude-3-sonnet-20240229',
            'max_tokens': config['max_tokens'],
            'temperature': config['temperature'],
            'system': self._get_system_prompt(analysis_type),
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        response = requests.post(
            config['api_endpoint'],
            headers=headers,
            json=payload,
            timeout=config['timeout_seconds']
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['content'][0]['text']
            return self._parse_ai_response(content, analysis_type, AIModelTypes.CLAUDE3_BACKUP)
        else:
            raise Exception(f"Claude API error: {response.status_code} - {response.text}")
    
    def _build_analysis_prompt(self, analysis_type: str, input_data: Dict) -> str:
        """Build analysis prompt based on type and input data"""
        
        prompts = {
            'remittance_analysis': f"""
            Analyze this remittance data for a Kenyan diaspora member:
            Amount: ${input_data.get('amount', 'N/A')}
            Frequency: {input_data.get('frequency', 'N/A')}
            Destination: {input_data.get('destination', 'N/A')}
            Purpose: {input_data.get('purpose', 'N/A')}
            Experience: {input_data.get('experience_years', 'N/A')} years
            Method: {input_data.get('method', 'N/A')}
            
            Provide a comprehensive analysis including:
            1. Assessment score (1-10)
            2. Key recommendations
            3. Risk factors
            4. Next steps
            """,
            
            'trade_facilitation': f"""
            Analyze this trade facilitation data:
            Business Type: {input_data.get('business_type', 'N/A')}
            Product Categories: {input_data.get('product_categories', 'N/A')}
            Annual Volume: ${input_data.get('annual_volume', 'N/A')}
            Target Markets: {input_data.get('target_markets', 'N/A')}
            Business Years: {input_data.get('business_years', 'N/A')}
            Challenges: {input_data.get('challenges', 'N/A')}
            
            Provide analysis for trade facilitation opportunities.
            """,
            
            'investment_opportunities': f"""
            Analyze investment opportunities for:
            Investment Amount: ${input_data.get('investment_amount', 'N/A')}
            Risk Tolerance: {input_data.get('risk_tolerance', 'N/A')}
            Investment Horizon: {input_data.get('investment_horizon', 'N/A')}
            Sector Interest: {input_data.get('sector_interest', 'N/A')}
            Location Preference: {input_data.get('location_preference', 'N/A')}
            
            Provide investment analysis and recommendations.
            """,
            
            'education_pathways': f"""
            Analyze education pathways for:
            Education Level: {input_data.get('education_level', 'N/A')}
            Field Interest: {input_data.get('field_interest', 'N/A')}
            Budget: ${input_data.get('budget', 'N/A')}
            Location Preference: {input_data.get('location_preference', 'N/A')}
            Time Commitment: {input_data.get('time_commitment', 'N/A')}
            
            Provide education pathway recommendations.
            """,
            
            'healthcare_access': f"""
            Analyze healthcare access for:
            Age Group: {input_data.get('age_group', 'N/A')}
            Health Conditions: {input_data.get('health_conditions', 'N/A')}
            Insurance Status: {input_data.get('insurance_status', 'N/A')}
            Location: {input_data.get('location', 'N/A')}
            Budget: ${input_data.get('budget', 'N/A')}
            
            Provide healthcare access analysis and recommendations.
            """
        }
        
        return prompts.get(analysis_type, f"Analyze this data: {input_data}")
    
    def _get_system_prompt(self, analysis_type: str) -> str:
        """Get system prompt for AI analysis"""
        return f"""
        You are an expert AI analyst specializing in {analysis_type.replace('_', ' ')} for the Kenyan diaspora.
        Provide detailed, actionable insights with:
        - Assessment scores (1-10 scale)
        - Specific recommendations
        - Risk factors and mitigation strategies
        - Clear next steps
        
        Focus on practical, implementable advice for diaspora members.
        Be concise but comprehensive in your analysis.
        """
    
    def _parse_ai_response(self, content: str, analysis_type: str, model_used: str) -> Dict:
        """Parse AI response into structured format"""
        try:
            # Try to extract structured data from AI response
            # This is a simplified parser - in production, you'd want more sophisticated parsing
            
            lines = content.split('\n')
            assessment_score = 7.0  # Default
            recommendations = []
            risk_factors = []
            next_steps = []
            
            current_section = None
            for line in lines:
                line = line.strip()
                if 'assessment' in line.lower() or 'score' in line.lower():
                    # Extract score
                    import re
                    score_match = re.search(r'(\d+(?:\.\d+)?)', line)
                    if score_match:
                        assessment_score = float(score_match.group(1))
                elif 'recommendation' in line.lower():
                    current_section = 'recommendations'
                elif 'risk' in line.lower():
                    current_section = 'risk_factors'
                elif 'next' in line.lower() or 'step' in line.lower():
                    current_section = 'next_steps'
                elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    item = line.lstrip('-•* ').strip()
                    if current_section == 'recommendations':
                        recommendations.append(item)
                    elif current_section == 'risk_factors':
                        risk_factors.append(item)
                    elif current_section == 'next_steps':
                        next_steps.append(item)
            
            # Ensure we have some content
            if not recommendations:
                recommendations = ["Continue current approach", "Monitor progress regularly"]
            if not risk_factors:
                risk_factors = ["Market volatility", "Regulatory changes"]
            if not next_steps:
                next_steps = ["Review analysis", "Implement recommendations"]
            
            return {
                'assessment_score': min(10.0, max(1.0, assessment_score)),
                'recommendations': recommendations[:5],  # Limit to 5 items
                'risk_factors': risk_factors[:4],  # Limit to 4 items
                'next_steps': next_steps[:4],  # Limit to 4 items
                'model_used': model_used,
                'raw_response': content
            }
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            # Return fallback structure
            return {
                'assessment_score': 7.0,
                'recommendations': ["Review the analysis", "Consider professional consultation"],
                'risk_factors': ["Market volatility", "Regulatory changes"],
                'next_steps': ["Implement recommendations", "Monitor progress"],
                'model_used': model_used,
                'raw_response': content
            }
    
    def _get_fallback_prediction(self, analysis_type: str, input_data: Dict) -> Dict:
        """Get realistic fallback prediction when AI is unavailable"""
        from .ai_services import SimpleAIResponseManager
        
        # Use existing fallback service
        fallback_service = SimpleAIResponseManager()
        return fallback_service.get_prediction(analysis_type, input_data, "fallback_session")


class AIHealthChecker:
    """Check health of AI services"""
    
    @staticmethod
    def check_ai_health() -> Dict:
        """Check health of all AI services"""
        health_status = {
            'overall_status': 'healthy',
            'services': {},
            'last_checked': timezone.now().isoformat()
        }
        
        try:
            ai_service = RealAIService()
            
            # Check OpenAI
            try:
                if ai_service.openai_api_key:
                    health_status['services']['openai'] = {
                        'status': 'available',
                        'models': ['gpt-4', 'gpt-3.5-turbo']
                    }
                else:
                    health_status['services']['openai'] = {
                        'status': 'unavailable',
                        'reason': 'API key not configured'
                    }
            except Exception as e:
                health_status['services']['openai'] = {
                    'status': 'error',
                    'reason': str(e)
                }
            
            # Check Claude
            try:
                if ai_service.claude_api_key or ai_service.anthropic_api_key:
                    health_status['services']['claude'] = {
                        'status': 'available',
                        'models': ['claude-3-sonnet']
                    }
                else:
                    health_status['services']['claude'] = {
                        'status': 'unavailable',
                        'reason': 'API key not configured'
                    }
            except Exception as e:
                health_status['services']['claude'] = {
                    'status': 'error',
                    'reason': str(e)
                }
            
            # Check fallback service
            health_status['services']['fallback'] = {
                'status': 'available',
                'models': ['local_offline']
            }
            
            # Determine overall status
            available_services = sum(1 for service in health_status['services'].values() 
                                   if service['status'] == 'available')
            if available_services == 0:
                health_status['overall_status'] = 'unhealthy'
            elif available_services < len(health_status['services']):
                health_status['overall_status'] = 'degraded'
            
        except Exception as e:
            health_status['overall_status'] = 'error'
            health_status['error'] = str(e)
        
        return health_status


