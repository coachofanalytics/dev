from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from .forms import UserRegistrationForm, ProfileEditForm
from .models import UserProfile, Staff, Role, Category
from django.db.models import Count


@ratelimit(key='ip', rate='5/h', method='POST')
def register(request):
    """
    User registration view with file upload support.
    Rate limited to 5 registration attempts per hour per IP.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            category = form.cleaned_data.get('category')
            messages.success(request, f'Account created successfully for {username} as {category.name}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()

    context = {
        'form': form
    }
    return render(request, 'accounts/register.html', context)


@login_required
def profile(request, username=None):
    """
    Display user profile - accessible to all logged-in users.
    """
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user

    # Get or create profile for the user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if created and user == request.user:
        messages.info(request, 'Profile created. Please complete your profile information.')
        return redirect('edit_profile')

    is_own_profile = request.user == user

    context = {
        'profile_user': user,
        'profile': profile,
        'is_own_profile': is_own_profile,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    """
    Edit user profile view - accessible to all logged-in users.
    """
    # Get or create profile for the user
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if created:
        messages.info(request, 'Profile created. Please complete your profile information.')

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile', username=request.user.username)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileEditForm(instance=profile, user=request.user)

    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def investor_dashboard(request):
    """
    Dashboard for investors.
    """
    context = {
        'profile': request.user.profile,
    }
    return render(request, 'accounts/dashboards/investor.html', context)


@login_required
def business_dashboard(request):
    """
    Dashboard for businesses.
    """
    context = {
        'profile': request.user.profile,
    }
    return render(request, 'accounts/dashboards/business.html', context)


@login_required
def individual_dashboard(request):
    """
    Dashboard for individuals.
    """
    context = {
        'profile': request.user.profile,
    }
    return render(request, 'accounts/dashboards/individual.html', context)


@method_decorator(ratelimit(key='ip', rate='10/h', method='POST'), name='dispatch')
class CustomLoginView(LoginView):
    """
    Custom login view that redirects users to their category-specific dashboard.
    Rate limited to 10 login attempts per hour per IP.
    """
    template_name = 'registration/login.html'

    def get_success_url(self):
        """
        Redirect to the appropriate dashboard based on user type.
        """
        user = self.request.user

        # Check if user is superuser
        if user.is_superuser:
            return '/admin/'

        # Check if user is staff
        if hasattr(user, 'staff') and user.staff.is_active:
            return '/staff/dashboard/'

        # Regular user - redirect based on category
        if hasattr(user, 'profile') and user.profile.category:
            return f'/dashboard/{user.profile.category.slug}/'

        return '/'


@login_required
def staff_dashboard(request):
    """
    Dashboard for internal staff members.
    """
    # Check if user is staff
    if not hasattr(request.user, 'staff') or not request.user.staff.is_active:
        messages.error(request, 'You do not have permission to access the staff dashboard.')
        return redirect('home')

    staff = request.user.staff
    role = staff.role

    # Get statistics
    total_users = User.objects.count()
    total_categories = Category.objects.count()
    total_staff = Staff.objects.filter(is_active=True).count()

    # Category distribution
    category_stats = UserProfile.objects.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')

    # Recent users
    recent_users = User.objects.order_by('-date_joined')[:5]

    context = {
        'staff': staff,
        'role': role,
        'total_users': total_users,
        'total_categories': total_categories,
        'total_staff': total_staff,
        'category_stats': category_stats,
        'recent_users': recent_users,
    }
    return render(request, 'accounts/staff_dashboard.html', context)


@login_required
def staff_users_list(request):
    """
    List all users - for staff with can_manage_users permission.
    """
    if not hasattr(request.user, 'staff') or not request.user.staff.role.can_manage_users:
        messages.error(request, 'You do not have permission to manage users.')
        return redirect('staff_dashboard')

    users = User.objects.select_related('profile', 'profile__category').order_by('-date_joined')

    context = {
        'users': users,
        'staff': request.user.staff,
    }
    return render(request, 'accounts/staff_users_list.html', context)


@login_required
def staff_categories_list(request):
    """
    List all categories - for staff with can_manage_categories permission.
    """
    if not hasattr(request.user, 'staff') or not request.user.staff.role.can_manage_categories:
        messages.error(request, 'You do not have permission to manage categories.')
        return redirect('staff_dashboard')

    categories = Category.objects.annotate(
        user_count=Count('users')
    ).order_by('name')

    context = {
        'categories': categories,
        'staff': request.user.staff,
    }
    return render(request, 'accounts/staff_categories_list.html', context)


@login_required
def user_settings(request):
    """
    User settings page - accessible to all logged-in users.
    Provides access to account settings including password reset.
    """
    # Get or create profile for the user
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Determine user type for display
    user_type = None
    if request.user.is_superuser:
        user_type = 'Superuser'
    elif hasattr(request.user, 'staff') and request.user.staff.is_active:
        user_type = f'Staff - {request.user.staff.role.name}'
    elif profile.category:
        user_type = profile.category.name

    context = {
        'profile': profile,
        'user_type': user_type,
    }
    return render(request, 'accounts/settings.html', context)
