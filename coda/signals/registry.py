"""
Unified Signal Registry for CODA Application
Consolidates signal handling to eliminate duplication and improve maintainability.
"""

from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify
from django.core.mail import send_mail
from django.conf import settings

from shared_core.users import CustomerUser, UserCategory as CategoryChoices
from accounts.models import UserGroups, LoginHistory
from accounts.utils import send_email_to_applicant


class SignalRegistry:
    """Centralized signal registration and management"""
    
    def __init__(self):
        self.registered_signals = {}
        self._setup_user_signals()
    
    def _setup_user_signals(self):
        """Setup all user-related signals"""
        # User creation and update signals
        post_save.connect(self._handle_user_post_save, sender=CustomerUser)
        post_delete.connect(self._handle_user_deletion, sender=CustomerUser)
        
        # User authentication signals
        user_logged_in.connect(self._handle_user_login, sender=CustomerUser)
        user_logged_out.connect(self._handle_user_logout, sender=CustomerUser)
    
    def _handle_user_post_save(self, sender, instance, created, **kwargs):
        """Unified handler for all CustomerUser post_save operations"""
        try:
            if created:
                self._handle_new_user_creation(instance)
            else:
                self._handle_user_update(instance)
        except Exception as e:
            # Log error but don't break the signal
            print(f"Error in user post_save signal: {e}")
    
    def _handle_new_user_creation(self, user):
        """Centralized new user creation handling"""
        self._create_user_profile(user)
        self._assign_user_to_group(user)
        self._send_welcome_email(user)
        self._assign_default_permissions(user)
    
    def _handle_user_update(self, user):
        """Centralized user update handling"""
        self._update_user_group_assignment(user)
        self._handle_status_changes(user)
    
    def _create_user_profile(self, user):
        """Create user profile if it doesn't exist"""
        # This would create a UserProfile if needed
        # Currently handled by existing signals
        pass



    def _assign_user_to_group(self, user):
        """Assign user to appropriate group based on category"""
        try:
            category = user.category
            
            # Get all available categories dynamically
            category_choices = dict(CategoryChoices.choices)
            
            # Handle legacy or invalid categories by mapping to a default
            if category not in category_choices:
                # Find the first available category as default
                default_category = min(category_choices.keys())
                print(f"Warning: Category {category} not found in choices. Mapping to default category {default_category}")
                
                # Update user's category to the default
                user.category = default_category
                user.save()
                category = default_category

            # Get the category name dynamically
            category_name = category_choices[category]
            
            # Generate the base group name based on the category
            base_group_name = slugify(category_name)
            
            # Find the latest group in the category
            last_group = UserGroups.objects.filter(
                name__startswith=base_group_name
            ).order_by('-id').first()
            
            if last_group and last_group.users.count() < 30:
                # Add the user to the last group if it has less than 30 users
                last_group.users.add(user)
                last_group.save()
                print(f"User {user.username} added to existing group: {last_group.name}")

            else:
                # Create a new group if the last group is full or does not exist
                group_count = UserGroups.objects.filter(
                    name__startswith=base_group_name
                ).count() + 1
                new_group_name = f"{base_group_name} Group {group_count}"
                
                # Create a new group and add the user
                new_group = UserGroups.objects.create(
                    name=new_group_name,
                    is_active=True,
                    is_featured=True
                )
                new_group.users.add(user)
                new_group.save()
                print(f"User {user.username} added to new group: {new_group.name}")

        except Exception as e:
            print(f"Error assigning user to group: {e}")
            # Don't fail the user creation, just log the error

    def _send_welcome_email(self, user):
        """Send welcome email to new user"""
        try:
            if user.category == CategoryChoices.APPLICANT:
                send_email_to_applicant(user)
            else:
                # Send generic welcome email
                subject = "Welcome to CODA!"
                message = f"Hi {user.first_name}, welcome to CODA! Your account has been created successfully."
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
        except Exception as e:
            print(f"Error sending welcome email: {e}")
    
    def _assign_default_permissions(self, user):
        """Assign default permissions based on user category"""
        try:
            if user.category == CategoryChoices.APPLICANT:
                user.is_staff = True
                user.save()
        except Exception as e:
            print(f"Error assigning default permissions: {e}")
    
    def _update_user_group_assignment(self, user):
        """Update user group assignment if category changed"""
        # This could handle moving users between groups if categories change
        pass
    
    def _handle_status_changes(self, user):
        """Handle user status changes"""
        try:
            if user.is_active and user.category == CategoryChoices.APPLICANT:
                send_email_to_applicant(user)
        except Exception as e:
            print(f"Error handling status changes: {e}")
    
    def _handle_user_deletion(self, sender, instance, **kwargs):
        """Handle user deletion"""
        try:
            # Clean up related data
            print(f"User {instance.username} deleted, cleaning up related data")
        except Exception as e:
            print(f"Error handling user deletion: {e}")
    
    def _handle_user_login(self, sender, user, request, **kwargs):
        """Handle user login"""
        try:
            LoginHistory.objects.create(user=user, login_time=timezone.now())
        except Exception as e:
            print(f"Error handling user login: {e}")
    
    def _handle_user_logout(self, sender, user, request, **kwargs):
        """Handle user logout"""
        try:
            last_login_entry = LoginHistory.objects.filter(
                user=user
            ).order_by('-login_time').first()
            
            if last_login_entry and last_login_entry.logout_time is None:
                last_login_entry.logout_time = timezone.now()
                last_login_entry.save()
        except Exception as e:
            print(f"Error handling user logout: {e}")




# Create and register the signal registry
registry = SignalRegistry()


# Legacy signal handlers for backward compatibility
# These will be removed once all apps are updated to use the registry

@receiver(post_save, sender=CustomerUser)
def add_user_to_group(sender, instance, created, **kwargs):
    """Legacy signal handler - will be removed after consolidation"""
    if created:
        registry._assign_user_to_group(instance)

@receiver(post_save, sender=CustomerUser)
def send_applicant_email_on_activation(sender, instance, **kwargs):
    """Legacy signal handler - will be removed after consolidation"""
    if instance.category == CategoryChoices.APPLICANT and instance.is_active:
        try:
            send_email_to_applicant(instance)
        except Exception as e:
            print(f"Error sending applicant email: {e}")

@receiver(user_logged_in)
def track_login(sender, user, request, **kwargs):
    """Legacy signal handler - will be removed after consolidation"""
    try:
        LoginHistory.objects.create(user=user, login_time=timezone.now())
    except Exception as e:
        print(f"Error tracking login: {e}")

@receiver(user_logged_out)
def track_logout(sender, user, request, **kwargs):
    """Legacy signal handler - will be removed after consolidation"""
    try:
        last_login_entry = LoginHistory.objects.filter(
            user=user
        ).order_by('-login_time').first()
        
        if last_login_entry and last_login_entry.logout_time is None:
            last_login_entry.logout_time = timezone.now()
            last_login_entry.save()
    except Exception as e:
        print(f"Error tracking logout: {e}") 