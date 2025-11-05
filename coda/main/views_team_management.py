"""
Team Management Views - Web UI for managing team assignments.

Provides a user-friendly interface for admins to:
- View all team members by category
- Assign members to teams
- Set priorities
- Promote members
- Recalculate points
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from accounts.models import TeamProfile
from main.services.team_service import TeamService

User = get_user_model()


@login_required
@user_passes_test(lambda u: u.is_superuser)
def team_management_dashboard(request):
    """
    Main team management dashboard.
    Shows all categories with member counts and quick actions.
    """
    # Get all team groups with member counts (show all, including empty)
    from urllib.parse import quote
    team_groups = []
    for group_name in TeamService.ALL_CATEGORIES:
        group = Group.objects.filter(name=group_name).first()
        if group:
            member_count = group.user_set.filter(is_active=True).count()
            is_manual = group_name in TeamService.MANUAL_CATEGORIES
            
            team_groups.append({
                'name': group_name,
                'name_encoded': quote(group_name),  # URL-encoded version
                'member_count': member_count,
                'is_manual': is_manual,
                'is_empty': member_count == 0,
                'group_obj': group,
            })
    
    # Get promotion candidates
    promotion_candidates = TeamService.get_promotion_candidates()
    
    # Get team statistics
    total_team_members = TeamProfile.objects.filter(user__is_active=True).count()
    
    # Manual count: users in manual categories
    manual_count = User.objects.filter(
        is_active=True,
        groups__name__in=TeamService.MANUAL_CATEGORIES
    ).distinct().count()
    
    # Points-based count: users in points-based categories
    auto_count = User.objects.filter(
        is_active=True,
        groups__name__in=TeamService.POINTS_CATEGORIES
    ).distinct().count()
    
    context = {
        'title': 'Team Management Dashboard',
        'team_groups': team_groups,
        'promotion_candidates': promotion_candidates,
        'total_team_members': total_team_members,
        'manual_count': manual_count,
        'auto_count': auto_count,
    }
    
    return render(request, 'main/team_management/dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def team_category_detail(request, category_name):
    """
    View and manage members in a specific category.
    """
    from urllib.parse import quote
    from django.core.paginator import Paginator
    
    # Get members in this category
    members = TeamService.get_team_members(category_name)
    
    # Get group
    group = get_object_or_404(Group, name=category_name)
    
    # Check if manual or points-based
    is_manual = category_name in TeamService.MANUAL_CATEGORIES
    
    # Get all active employees not in this category (for adding)
    # Use is_staff=True (currently employed by CODA) instead of category=2 (which is STUDENT)
    available_users_all = User.objects.filter(
        is_staff=True,  # Currently employed by CODA (not just applicants/students)
        is_active=True,  # Account not disabled
    ).exclude(
        groups__name=category_name
    ).select_related('profile', 'team_profile')
    
    # Apply search filter if provided
    search_query = request.GET.get('search', '').strip()
    if search_query:
        available_users_all = available_users_all.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(profile__position__icontains=search_query)
        )
    
    # Order results
    available_users_all = available_users_all.order_by('username')
    
    # Paginate available users (20 per page)
    paginator = Paginator(available_users_all, 20)
    page_number = request.GET.get('page', 1)
    available_users_page = paginator.get_page(page_number)
    
    context = {
        'title': f'{category_name} - Team Management',
        'category_name': category_name,
        'category_name_encoded': quote(category_name),  # URL-encoded version
        'members': members,
        'group': group,
        'is_manual': is_manual,
        'available_users': available_users_page,  # Paginated
        'total_available': available_users_all.count(),  # Total count
    }
    
    return render(request, 'main/team_management/category_detail.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def assign_member_to_category(request, user_id, category_name):
    """
    Assign a specific user to a team category.
    """
    user = get_object_or_404(User, id=user_id)
    
    # Assign using TeamService
    TeamService.assign_to_category(
        user,
        category_name,
        priority=50,  # Default priority
        is_manual=True,
        notes=f'Assigned by {request.user.username} via web interface'
    )
    
    messages.success(
        request,
        f'Successfully assigned {user.get_full_name()} to {category_name}'
    )
    
    return redirect('main:team_category_detail', category_name=category_name)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def remove_member_from_category(request, user_id, category_name):
    """
    Remove a user from a team category.
    """
    user = get_object_or_404(User, id=user_id)
    group = get_object_or_404(Group, name=category_name)
    
    # Remove from group
    user.groups.remove(group)
    
    messages.success(
        request,
        f'Removed {user.get_full_name()} from {category_name}'
    )
    
    return redirect('main:team_category_detail', category_name=category_name)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_member_priority(request, user_id):
    """
    Update a member's display priority.
    """
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        priority = int(request.POST.get('priority', 0))
        
        team_profile = user.team_profile
        team_profile.priority = priority
        team_profile.save()
        
        messages.success(
            request,
            f'Updated priority for {user.get_full_name()} to {priority}'
        )
        
        # Redirect back to category page
        category = team_profile.category
        if category:
            return redirect('main:team_category_detail', category_name=category)
    
    return redirect('main:team_management_dashboard')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def recalculate_all_points(request):
    """
    Recalculate points for all non-manual members.
    """
    from django.utils import timezone
    
    profiles = TeamProfile.objects.filter(is_manually_assigned=False)
    count = 0
    
    for team_profile in profiles:
        points = TeamService.calculate_total_points(team_profile.user)
        team_profile.total_points = points
        team_profile.save()
        
        # Auto-categorize
        TeamService.auto_categorize_by_points(team_profile.user)
        count += 1
    
    messages.success(
        request,
        f'Successfully recalculated points for {count} member(s)'
    )
    
    return redirect('main:team_management_dashboard')

