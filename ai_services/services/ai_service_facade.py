"""
AI Service Facade

Centralized AI service that consolidates all AI functionality across the CODA application.
This facade provides a unified interface for AI operations, eliminating duplicate AI implementations.

Replaces duplicate AI functions in:
- main/utils.py
- main/views.py
- main/utilities/ai_utils.py
"""

import logging
import os
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.cache import cache
from .ai_analytics_service import AIAnalyticsService
from ..ai_integration_service import RealAIService
from ..ai_configuration_service import AIConfigurationService
from ..ai_services import SimpleAIResponseManager

logger = logging.getLogger(__name__)


class AIServiceFacade:
    """
    Centralized AI service facade that provides a unified interface for all AI operations.
    
    This service consolidates AI functionality from multiple implementations into a single,
    robust service that handles fallbacks, caching, and error recovery.
    """
    
    def __init__(self):
        self.logger = logger
        self.analytics_service = AIAnalyticsService()
        self.real_ai_service = RealAIService()
        self.config_service = AIConfigurationService()
        self.response_manager = SimpleAIResponseManager()
        self.cache_timeout = 3600  # 1 hour cache
    
    def generate_response(self, user_message: str, context: Optional[Dict] = None, 
                         general_use: bool = False) -> Dict[str, Any]:
        """
        Generate AI response for user message.
        
        Replaces: main/views.py get_respos()
        
        Args:
            user_message: User's message/query
            context: Optional context for the message
            general_use: Whether this is for general use or specific analysis
            
        Returns:
            Dict with AI response and metadata
        """
        try:
            if not user_message:
                return {'response': 'Invalid user message', 'error': 'Empty message'}
            
            # Try database-specific response first if not general use
            if not general_use:
                database_response = self._generate_database_response(user_message)
                if database_response:
                    # Use AI to enhance database response
                    enhanced_response = self._enhance_with_ai(database_response, user_message)
                    if enhanced_response:
                        return {
                            'response': enhanced_response,
                            'source': 'database_enhanced',
                            'cache_hit': False
                        }
            
            # Fallback to general chatbot response
            chatbot_response = self.generate_chatbot_response(user_message, context)
            if chatbot_response:
                return {
                    'response': chatbot_response,
                    'source': 'chatbot',
                    'cache_hit': False
                }
            
            # Final fallback to DSU (Diaspora Support Unit)
            dsu_response = self._get_dsu_response(user_message)
            if dsu_response:
                return {
                    'response': dsu_response,
                    'source': 'dsu',
                    'cache_hit': False
                }
            
            # Default response
            return {
                'response': "Oops! It seems I haven't learned that one yet, but don't worry. Our team will get back to you shortly with the information you need. Thanks for your patience!",
                'source': 'default',
                'cache_hit': False
            }
            
        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            return {
                'response': 'I apologize, but I encountered an error processing your request. Please try again.',
                'error': str(e),
                'source': 'error'
            }
    
    def generate_openai_user_message(self, openai_context: str, 
                                   requirement: Optional[str] = None) -> str:
        """
        Generate OpenAI user message.
        
        Replaces: main/utils.py openai_user_message()
        
        Args:
            openai_context: Context for the message
            requirement: Optional requirement
            
        Returns:
            Formatted user message
        """
        try:
            if not openai_context:
                return "Please provide more context for your request."
            
            message = f"Context: {openai_context}"
            
            if requirement:
                message += f"\nRequirement: {requirement}"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error generating OpenAI user message: {e}")
            return "Error generating message"
    
    def generate_chatbot_response(self, user_message: str, 
                                user_message_dict: Optional[Dict] = None) -> Optional[str]:
        """
        Generate chatbot response.
        
        Replaces: main/utils.py generate_chatbot_response()
        
        Args:
            user_message: User's message
            user_message_dict: Optional message dictionary
            
        Returns:
            Chatbot response or None
        """
        try:
            # Check cache first
            cache_key = f"chatbot_response_{hash(user_message)}"
            cached_response = cache.get(cache_key)
            if cached_response:
                self.logger.info("Using cached chatbot response")
                return cached_response
            
            # Use AI services to generate response
            response_data = self.real_ai_service.get_ai_response(
                user_message, 
                context=user_message_dict
            )
            
            if response_data and response_data.get('success'):
                response = response_data.get('response', '')
                
                # Cache successful response
                cache.set(cache_key, response, self.cache_timeout)
                
                return response
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating chatbot response: {e}")
            return None
    
    def parse_user_query(self, user_query: str) -> List[str]:
        """
        Parse user query to extract keywords.
        
        Replaces: main/utils.py parse_user_query()
        
        Args:
            user_query: User's query string
            
        Returns:
            List of extracted keywords
        """
        try:
            if not user_query:
                return []
            
            # Use AI to extract keywords
            keywords = self.real_ai_service.extract_keywords(user_query)
            
            if keywords:
                return keywords
            
            # Fallback to simple keyword extraction
            import re
            words = re.findall(r'\b\w+\b', user_query.lower())
            
            # Filter out common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
            
            keywords = [word for word in words if word not in stop_words and len(word) > 2]
            
            return keywords[:10]  # Limit to 10 keywords
            
        except Exception as e:
            self.logger.error(f"Error parsing user query: {e}")
            return []
    
    def _generate_database_response(self, user_message: str) -> Optional[str]:
        """
        Generate database-specific response.
        
        This method would integrate with your existing database query system.
        """
        try:
            # This would integrate with your existing database response system
            # For now, return None to indicate no database response available
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating database response: {e}")
            return None
    
    def _enhance_with_ai(self, database_response: str, user_message: str) -> Optional[str]:
        """
        Enhance database response with AI.
        
        Args:
            database_response: Raw database response
            user_message: Original user message
            
        Returns:
            AI-enhanced response
        """
        try:
            # Use OpenAI to enhance the database response
            openai_api_key = os.environ.get('OPENAI_API_KEY')
            if not openai_api_key:
                return database_response
            
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage
            
            llm = ChatOpenAI(openai_api_key=openai_api_key)
            messages = [HumanMessage(content=str(database_response))]
            response_llm = llm.predict_messages(messages)
            
            return response_llm.content
            
        except Exception as e:
            self.logger.error(f"Error enhancing with AI: {e}")
            return database_response
    
    def _get_dsu_response(self, user_message: str) -> Optional[str]:
        """
        Get DSU (Diaspora Support Unit) response.
        
        Args:
            user_message: User's message
            
        Returns:
            DSU response if available
        """
        try:
            # This would integrate with your existing DSU system
            # For now, return None to indicate no DSU response available
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting DSU response: {e}")
            return None
    
    def get_ai_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive AI services health status.
        
        Returns:
            Dict with AI services health information
        """
        try:
            return self.config_service.get_ai_service_status()
            
        except Exception as e:
            self.logger.error(f"Error getting AI health status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'services': {}
            }
    
    def get_ai_configuration(self) -> Dict[str, Any]:
        """
        Get AI configuration information.
        
        Returns:
            Dict with AI configuration
        """
        try:
            return self.config_service.get_configuration_summary()
            
        except Exception as e:
            self.logger.error(f"Error getting AI configuration: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


# Global instance for easy access
ai_service_facade = AIServiceFacade()
