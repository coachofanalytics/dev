"""
User Service

Handles all user-related business logic including:
- User registration and management
- Email verification
- User profiles
- User groups and permissions
- Login history and security

This service encapsulates the business logic previously scattered across accounts/views.py
"""

import logging
from typing import Dict, List, Optional, Any
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

from .base_service import BaseAccountsService

logger = logging.getLogger(__name__)
User = get_user_model()


class UserService(BaseAccountsService):
    """
    Service for managing user operations.
    
    Handles user registration, profiles, groups, and security.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logger
    
    def register_user(
        self, 
        registration_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            registration_data: Dictionary containing user registration details
            
        Returns:
            Dict with success status and user data
        """
        try:
            # Validate required fields
            required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
            for field in required_fields:
                if field not in registration_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Validate email and password
            email = self._validate_email(registration_data['email'])
            password = self._validate_password(registration_data['password'])
            
            # Check if user already exists
            if User.objects.filter(username=registration_data['username']).exists():
                raise ValidationError("Username already exists")
            
            if User.objects.filter(email=email).exists():
                raise ValidationError("Email already registered")
            
            with transaction.atomic():
                # Create user
                user = User.objects.create_user(
                    username=registration_data['username'],
                    email=email,
                    password=password,
                    first_name=registration_data['first_name'],
                    last_name=registration_data['last_name'],
                    is_active=False  # Require email verification
                )
                
                # Log the operation
                self._log_operation(
                    'register_user',
                    user,
                    {'email': email}
                )
                
                # Generate verification token (placeholder)
                verification_token = self._generate_verification_token(user)
                
                return self.create_success_response(
                    {
                        'user_id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'verification_token': verification_token
                    },
                    "User registered successfully. Please verify your email."
                )

        except Exception as e:
            self._handle_error(e, 'register_user')
    
    def verify_email(
        self, 
        token: str
    ) -> Dict[str, Any]:
        """
        Verify user email with token.
        
        Args:
            token: Email verification token
            
        Returns:
            Dict with success status
        """
        try:
            if not token:
                raise ValidationError("Verification token is required")
            
            # Placeholder for actual token verification
            # This would typically validate the token and activate the user
            user_id = self._validate_verification_token(token)
            
            if not user_id:
                raise ValidationError("Invalid or expired verification token")
            
            try:
                user = User.objects.get(id=user_id)
            except ObjectDoesNotExist:
                raise ValidationError("User not found")
            
            with transaction.atomic():
                # Activate user
                user.is_active = True
                user.save()
                
                # Log the operation
                self._log_operation(
                    'verify_email',
                    user,
                    {'token': token}
                )
                
                return self.create_success_response(
                    {'user_id': user.id, 'username': user.username},
                    "Email verified successfully"
                )

        except Exception as e:
            self._handle_error(e, 'verify_email')
    
    def get_user_profile(
        self, 
        user: User,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user profile.
        
        Args:
            user: The user requesting the profile
            username: Optional specific username
            
        Returns:
            Dict with success status and profile data
        """
        try:
            self._validate_user(user)
            
            target_user = user
            if username and username != user.username:
                try:
                    target_user = User.objects.get(username=username)
                except ObjectDoesNotExist:
                    raise ValidationError("User not found")
            
            # Log the operation
            self._log_operation(
                'get_user_profile',
                user,
                {'target_username': target_user.username}
            )
            
            # Get profile data
            profile_data = {
                'id': target_user.id,
                'username': target_user.username,
                'email': target_user.email,
                'first_name': target_user.first_name,
                'last_name': target_user.last_name,
                'date_joined': target_user.date_joined,
                'last_login': target_user.last_login,
                'is_active': target_user.is_active,
                'is_staff': target_user.is_staff,
                'groups': [group.name for group in target_user.groups.all()]
            }
            
            return self.create_success_response(
                profile_data,
                f"Profile retrieved for {target_user.username}"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_user_profile', user)
    
    def update_user_profile(
        self, 
        user: User, 
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user profile.
        
        Args:
            user: The user updating the profile
            profile_data: Dictionary containing profile updates
            
        Returns:
            Dict with success status and updated profile data
        """
        try:
            self._validate_user(user)
            validated_data = self._validate_profile_data(profile_data)
            
            with transaction.atomic():
                # Update user profile
                user.first_name = validated_data['first_name']
                user.last_name = validated_data['last_name']
                
                if 'email' in validated_data:
                    user.email = self._validate_email(validated_data['email'])
                
                user.save()
                
                # Log the operation
                self._log_operation(
                    'update_user_profile',
                    user,
                    {'updated_fields': list(validated_data.keys())}
                )
                
                return self.create_success_response(
                    {
                        'user_id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email
                    },
                    "Profile updated successfully"
                )

        except Exception as e:
            self._handle_error(e, 'update_user_profile', user)
    
    def get_users(
        self, 
        user: User,
        active_only: bool = True,
        staff_only: bool = False
    ) -> Dict[str, Any]:
        """
        Get list of users.
        
        Args:
            user: The user requesting the list
            active_only: Whether to return only active users
            staff_only: Whether to return only staff users
            
        Returns:
            Dict with success status and list of users
        """
        try:
            self._validate_user(user)
            
            # Log the operation
            self._log_operation(
                'get_users',
                user,
                {'active_only': active_only, 'staff_only': staff_only}
            )
            
            # Get users
            queryset = User.objects.all()
            
            if active_only:
                queryset = queryset.filter(is_active=True)
            
            if staff_only:
                queryset = queryset.filter(is_staff=True)
            
            users = []
            for u in queryset.order_by('username'):
                users.append({
                    'id': u.id,
                    'username': u.username,
                    'email': u.email,
                    'first_name': u.first_name,
                    'last_name': u.last_name,
                    'date_joined': u.date_joined,
                    'last_login': u.last_login,
                    'is_active': u.is_active,
                    'is_staff': u.is_staff
                })
            
            return self.create_success_response(
                {'users': users},
                f"Retrieved {len(users)} users"
            )

        except Exception as e:
            self._handle_error(e, 'get_users', user)
    
    def get_user_login_history(
        self, 
        user: User,
        target_username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user login history.
        
        Args:
            user: The user requesting the history
            target_username: Optional specific username
            
        Returns:
            Dict with success status and login history
        """
        try:
            self._validate_user(user)
            
            # Log the operation
            self._log_operation(
                'get_user_login_history',
                user,
                {'target_username': target_username}
            )
            
            # Placeholder for actual login history retrieval
            login_history = {
                'username': target_username or user.username,
                'total_logins': 0,
                'last_login': None,
                'login_sessions': [],
                'security_events': []
            }
            
            return self.create_success_response(
                login_history,
                f"Login history retrieved for {target_username or user.username}"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_user_login_history', user)
    
    def create_user_group(
        self, 
        user: User, 
        group_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new user group.
        
        Args:
            user: The user creating the group
            group_data: Dictionary containing group details
            
        Returns:
            Dict with success status and group data
        """
        try:
            self._validate_user(user)
            
            if not user.is_staff:
                raise ValidationError("Staff permissions required to create groups")
            
            # Validate required fields
            if 'name' not in group_data:
                raise ValidationError("Group name is required")
            
            if len(group_data['name']) < 2:
                raise ValidationError("Group name must be at least 2 characters long")
            
            # Log the operation
            self._log_operation(
                'create_user_group',
                user,
                {'group_name': group_data['name']}
            )
            
            # Placeholder for actual group creation
            group = {
                'id': 1,  # Placeholder ID
                'name': group_data['name'],
                'description': group_data.get('description', ''),
                'created_by': user.username,
                'created_at': timezone.now()
            }
            
            return self.create_success_response(
                group,
                f"Group '{group_data['name']}' created successfully"
            )

        except Exception as e:
            self._handle_error(e, 'create_user_group', user)
    
    def get_user_analytics(
        self, 
        user: User
    ) -> Dict[str, Any]:
        """
        Get user analytics.
        
        Args:
            user: The user requesting analytics
            
        Returns:
            Dict with success status and analytics data
        """
        try:
            self._validate_user(user)
            
            # Log the operation
            self._log_operation(
                'get_user_analytics',
                user
            )
            
            # Placeholder for actual analytics calculation
            analytics_data = {
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
                'staff_users': User.objects.filter(is_staff=True).count(),
                'new_users_today': 0,
                'user_growth_rate': 0,
                'most_active_users': [],
                'registration_trends': []
            }
            
            return self.create_success_response(
                analytics_data,
                "User analytics retrieved successfully"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_user_analytics', user)
    
    # Helper methods
    def _generate_verification_token(self, user: User) -> str:
        """Generate email verification token."""
        # Placeholder for actual token generation
        return f"token_{user.id}_{timezone.now().timestamp()}"
    
    def _validate_verification_token(self, token: str) -> Optional[int]:
        """Validate email verification token."""
        # Placeholder for actual token validation
        if token.startswith('token_'):
            try:
                parts = token.split('_')
                return int(parts[1])
            except (IndexError, ValueError):
                return None
        return None