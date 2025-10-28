"""
Token Encryption Service for GoToMeeting OAuth Tokens

PHASE 1 IMPROVEMENT: Secure token storage with encryption.

This service handles encryption/decryption of OAuth tokens before storing in database.
Uses Django's cryptographic signing plus Fernet encryption for defense-in-depth.

Usage:
    from ai_services.services.token_encryption_service import TokenEncryptionService
    
    service = TokenEncryptionService()
    encrypted = service.encrypt_token("my_secret_token")
    decrypted = service.decrypt_token(encrypted)
"""

import os
import logging
from django.core.signing import Signer
from django.conf import settings
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)


class TokenEncryptionService:
    """
    Service for encrypting and decrypting OAuth tokens.
    
    Uses Fernet symmetric encryption with a key derived from Django SECRET_KEY.
    """
    
    def __init__(self):
        """Initialize encryption cipher"""
        # Generate encryption key from Django SECRET_KEY
        # This ensures we don't need a separate encryption key in environment
        secret_key = settings.SECRET_KEY.encode()
        
        # Fernet requires 32 url-safe base64-encoded bytes
        # We'll use the first 32 bytes of SHA256 hash of SECRET_KEY
        import hashlib
        key_hash = hashlib.sha256(secret_key).digest()
        self.key = base64.urlsafe_b64encode(key_hash[:32])
        self.cipher = Fernet(self.key)
        
        # Also use Django's signing for additional security layer
        self.signer = Signer()
    
    def encrypt_token(self, token: str) -> str:
        """
        Encrypt a token for secure storage.
        
        Args:
            token: Plain text token to encrypt
        
        Returns:
            Encrypted token as string
        
        Raises:
            ValueError: If token is None or empty
        """
        if not token:
            raise ValueError("Token cannot be None or empty")
        
        try:
            # Encrypt with Fernet
            encrypted_bytes = self.cipher.encrypt(token.encode('utf-8'))
            encrypted_string = encrypted_bytes.decode('utf-8')
            
            # Sign with Django signer (defense in depth)
            signed_encrypted = self.signer.sign(encrypted_string)
            
            logger.debug("✅ Token encrypted successfully")
            return signed_encrypted
            
        except Exception as e:
            logger.error(f"Token encryption failed: {e}", exc_info=True)
            raise
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt a token from storage.
        
        Args:
            encrypted_token: Encrypted token string
        
        Returns:
            Decrypted plain text token
        
        Raises:
            ValueError: If encrypted_token is None or empty
            Exception: If decryption fails (tampered data, wrong key, etc.)
        """
        if not encrypted_token:
            raise ValueError("Encrypted token cannot be None or empty")
        
        try:
            # Unsign with Django signer
            unsigned = self.signer.unsign(encrypted_token)
            
            # Decrypt with Fernet
            decrypted_bytes = self.cipher.decrypt(unsigned.encode('utf-8'))
            decrypted_string = decrypted_bytes.decode('utf-8')
            
            logger.debug("✅ Token decrypted successfully")
            return decrypted_string
            
        except Exception as e:
            logger.error(f"Token decryption failed: {e}", exc_info=True)
            raise
    
    def is_token_valid(self, encrypted_token: str) -> bool:
        """
        Check if an encrypted token can be decrypted (hasn't been tampered with).
        
        Args:
            encrypted_token: Encrypted token to validate
        
        Returns:
            True if token can be decrypted, False otherwise
        """
        try:
            self.decrypt_token(encrypted_token)
            return True
        except Exception:
            return False


class OAuthTokenManager:
    """
    Manager for OAuth token storage and retrieval.
    
    PHASE 1 IMPROVEMENT: Database-backed token storage with encryption.
    Replaces cache-based storage that was lost on server restart.
    """
    
    def __init__(self, service_name='gotomeeting'):
        """
        Initialize token manager.
        
        Args:
            service_name: Name of the service (gotomeeting, google_drive, etc.)
        """
        self.service_name = service_name
        self.encryption_service = TokenEncryptionService()
    
    def save_tokens(self, access_token, refresh_token, expires_in=3600):
        """
        Save OAuth tokens to database (encrypted).
        
        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token  
            expires_in: Token expiration time in seconds
        
        Returns:
            OAuthToken instance
        """
        from ai_services.models import OAuthToken
        from django.utils import timezone
        from datetime import timedelta
        
        # Encrypt tokens
        encrypted_access = self.encryption_service.encrypt_token(access_token)
        encrypted_refresh = self.encryption_service.encrypt_token(refresh_token)
        
        # Calculate expiration time
        expires_at = timezone.now() + timedelta(seconds=expires_in)
        
        # Create or update token record
        token_obj, created = OAuthToken.objects.update_or_create(
            service_name=self.service_name,
            defaults={
                'access_token': encrypted_access,
                'refresh_token': encrypted_refresh,
                'expires_at': expires_at,
                'is_valid': True,
                'last_refreshed_at': timezone.now() if not created else None,
            }
        )
        
        action = "Created" if created else "Updated"
        logger.info(f"✅ {action} {self.service_name} OAuth token (expires: {expires_at})")
        
        return token_obj
    
    def get_access_token(self):
        """
        Retrieve valid access token (auto-refresh if needed).
        
        Returns:
            Decrypted access token string, or None if not available
        """
        from ai_services.models import OAuthToken
        
        try:
            token_obj = OAuthToken.objects.get(service_name=self.service_name, is_valid=True)
            
            # Check if token needs refresh
            if token_obj.needs_refresh:
                logger.info(f"🔄 Token for {self.service_name} needs refresh")
                if self.refresh_token_from_db(token_obj):
                    # Get updated token
                    token_obj.refresh_from_db()
                else:
                    logger.error("Token refresh failed")
                    return None
            
            # Decrypt and return access token
            return self.encryption_service.decrypt_token(token_obj.access_token)
            
        except OAuthToken.DoesNotExist:
            logger.warning(f"No OAuth token found for {self.service_name}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving access token: {e}", exc_info=True)
            return None
    
    def get_refresh_token(self):
        """
        Retrieve refresh token.
        
        Returns:
            Decrypted refresh token string, or None if not available
        """
        from ai_services.models import OAuthToken
        
        try:
            token_obj = OAuthToken.objects.get(service_name=self.service_name, is_valid=True)
            return self.encryption_service.decrypt_token(token_obj.refresh_token)
        except OAuthToken.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error retrieving refresh token: {e}", exc_info=True)
            return None
    
    def refresh_token_from_db(self, token_obj):
        """
        Refresh access token using refresh token from database.
        
        Args:
            token_obj: OAuthToken instance
        
        Returns:
            True if refresh successful, False otherwise
        """
        try:
            # Decrypt refresh token
            refresh_token = self.encryption_service.decrypt_token(token_obj.refresh_token)
            
            # Call GoToMeeting API to refresh
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
            }
            auth = (os.environ.get("API_CLIENT_ID"), os.environ.get("API_CLIENT_SECRET"))
            
            response = requests.post(
                "https://authentication.logmeininc.com/oauth/token",
                headers=headers,
                data=data,
                auth=auth,
                timeout=10
            )
            response.raise_for_status()
            
            token_data = response.json()
            new_access_token = token_data.get('access_token')
            new_refresh_token = token_data.get('refresh_token', refresh_token)
            expires_in = token_data.get('expires_in', 3600)
            
            # Save refreshed tokens
            self.save_tokens(new_access_token, new_refresh_token, expires_in)
            
            return True
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}", exc_info=True)
            # Mark token as invalid
            token_obj.is_valid = False
            token_obj.save(update_fields=['is_valid'])
            return False
    
    def invalidate_tokens(self):
        """
        Mark tokens as invalid (e.g., after user logout or token compromise).
        """
        from ai_services.models import OAuthToken
        
        updated = OAuthToken.objects.filter(
            service_name=self.service_name,
            is_valid=True
        ).update(is_valid=False)
        
        logger.info(f"🔒 Invalidated {updated} token(s) for {self.service_name}")
        return updated > 0


# Convenience functions for backward compatibility with existing cache-based code
def save_tokens_to_db(access_token, refresh_token, expires_in=3600, service='gotomeeting'):
    """Save tokens to database (convenience wrapper)"""
    manager = OAuthTokenManager(service)
    return manager.save_tokens(access_token, refresh_token, expires_in)


def get_token_from_db(service='gotomeeting'):
    """Get access token from database (convenience wrapper)"""
    manager = OAuthTokenManager(service)
    return manager.get_access_token()

