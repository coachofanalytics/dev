"""
String Utilities

Handles all string-related operations including:
- Random string generation
- Slug generation
- String manipulation and validation
- Text processing

This utility encapsulates string-related functionality previously scattered across main/utils.py
"""

import logging
import string
import random
from typing import Optional, List, Dict, Any
from django.utils.text import slugify
from django.db import models

logger = logging.getLogger(__name__)


class StringUtils:
    """
    Utility class for string-related operations.
    
    Provides methods for string generation, manipulation, and validation.
    """
    
    def __init__(self):
        self.logger = logger
    
    def random_string_generator(
        self, 
        size: int = 25, 
        chars: str = string.ascii_lowercase + string.digits
    ) -> str:
        """
        Generate a random string of specified size.
        
        Args:
            size: Length of the random string
            chars: Character set to use for generation
            
        Returns:
            Random string of specified size
        """
        try:
            if size <= 0:
                return ""
            
            # Use centralized utility service
            from core.services.utility_service import utility_service
            return utility_service.random_string_generator(size, chars)
            
        except Exception as e:
            self.logger.error(f"Error generating random string: {e}")
            # Fallback to original implementation
            return ''.join(random.choice(chars) for _ in range(size))
    
    def unique_slug_generator(
        self, 
        instance: models.Model, 
        new_slug: Optional[str] = None
    ) -> str:
        """
        Generate a unique slug for a model instance.
        
        Args:
            instance: Django model instance
            new_slug: Optional custom slug
            
        Returns:
            Unique slug string
        """
        try:
            # Use centralized utility service
            from core.services.utility_service import utility_service
            return utility_service.generate_unique_slug(instance, new_slug)
            
        except Exception as e:
            self.logger.error(f"Error generating unique slug: {e}")
            # Fallback to original implementation
            if new_slug is not None:
                slug = new_slug
            else:
                # Try to get slug from instance
                if hasattr(instance, 'title'):
                    slug = slugify(instance.title)
                elif hasattr(instance, 'name'):
                    slug = slugify(instance.name)
                else:
                    slug = slugify(str(instance))
            
            # Ensure slug is not empty
            if not slug:
                slug = self.random_string_generator(8)
            
            # Check for uniqueness
            model_class = instance.__class__
            original_slug = slug
            
            counter = 1
            while model_class.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            return slug
    
    def slug_pre_save_receiver(
        self, 
        sender: models.Model, 
        instance: models.Model, 
        *args, 
        **kwargs
    ) -> None:
        """
        Pre-save receiver for automatic slug generation.
        
        Args:
            sender: Model class
            instance: Model instance
            *args: Additional arguments
            **kwargs: Additional keyword arguments
        """
        try:
            if not instance.slug:
                instance.slug = self.unique_slug_generator(instance)
                
        except Exception as e:
            self.logger.error(f"Error in slug pre-save receiver: {e}")
    
    def parse_user_query(self, user_query: str) -> Dict[str, Any]:
        """
        Parse user query for intent and parameters.
        
        Args:
            user_query: User's query string
            
        Returns:
            Dict with parsed query information
        """
        try:
            if not user_query:
                return {'intent': 'unknown', 'parameters': {}}
            
            query_lower = user_query.lower().strip()
            
            # Simple intent detection
            intent = 'unknown'
            parameters = {}
            
            # Check for common intents
            if any(word in query_lower for word in ['create', 'add', 'new']):
                intent = 'create'
            elif any(word in query_lower for word in ['get', 'find', 'search', 'show']):
                intent = 'retrieve'
            elif any(word in query_lower for word in ['update', 'edit', 'modify']):
                intent = 'update'
            elif any(word in query_lower for word in ['delete', 'remove']):
                intent = 'delete'
            elif any(word in query_lower for word in ['help', 'how']):
                intent = 'help'
            
            # Extract potential parameters
            words = query_lower.split()
            for i, word in enumerate(words):
                if word in ['for', 'with', 'by'] and i + 1 < len(words):
                    parameters[word] = words[i + 1]
            
            return {
                'intent': intent,
                'parameters': parameters,
                'original_query': user_query,
                'word_count': len(words),
                'has_question': '?' in user_query
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing user query: {e}")
            return {
                'intent': 'unknown',
                'parameters': {},
                'original_query': user_query,
                'word_count': 0,
                'has_question': False
            }
    
    def validate_string_input(
        self, 
        input_string: str, 
        min_length: int = 1, 
        max_length: int = 1000,
        allowed_chars: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate string input based on criteria.
        
        Args:
            input_string: String to validate
            min_length: Minimum length required
            max_length: Maximum length allowed
            allowed_chars: Optional allowed characters
            
        Returns:
            Dict with validation results
        """
        try:
            if not isinstance(input_string, str):
                return {
                    'valid': False,
                    'error': 'Input must be a string',
                    'length': 0
                }
            
            length = len(input_string)
            
            if length < min_length:
                return {
                    'valid': False,
                    'error': f'String too short (minimum {min_length} characters)',
                    'length': length
                }
            
            if length > max_length:
                return {
                    'valid': False,
                    'error': f'String too long (maximum {max_length} characters)',
                    'length': length
                }
            
            if allowed_chars:
                for char in input_string:
                    if char not in allowed_chars:
                        return {
                            'valid': False,
                            'error': f'Character "{char}" not allowed',
                            'length': length
                        }
            
            return {
                'valid': True,
                'error': None,
                'length': length,
                'word_count': len(input_string.split())
            }
            
        except Exception as e:
            self.logger.error(f"Error validating string input: {e}")
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}',
                'length': 0
            }
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing extra whitespace and special characters.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        try:
            if not text:
                return ""
            
            # Remove extra whitespace
            cleaned = ' '.join(text.split())
            
            # Remove common unwanted characters
            unwanted_chars = ['\r', '\n', '\t']
            for char in unwanted_chars:
                cleaned = cleaned.replace(char, ' ')
            
            # Remove extra spaces again
            cleaned = ' '.join(cleaned.split())
            
            return cleaned.strip()
            
        except Exception as e:
            self.logger.error(f"Error cleaning text: {e}")
            return text or ""
    
    def extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            min_length: Minimum length of keywords
            
        Returns:
            List of keywords
        """
        try:
            if not text:
                return []
            
            # Simple keyword extraction
            words = text.lower().split()
            keywords = []
            
            # Filter out common stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
                'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
            }
            
            for word in words:
                # Remove punctuation
                clean_word = ''.join(char for char in word if char.isalnum())
                
                if (len(clean_word) >= min_length and 
                    clean_word not in stop_words and 
                    clean_word not in keywords):
                    keywords.append(clean_word)
            
            return keywords
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            return []
    
    def format_phone_number(self, phone: str) -> str:
        """
        Format phone number to standard format.
        
        Args:
            phone: Phone number string
            
        Returns:
            Formatted phone number
        """
        try:
            if not phone:
                return ""
            
            # Remove all non-digit characters
            digits = ''.join(char for char in phone if char.isdigit())
            
            # Format based on length
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits[0] == '1':
                return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
            else:
                return phone  # Return original if can't format
                
        except Exception as e:
            self.logger.error(f"Error formatting phone number: {e}")
            return phone or ""
    
    def truncate_text(self, text: str, max_length: int = 100, suffix: str = "...") -> str:
        """
        Truncate text to specified length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            suffix: Suffix to add when truncating
            
        Returns:
            Truncated text
        """
        try:
            if not text or len(text) <= max_length:
                return text
            
            return text[:max_length - len(suffix)] + suffix
            
        except Exception as e:
            self.logger.error(f"Error truncating text: {e}")
            return text or ""




