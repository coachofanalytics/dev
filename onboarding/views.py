"""
Onboarding views for user registration and profile completion.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods

from .forms import SimplifiedRegistrationForm, CompleteProfileForm
from .forms_social import SocialAuthCategoryForm
from .models import OnboardingProgress, EmailVerificationToken
from .services.onboarding_service import OnboardingService
from accounts.models import UserProfile


def simplified_register(request):
    """
    Simplified registration view - only collects essential info.

    After registration, sends verification email and redirects to check-email page.
    """
    # Redirect if already authenticated
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SimplifiedRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Create user (inactive until email verified)
                user = User.objects.create_user(
                    username=form.cleaned_data['email'].split('@')[0] + str(User.objects.count()),
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    is_active=False  # Inactive until email verified
                )

                # Update the auto-created UserProfile with selected category
                # (UserProfile is auto-created by signal in accounts.models)
                user.profile.category = form.cleaned_data['category']
                user.profile.save()

                # Create onboarding progress
                progress = OnboardingService.create_onboarding_progress(user)

                # User already selected category during registration, so mark it complete
                progress.category_selected = True
                progress.save(update_fields=['category_selected'])

                # Generate verification token
                token = OnboardingService.generate_verification_token(user)

                # Send verification email
                email_sent = OnboardingService.send_verification_email(user, token.token)

                # Store user email in session for resend functionality
                request.session["pending_verification_email"] = user.email

                if email_sent:
                    messages.success(
                        request,
                        f'Registration successful! We\'ve sent a verification email to {user.email}. '
                        'Please check your inbox and click the verification link.'
                    )
                    return redirect('onboarding:check_email')
                else:
                    messages.warning(
                        request,
                        'Registration successful, but we couldn\'t send the verification email. '
                        'Please contact support.'
                    )
                    return redirect('onboarding:check_email')

            except Exception as e:
                messages.error(request, f'An error occurred during registration: {str(e)}')
    else:
        form = SimplifiedRegistrationForm()

    return render(request, 'onboarding/register.html', {'form': form})


def check_email(request):
    """
    Page shown after registration asking user to check email.
    """
    return render(request, 'onboarding/check_email.html')


def verify_email(request, token):
    """
    Email verification view - verifies token and activates user account.

    After successful verification, logs in user and redirects to complete-profile.
    """
    success, user, message = OnboardingService.verify_email_token(token)

    if success:
        messages.success(request, message)
        # Log the user in
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('onboarding:complete_profile')
    else:
        messages.error(request, message)
        return redirect('onboarding:resend_verification')


def resend_verification_email(request):
    """
    Resend verification email to user.
    Works for both logged-in and non-logged-in users (via session).
    """
    if request.method == 'POST':
        # Try to get user from session email or from authenticated user
        user = None
        if request.user.is_authenticated:
            user = request.user
        elif 'pending_verification_email' in request.session:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(email=request.session['pending_verification_email'])
            except User.DoesNotExist:
                messages.error(request, 'User not found. Please register again.')
                return redirect('onboarding:register')
        
        if user:
            success, message = OnboardingService.resend_verification_email(user)
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
            # Stay on check_email page instead of redirecting
            return redirect('onboarding:check_email')
        else:
            messages.error(request, 'Please log in or complete registration first.')
            return redirect('login')

    return render(request, 'onboarding/resend_verification.html')


@login_required
def complete_profile(request):
    """
    Complete profile view - collects remaining profile information.

    After completion, marks onboarding as complete and redirects to dashboard.
    """
    # Check if profile already completed
    try:
        progress = OnboardingProgress.objects.get(user=request.user)
        if progress.is_complete():
            messages.info(request, 'Your profile is already complete!')
            return redirect('dashboard')

        # Check if email verified
        if not progress.email_verified:
            messages.warning(request, 'Please verify your email first.')
            return redirect('onboarding:check_email')

    except OnboardingProgress.DoesNotExist:
        messages.error(request, 'Onboarding progress not found.')
        return redirect('dashboard')

    # Get user profile
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = CompleteProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            try:
                form.save()

                # Mark profile as completed
                progress.mark_profile_completed()

                messages.success(
                    request,
                    'Profile completed successfully! Welcome to Biashara Bridges!'
                )
                return redirect('dashboard')

            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
    else:
        form = CompleteProfileForm(instance=profile)

    return render(request, 'onboarding/complete_profile.html', {
        'form': form,
        'progress': progress
    })


@login_required
def onboarding_status(request):
    """
    View current onboarding status.
    """
    status = OnboardingService.check_onboarding_status(request.user)

    return render(request, 'onboarding/status.html', {
        'status': status
    })


@login_required
def select_category_social(request):
    """
    Category selection view for users who registered via social authentication.

    After social auth completes, users are redirected here to select their category.
    """
    # Check if user already has a category selected
    try:
        profile = request.user.profile
        if profile.category and profile.category.slug != 'individual':
            # User already has a specific category, redirect to dashboard
            messages.info(request, 'Your profile is already set up!')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = SocialAuthCategoryForm(request.POST)
        if form.is_valid():
            try:
                # Update user's category
                profile.category = form.cleaned_data['category']
                profile.save()

                # Ensure onboarding progress exists
                # Only mark category_selected = True, NOT profile_completed
                # User still needs to complete their profile (phone, country, etc.)
                progress, created = OnboardingProgress.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'email_verified': True,  # Social auth verifies email
                        'profile_completed': False,  # NOT complete yet - need profile info
                        'category_selected': True,
                    }
                )

                # Update category_selected flag if not already set
                if not progress.category_selected:
                    progress.category_selected = True
                    progress.save(update_fields=['category_selected'])

                messages.success(
                    request,
                    f'Great choice! Now let\'s complete your profile.'
                )
                # Redirect to complete_profile, NOT dashboard
                return redirect('onboarding:complete_profile')

            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
    else:
        form = SocialAuthCategoryForm()

    return render(request, 'onboarding/select_category_social.html', {
        'form': form,
        'user': request.user
    })
