"""
Social Authentication Pipeline
Custom pipeline functions for social auth integration
"""
import logging
import traceback
from django.utils import timezone
from django.shortcuts import redirect
from accounts.models import UserProfile, Category
from django.urls import reverse

logger = logging.getLogger(__name__)


def create_user_profile(backend, user, response, is_new=False, *args, **kwargs):
    """
    Create UserProfile for users who register via social authentication.
    This function is called during the social auth pipeline.
    Uses get_or_create to safely handle existing profiles.
    """
    try:
        logger.error(f"[PIPELINE] create_user_profile called - user: {user}, backend: {backend.name}, is_new: {is_new}")

        if user:
            # Ensure user is active (social auth users should be active)
            if not user.is_active:
                user.is_active = True
                user.save(update_fields=['is_active'])
                logger.error(f"[PIPELINE] Activated user: {user.username}")

            # Get or create a default category for social auth users
            logger.error("[PIPELINE] Getting or creating default category...")
            default_category, cat_created = Category.objects.get_or_create(
                slug='individual',
                defaults={
                    'name': 'Individual',
                    'description': 'Individual users',
                    'icon': 'bi-person',
                    'is_active': True
                }
            )
            logger.error(f"[PIPELINE] Category: {default_category.name}, created: {cat_created}")

            # Get or create the user profile (safe for existing users)
            logger.error("[PIPELINE] Getting or creating user profile...")
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'category': default_category}
            )
            logger.error(f"[PIPELINE] Profile created: {profile_created}")

            # Ensure profile has a category (fix for existing profiles without category)
            if profile.category is None:
                profile.category = default_category
                profile.save(update_fields=['category'])
                logger.error(f"[PIPELINE] Assigned default category to existing profile")

            # Only update profile data if it was just created or if from social auth
            # Extract additional information from social auth response
            if backend.name == 'google-oauth2':
                # Google OAuth2 specific data
                logger.error(f"[PIPELINE] Processing Google OAuth2 response: {response}")
                if 'given_name' in response:
                    user.first_name = response.get('given_name', '')
                if 'family_name' in response:
                    user.last_name = response.get('family_name', '')
                # Note: Google profile picture URL cannot be stored in ImageField
                # Profile picture would need to be downloaded and saved as a file

            elif backend.name == 'facebook':
                # Facebook specific data
                logger.error(f"[PIPELINE] Processing Facebook response: {response}")
                if 'first_name' in response:
                    user.first_name = response.get('first_name', '')
                if 'last_name' in response:
                    user.last_name = response.get('last_name', '')
                # Note: Facebook profile picture URL cannot be stored in ImageField
                # Profile picture would need to be downloaded and saved as a file

            # Save the updated user and profile
            logger.error("[PIPELINE] Saving user...")
            user.save()
            logger.error("[PIPELINE] Saving profile...")
            profile.save()

            # Create OnboardingProgress for social auth users
            # Social auth users have verified email (from OAuth provider)
            # But profile is NOT complete yet - they need to select category
            logger.error("[PIPELINE] Creating OnboardingProgress...")
            from onboarding.models import OnboardingProgress
            progress, prog_created = OnboardingProgress.objects.get_or_create(
                user=user,
                defaults={
                    'email_verified': True,
                    'profile_completed': False,  # Will be set to True after category selection
                    'category_selected': False,  # Will be set to True after category selection
                }
            )
            logger.error(f"[PIPELINE] OnboardingProgress created: {prog_created}")

        logger.error("[PIPELINE] create_user_profile completed successfully")
        return {'user': user}
    except Exception as e:
        logger.error(f"[PIPELINE ERROR] create_user_profile failed: {str(e)}")
        logger.error(f"[PIPELINE ERROR] Traceback: {traceback.format_exc()}")
        raise


def require_category_selection(strategy, backend, user, *args, **kwargs):
    """
    Ensure OnboardingProgress exists for social auth users.

    NOTE: We do NOT redirect from within the pipeline as this loses session cookies.
    Instead, we let SOCIAL_AUTH_LOGIN_REDIRECT_URL handle the redirect, and the
    OnboardingMiddleware enforces the category selection flow.
    """
    try:
        logger.info(f"[PIPELINE] require_category_selection called - user: {user}, backend: {backend.name}")

        if user:
            # Ensure OnboardingProgress exists with correct flags
            from onboarding.models import OnboardingProgress
            progress, created = OnboardingProgress.objects.get_or_create(
                user=user,
                defaults={
                    'email_verified': True,  # Social auth verifies email
                    'profile_completed': False,
                    'category_selected': False,
                }
            )
            logger.info(f"[PIPELINE] OnboardingProgress created: {created}, category_selected: {progress.category_selected}")

        logger.info("[PIPELINE] require_category_selection completed - continuing pipeline")
        return None  # Continue pipeline, let settings redirect handle navigation
    except Exception as e:
        logger.error(f"[PIPELINE ERROR] require_category_selection failed: {str(e)}")
        logger.error(f"[PIPELINE ERROR] Traceback: {traceback.format_exc()}")
        # Don't raise - let the auth continue even if this fails
        return None
