import traceback
import logging
from django.http import Http404, HttpResponse
from django.core.exceptions import ValidationError
from ai_services.models import Logs

logger = logging.getLogger(__name__)

class MailMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Add input validation
        try:
            # Validate request path
            if not request.path or len(request.path) > 500:
                logger.warning(f"Invalid request path: {request.path}")
                return HttpResponse("Invalid request", status=400)
            
            # Validate request method
            if request.method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                logger.warning(f"Invalid request method: {request.method}")
                return HttpResponse("Method not allowed", status=405)
                
        except Exception as e:
            logger.error(f"Middleware validation error: {e}")
            return HttpResponse("Bad request", status=400)
        
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        try:
            # Don't log sensitive information
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_id = request.user.id
            else:
                user_id = None
            
            # Log error without exposing sensitive details
            logger.error(f"Exception in {request.path}: {type(exception).__name__}: {str(exception)}")
            
            # Only log to database for non-sensitive errors
            if not self._is_sensitive_exception(exception):
                try:
                    Logs.objects.create(
                        api=request.path,
                        location_in_code=self._get_safe_error_location(exception),
                        reason_code_crash=str(exception)[:200],  # Limit length
                        user_id=user_id,
                        exception=str(exception.args)[:200]  # Limit length
                    )
                except Exception as log_error:
                    logger.error(f"Failed to log to database: {log_error}")
            
        except Exception as e:
            logger.error(f"Error in middleware exception handler: {e}")
        
        # Don't return anything - let Django handle the exception
        return None
    
    def _is_sensitive_exception(self, exception):
        """Check if exception contains sensitive information"""
        sensitive_keywords = ['password', 'token', 'secret', 'key', 'credential']
        exception_str = str(exception).lower()
        return any(keyword in exception_str for keyword in sensitive_keywords)
    
    def _get_safe_error_location(self, exception):
        """Get safe error location without exposing sensitive information"""
        try:
            tb = traceback.extract_tb(exception.__traceback__)
            if tb:
                # Return only filename and line number, not full path
                frame = tb[-1]
                return f"{frame.filename.split('/')[-1]}:{frame.lineno}"
        except:
            pass
        return "Unknown location"
