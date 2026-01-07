"""
KYC decorators for restricting access to features.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import KYCVerificationLevel


def kyc_required(view_func):
    """
    Decorator to require KYC verification before accessing a view.

    Checks if user has completed KYC verification (identity_verified=True).
    If not, redirects to KYC upload page with a message.
    """
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        try:
            kyc_level = KYCVerificationLevel.objects.get(user=request.user)

            # Check if user has completed KYC (identity verified)
            if not kyc_level.identity_verified:
                messages.warning(
                    request,
                    'You must complete KYC verification to access this feature. '
                    'Please upload your identity documents for admin approval.'
                )
                return redirect('kyc:upload')

        except KYCVerificationLevel.DoesNotExist:
            # No KYC level exists - redirect to upload
            messages.warning(
                request,
                'You must complete KYC verification to access this feature. '
                'Please upload your identity documents for admin approval.'
            )
            return redirect('kyc:upload')

        # KYC verified - allow access
        return view_func(request, *args, **kwargs)

    return wrapped_view


def kyc_level_required(min_level='standard'):
    """
    Decorator to require a specific KYC verification level.

    Args:
        min_level: Minimum KYC level required ('basic', 'standard', 'enhanced', 'premium')

    Usage:
        @kyc_level_required('enhanced')
        def high_value_investment_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            try:
                kyc_level = KYCVerificationLevel.objects.get(user=request.user)

                level_order = ['basic', 'standard', 'enhanced', 'premium']
                user_level_index = level_order.index(kyc_level.level)
                required_level_index = level_order.index(min_level)

                if user_level_index < required_level_index:
                    messages.warning(
                        request,
                        f'This feature requires {min_level.capitalize()} KYC verification. '
                        f'Your current level is {kyc_level.get_level_display()}. '
                        'Please complete additional verification steps.'
                    )
                    return redirect('kyc:verification_status')

            except KYCVerificationLevel.DoesNotExist:
                messages.warning(
                    request,
                    f'This feature requires {min_level.capitalize()} KYC verification. '
                    'Please complete KYC verification first.'
                )
                return redirect('kyc:upload')

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator
