"""
Middleware for enforcing onboarding completion.
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

from .models import OnboardingProgress


class OnboardingMiddleware:
    """
    Middleware to enforce onboarding completion.

    If user is authenticated but hasn't completed onboarding,
    redirects them to the appropriate onboarding step.
    """

    # URLs that don't require onboarding completion
    EXEMPT_URLS = [
        '/onboarding/',
        '/logout/',
        '/admin/',
        '/static/',
        '/media/',
        '/oauth/',
        '/accounts/logout/',
        '/accounts/login/',
        '/accounts/signup/',
        '/login/',
        '/register/',
        '/',  # Homepage
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated
        if request.user.is_authenticated:
            # Check if current path is exempt
            path = request.path
            is_exempt = any(path.startswith(exempt) for exempt in self.EXEMPT_URLS)

            if not is_exempt:
                try:
                    # Get onboarding progress
                    progress = OnboardingProgress.objects.get(user=request.user)

                    # If onboarding not complete, redirect to next step
                    if not progress.is_complete():
                        next_step_url = progress.get_next_step_url()

                        # Only redirect if we have a valid next step URL
                        if next_step_url and path != next_step_url:
                            # Show message only once
                            if not request.session.get('onboarding_message_shown'):
                                messages.info(
                                    request,
                                    f'Please complete your onboarding: {progress.get_status()}'
                                )
                                request.session['onboarding_message_shown'] = True

                            return redirect(next_step_url)
                        elif path == next_step_url:
                            # Clear the session flag when on the right page
                            request.session.pop('onboarding_message_shown', None)

                    else:
                        # Clear the session flag when onboarding is complete
                        request.session.pop('onboarding_message_shown', None)

                except OnboardingProgress.DoesNotExist:
                    # For existing users without onboarding progress,
                    # mark them as already complete (grandfathered in)
                    from django.utils import timezone
                    OnboardingProgress.objects.create(
                        user=request.user,
                        email_verified=True,
                        category_selected=True,
                        profile_completed=True,
                        completed_at=timezone.now()
                    )

        response = self.get_response(request)
        return response
