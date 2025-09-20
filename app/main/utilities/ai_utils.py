"""
AI Utilities

Handles all AI-related operations including:
- OpenAI API interactions
- Chatbot response generation
- Database query processing
- WCAG compliance analysis

This utility encapsulates AI-related functionality previously scattered across main/utils.py
"""

import logging
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AIUtils:
    """
    Utility class for AI-related operations.
    
    Provides methods for AI interactions, chatbot responses, and analysis.
    """
    
    def __init__(self):
        self.logger = logger
    
    def openai_user_message(
        self, 
        openai_context: str, 
        requirement: Optional[str] = None
    ) -> str:
        """
        Generate OpenAI user message.
        
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
    
    def generate_chatbot_response(
        self, 
        user_message: str, 
        user_message_dict: Optional[Dict] = None
    ) -> str:
        """
        Generate chatbot response.
        
        Args:
            user_message: User's message
            user_message_dict: Optional user message dictionary
            
        Returns:
            Chatbot response
        """
        try:
            if not user_message:
                return "I didn't receive your message. Please try again."
            
            # Simple response generation (placeholder for actual AI)
            responses = [
                "I understand your request. Let me help you with that.",
                "That's an interesting question. Here's what I can tell you.",
                "I can assist you with that. Let me provide some information.",
                "Thank you for your message. I'll do my best to help.",
                "I've received your request and I'm processing it now."
            ]
            
            # Simple keyword-based response selection
            if any(word in user_message.lower() for word in ['help', 'assist', 'support']):
                return "I'm here to help! What specific assistance do you need?"
            elif any(word in user_message.lower() for word in ['thank', 'thanks']):
                return "You're welcome! Is there anything else I can help you with?"
            elif '?' in user_message:
                return "That's a great question! Let me provide you with some information."
            else:
                import random
                return random.choice(responses)
                
        except Exception as e:
            self.logger.error(f"Error generating chatbot response: {e}")
            return "I'm sorry, I encountered an error processing your message."
    
    def generate_database_response(
        self, 
        user_message: str, 
        app: str = 'investing', 
        table: str = 'investments'
    ) -> str:
        """
        Generate database response.
        
        Args:
            user_message: User's message
            app: Application name
            table: Table name
            
        Returns:
            Database response
        """
        try:
            if not user_message:
                return "Please provide a query or request."
            
            # Placeholder for actual database query processing
            self.logger.info(f"Processing database query for {app}.{table}")
            
            return f"I'm processing your request for {app} data in the {table} table. This is a placeholder response."
            
        except Exception as e:
            self.logger.error(f"Error generating database response: {e}")
            return "Error processing database request"
    
    def analyze_website_for_wcag_compliance(
        self, 
        uploaded_file_content: str
    ) -> Dict[str, Any]:
        """
        Analyze website for WCAG compliance.
        
        Args:
            uploaded_file_content: Website content to analyze
            
        Returns:
            Dict with compliance analysis
        """
        try:
            if not uploaded_file_content:
                return {
                    'success': False,
                    'error': 'No content provided for analysis'
                }
            
            # Placeholder for actual WCAG analysis
            self.logger.info("Analyzing website for WCAG compliance")
            
            # Simple analysis based on content
            content_lower = uploaded_file_content.lower()
            
            issues = []
            recommendations = []
            
            # Check for common accessibility issues
            if 'alt=' not in content_lower:
                issues.append("Missing alt attributes on images")
                recommendations.append("Add alt attributes to all images")
            
            if 'aria-label' not in content_lower:
                issues.append("Missing ARIA labels")
                recommendations.append("Add ARIA labels for better accessibility")
            
            if 'title=' not in content_lower:
                issues.append("Missing title attributes")
                recommendations.append("Add title attributes to important elements")
            
            return {
                'success': True,
                'analysis_complete': True,
                'issues_found': len(issues),
                'issues': issues,
                'recommendations': recommendations,
                'compliance_score': max(0, 100 - len(issues) * 10),
                'content_length': len(uploaded_file_content)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing WCAG compliance: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_openai_api_exception(self, responses: Any) -> Dict[str, Any]:
        """
        Handle OpenAI API exceptions.
        
        Args:
            responses: API responses
            
        Returns:
            Dict with error handling information
        """
        try:
            if not responses:
                return {
                    'success': False,
                    'error': 'No response received from API'
                }
            
            # Placeholder for actual exception handling
            self.logger.info("Handling OpenAI API exception")
            
            return {
                'success': True,
                'error_handled': True,
                'response': str(responses),
                'error_type': type(responses).__name__
            }
            
        except Exception as e:
            self.logger.error(f"Error handling OpenAI API exception: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def parse_json_response(self, responses: Any) -> Dict[str, Any]:
        """
        Parse JSON response.
        
        Args:
            responses: Response to parse
            
        Returns:
            Dict with parsed response
        """
        try:
            if not responses:
                return {
                    'success': False,
                    'error': 'No response to parse'
                }
            
            # Try to parse as JSON
            if isinstance(responses, str):
                try:
                    parsed = json.loads(responses)
                except json.JSONDecodeError:
                    parsed = {'raw_response': responses}
            else:
                parsed = responses
            
            return {
                'success': True,
                'parsed_data': parsed,
                'is_json': isinstance(parsed, (dict, list))
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing JSON response: {e}")
            return {
                'success': False,
                'error': str(e),
                'raw_response': str(responses)
            }





