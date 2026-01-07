"""
Custom adapters for django-allauth
Integrates allauth with existing user registration system
"""
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from .models import UserProfile, Category


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter to integrate with existing UserProfile system.
    """

    def save_user(self, request, user, form, commit=True):
        """
        Save a new user instance using information provided in the signup form.
        """
        user = super().save_user(request, user, form, commit=False)

        # Save the user first so we have a user ID
        if commit:
            user.save()

            # Create UserProfile if it doesn't exist
            if not hasattr(user, 'userprofile'):
                # Get or create default category
                default_category, _ = Category.objects.get_or_create(
                    slug='individual',
                    defaults={
                        'name': 'Individual',
                        'description': 'Individual users',
                        'icon': 'bi-person',
                        'is_active': True
                    }
                )

                # Create user profile
                UserProfile.objects.create(
                    user=user,
                    category=default_category
                )

        return user

    def get_login_redirect_url(self, request):
        """
        Redirect users based on their role after login.
        """
        user = request.user

        if user.is_superuser:
            return '/admin/'
        elif user.is_staff:
            return '/staff/dashboard/'
        else:
            # Check if user has completed their profile
            if hasattr(user, 'userprofile'):
                profile = user.userprofile
                if profile.category:
                    category_slug = profile.category.slug
                    if category_slug == 'investor':
                        return '/dashboard/investor/'
                    elif category_slug == 'business':
                        return '/dashboard/business/'
                    else:
                        return '/dashboard/individual/'

            # Default redirect
            return settings.LOGIN_REDIRECT_URL

    def get_email_confirmation_redirect_url(self, request):
        """
        Redirect URL after email confirmation.
        Redirect to login page with success message.
        """
        return settings.LOGIN_URL

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        Send email confirmation.
        """
        current_site = get_current_site(request)
        activate_url = self.get_email_confirmation_url(request, emailconfirmation)

        ctx = {
            "user": emailconfirmation.email_address.user,
            "activate_url": activate_url,
            "current_site": current_site,
            "key": emailconfirmation.key,
        }

        if signup:
            email_template = 'account/email/email_confirmation_signup'
        else:
            email_template = 'account/email/email_confirmation'

        self.send_mail(email_template, emailconfirmation.email_address.email, ctx)
