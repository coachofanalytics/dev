"""
Team Service - Business logic for team assignment and categorization.

This service handles:
- Point calculation from multiple sources
- Team category assignment (manual and points-based)
- Promotion candidate detection
- Auto-categorization for trainees
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Sum
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class TeamService:
    """Service layer for team operations"""
    
    # Team category definitions
    MANUAL_CATEGORIES = [
        'BOG/Leadership',
        'Elite Team',
        'Lead Team',
        'Support Team',
        'Senior Analysts',
        'Junior Analysts',
    ]
    
    POINTS_CATEGORIES = [
        'Senior Trainee',
        'Junior Trainee',
        'Elementary',
    ]
    
    ALL_CATEGORIES = MANUAL_CATEGORIES + POINTS_CATEGORIES
    
    # Point thresholds for auto-categorization
    POINT_THRESHOLDS = {
        'Senior Trainee': (5000, 6000),
        'Junior Trainee': (4000, 5000),
        'Elementary': (0, 4000),
    }
    
    # Education point multipliers
    EDUCATION_POINTS = {
        1: 250,    # High School
        2: 500,    # Some College
        3: 1000,   # Bachelor's
        4: 1500,   # Master's
        5: 2000,   # Doctorate
    }
    
    # Training level multipliers
    TRAINING_MULTIPLIERS = {
        1: 5,
        2: 10,
        3: 15,
        4: 20,
        5: 25,
    }
    
    @staticmethod
    def get_team_members(category_name, use_priority=True):
        """
        Get all team members in a category.
        
        Args:
            category_name: Group name (e.g., 'Lead Team')
            use_priority: Whether to order by priority
        
        Returns:
            QuerySet of User objects with related data
        """
        queryset = User.objects.filter(
            groups__name=category_name,
            is_active=True
        ).select_related(
            'profile',
            'team_profile'
        )
        
        if use_priority:
            queryset = queryset.order_by(
                'team_profile__priority',
                '-team_profile__total_points',
                'date_joined'
            )
        
        return queryset
    
    @staticmethod
    def assign_to_category(user, category_name, priority=0, is_manual=True, notes=''):
        """
        Assign user to team category using Django Groups.
        
        Args:
            user: User instance
            category_name: Group name (e.g., 'Lead Team')
            priority: Display priority (higher = shown first)
            is_manual: True for manual assignment, False for auto
            notes: Promotion/assignment notes
        """
        from accounts.models import TeamProfile
        
        # Get or create group
        group, created = Group.objects.get_or_create(name=category_name)
        
        # Clear existing team groups (user should only be in ONE team category)
        user.groups.filter(name__in=TeamService.ALL_CATEGORIES).delete()
        
        # Add to new group
        user.groups.add(group)
        
        # Update or create TeamProfile
        team_profile, created = TeamProfile.objects.get_or_create(user=user)
        team_profile.is_manually_assigned = is_manual
        team_profile.priority = priority
        team_profile.last_promoted = timezone.now()
        
        if notes:
            team_profile.promotion_notes = notes
        
        team_profile.save()
        
        logger.info(
            f"Assigned {user.username} to {category_name} "
            f"(manual={is_manual}, priority={priority})"
        )
    
    @staticmethod
    def calculate_total_points(user):
        """
        Calculate total points from all sources.
        
        Point Sources:
        1. Education (250-2,000 points)
        2. Task History (variable)
        3. Requirements (variable)
        4. Training (5-125 per training)
        5. Client Assessment (variable)
        
        Returns:
            Integer total points
        """
        education_pts = TeamService._calculate_education_points(user)
        task_pts = TeamService._calculate_task_points(user)
        requirement_pts = TeamService._calculate_requirement_points(user)
        training_pts = TeamService._calculate_training_points(user)
        assessment_pts = TeamService._calculate_assessment_points(user)
        
        total = (
            education_pts +
            task_pts +
            requirement_pts +
            training_pts +
            assessment_pts
        )
        
        logger.debug(
            f"Points for {user.username}: "
            f"edu={education_pts}, task={task_pts}, req={requirement_pts}, "
            f"train={training_pts}, assess={assessment_pts}, total={total}"
        )
        
        return total
    
    @staticmethod
    def _calculate_education_points(user):
        """Calculate education points from user profile"""
        try:
            education_level = user.profile.education
            return TeamService.EDUCATION_POINTS.get(education_level, 0)
        except Exception as e:
            logger.error(f"Error calculating education points for {user.username}: {e}")
            return 0
    
    @staticmethod
    def _calculate_task_points(user):
        """Calculate task history points"""
        try:
            from management.models import TaskHistory
            total = TaskHistory.objects.filter(
                employee_id=user
            ).aggregate(total=Sum('point'))['total']
            return total or 0
        except Exception as e:
            logger.error(f"Error calculating task points for {user.username}: {e}")
            return 0
    
    @staticmethod
    def _calculate_requirement_points(user):
        """Calculate requirement points (duration)"""
        try:
            from management.models import Requirement
            total = Requirement.objects.filter(
                assigned_to=user
            ).aggregate(total=Sum('duration'))['total']
            return total or 0
        except Exception as e:
            logger.error(f"Error calculating requirement points for {user.username}: {e}")
            return 0
    
    @staticmethod
    def _calculate_training_points(user):
        """Calculate training points"""
        try:
            from management.models import Training
            
            trainings = Training.objects.filter(presenter=user)
            total = 0
            
            for training in trainings:
                multiplier = TeamService.TRAINING_MULTIPLIERS.get(training.level, 0)
                total += training.level * multiplier
            
            return total
        except Exception as e:
            logger.error(f"Error calculating training points for {user.username}: {e}")
            return 0
    
    @staticmethod
    def _calculate_assessment_points(user):
        """Calculate client assessment points"""
        try:
            from professional_services.models import ClientAssessment
            
            latest = ClientAssessment.objects.filter(
                email=user.email
            ).order_by('-rating_date').first()
            
            return latest.totalpoints if latest else 0
        except Exception as e:
            logger.error(f"Error calculating assessment points for {user.username}: {e}")
            return 0
    
    @staticmethod
    def get_promotion_candidates():
        """
        Get trainees with 6,000+ points ready for promotion to Junior Analyst.
        
        Returns:
            QuerySet of User objects
        """
        return User.objects.filter(
            team_profile__is_manually_assigned=False,
            team_profile__total_points__gte=6000,
            is_active=True
        ).select_related('profile', 'team_profile').order_by(
            '-team_profile__total_points'
        )
    
    @staticmethod
    def auto_categorize_by_points(user):
        """
        Auto-assign user to appropriate group based on points.
        Only for non-manually assigned members (trainees).
        
        Args:
            user: User instance
        """
        try:
            team_profile = user.team_profile
        except:
            # No team profile, skip
            return
        
        # Skip manual members
        if team_profile.is_manually_assigned:
            logger.debug(f"Skipping {user.username} - manually assigned")
            return
        
        points = team_profile.total_points
        
        # Determine category based on points
        if points >= 5000 and points < 6000:
            category = 'Senior Trainee'
        elif points >= 4000 and points < 5000:
            category = 'Junior Trainee'
        else:
            category = 'Elementary'
        
        # Assign to group
        TeamService.assign_to_category(
            user,
            category,
            priority=0,
            is_manual=False,
            notes=f'Auto-categorized based on {points} points'
        )
        
        logger.info(
            f"Auto-categorized {user.username} to {category} ({points} points)"
        )
    
    @staticmethod
    def get_category_display_name(category_slug):
        """Get human-readable category name"""
        return category_slug  # Group names are already human-readable

