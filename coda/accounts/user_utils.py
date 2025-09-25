"""
User categorization utility functions for CustomerUser model
Computed user status functions to replace redundant boolean fields
"""

from django.utils import timezone
from django.urls import reverse, reverse_lazy
import logging
from accounts.choices import (
    UserCategory as CategoryChoices,
    ApplicantSubCategoryChoices,
    StudentSubCategoryChoices,
    ConsultantSubCategoryChoices,
    InvestorSubCategoryChoices,
    ExplorerSubCategoryChoices,
)

logger = logging.getLogger(__name__)

"""
Unified Navigation System for CODA
Combines category-level and subcategory-level navigation logic
"""


class NavigationService:
    """
    Centralized navigation service that handles both category and subcategory-level routing
    """

    def __init__(self):
        self.category_redirects = {
            CategoryChoices.APPLICANT: self._get_applicant_redirect,
            CategoryChoices.STUDENT: self._get_student_redirect,
            CategoryChoices.CONSULTANT: self._get_consultant_redirect,
            CategoryChoices.INVESTOR: self._get_investor_redirect,
            CategoryChoices.EXPLORER: self._get_explorer_redirect,
        }

    def get_redirect_url(self, user):
        """
        Main entry point for user redirection
        Handles email verification, admin checks, and category-based routing
        """
        # Email verification check (highest priority) - handled by allauth settings
        if not user.email_verified:
            return reverse("accounts:email-verification-notice", args=[user.id])

        # Admin redirects (second priority) - now go to unified dashboard
        if user.is_admin:
            return reverse_lazy("dashboard:unified_dashboard")

        # Staff redirects - now go to unified dashboard
        if user.is_staff:
            return reverse_lazy("dashboard:unified_dashboard")

        # Category-based redirects with subcategory consideration
        redirect_function = self.category_redirects.get(user.category)
        if redirect_function:
            return redirect_function(user)

        # Default fallback - now go to unified dashboard
        logger.warning(
            f"User {user.username} does not have a recognized category for redirection."
        )
        return reverse_lazy("dashboard:unified_dashboard")

    def _get_applicant_redirect(self, user):
        """Handle applicant category redirects with subcategory consideration"""
        if user.sub_category == ApplicantSubCategoryChoices.FULL_TIME:
            return reverse_lazy("application:interview")
        elif user.sub_category == ApplicantSubCategoryChoices.CONTRACT:
            return reverse_lazy("application:interview")
        elif user.sub_category == ApplicantSubCategoryChoices.INTERNSHIP:
            return reverse_lazy("application:interview")
        else:
            return reverse_lazy("application:interview")  # Default for applicants

    def _get_student_redirect(self, user):
        """Handle student category redirects with subcategory consideration"""
        # All students should go to unified dashboard with quick links for professional services
        return reverse_lazy("dashboard:unified_dashboard")

    def _get_consultant_redirect(self, user):
        """Handle consultant category redirects with subcategory consideration"""
        # All consultants should go to unified dashboard with professional services links
        return reverse_lazy("dashboard:unified_dashboard")

    def _get_investor_redirect(self, user):
        """Handle investor category redirects based on KCC membership and subcategory"""
        try:
            # Check if user is a KCC member
            is_kcc_member = self._check_kcc_membership(user)

            if is_kcc_member:
                # KCC members go to loan system for KCC benefits
                return reverse_lazy("finance:loan-home")

            # Non-KCC investors go to investment system based on subcategory
            if user.sub_category == InvestorSubCategoryChoices.ANGEL:
                return reverse_lazy("investing:investment_dashboard")  # Angel investors
            elif user.sub_category == InvestorSubCategoryChoices.VC:
                return reverse_lazy("investing:investment_dashboard")  # VC investors
            elif user.sub_category == InvestorSubCategoryChoices.PRIVATE:
                return reverse_lazy(
                    "investing:investment_dashboard"
                )  # Private equity investors
            elif user.sub_category == InvestorSubCategoryChoices.INDIVIDUAL:
                return reverse_lazy(
                    "investing:investment_dashboard"
                )  # Individual investors (non-KCC)
            else:
                return reverse_lazy(
                    "investing:investment_dashboard"
                )  # Default for investors

        except Exception as e:
            logger.error(
                f"Error determining investor redirect for user {user.username}: {e}"
            )
            # Fallback to investment system
            return reverse_lazy("investing:investment_dashboard")

    def _check_kcc_membership(self, user):
        """Check if user is a KCC member"""
        try:
            # Staff users are never KCC members
            if user.category == 2:  # Staff category
                return False

            if hasattr(user, "profile") and user.profile:
                profile = user.profile
                if profile.is_karen_country_club_member:
                    # Check if membership is not expired
                    if profile.kcc_membership_expiry:
                        from django.utils import timezone

                        return profile.kcc_membership_expiry >= timezone.now().date()
                    else:
                        # No expiry date, assume valid
                        return True
            return False
        except Exception as e:
            logger.error(f"Error checking KCC membership for user {user.username}: {e}")
            return False

    def _get_explorer_redirect(self, user):
        """Handle explorer category redirects with subcategory consideration"""
        # All explorers should go to unified dashboard with appropriate links
        return reverse_lazy("dashboard:unified_dashboard")

    def get_user_dashboard_url(self, user):
        """
        Get the appropriate dashboard URL for a user
        This is different from redirect URL - it's for navigation purposes
        """
        try:
            # All users now go to the unified dashboard
            return "dashboard:unified_dashboard"

        except Exception as e:
            logger.error(f"Error getting dashboard URL for user {user.username}: {e}")
            return "dashboard:unified_dashboard"

    def get_user_service_urls(self, user):
        """
        Get all relevant service URLs for a user based on their category/subcategory
        Useful for navigation menus
        """
        service_urls = {
            "dashboard": self.get_user_dashboard_url(user),
            "profile": reverse_lazy(
                "accounts:account-profile", kwargs={"username": user.username}
            ),
        }

        # Add category-specific services
        if user.category == CategoryChoices.STUDENT:
            service_urls.update(
                {
                    "training": reverse_lazy("professional_services:bitraining"),
                    "courses": reverse_lazy("professional_services:course"),
                    "progress": reverse_lazy("professional_services:training"),
                }
            )
        elif user.category == CategoryChoices.CONSULTANT:
            service_urls.update(
                {
                    "interview_prep": reverse_lazy(
                        "professional_services:interview_roles"
                    ),
                    "projects": reverse_lazy("professional_services:jobroles"),
                    "resumes": reverse_lazy("professional_services:prepquestions"),
                }
            )
        elif user.category == CategoryChoices.INVESTOR:
            service_urls.update(
                {
                    "loans": reverse_lazy("finance:loan-home"),
                    "investments": reverse_lazy("investing:investment_plan_list"),
                    "payments": reverse_lazy("finance:unified_method_selection"),
                }
            )
        elif user.category == CategoryChoices.EXPLORER:
            service_urls.update(
                {
                    "home": reverse_lazy("accounts:home"),
                    "about": reverse_lazy("main:about"),
                    "contact": reverse_lazy("main:contact"),
                }
            )

        return service_urls


# Create a singleton instance for easy import
navigation_service = NavigationService()


# Convenience functions for backward compatibility
def get_redirect_url(user):
    """Backward compatibility function"""
    return navigation_service.get_redirect_url(user)


def get_user_dashboard_url(user):
    """Backward compatibility function"""
    return navigation_service.get_user_dashboard_url(user)


def get_user_service_urls(user):
    """Backward compatibility function"""
    return navigation_service.get_user_service_urls(user)


def get_user_employment_status(user):
    """
    Compute employment status from category + subcategory + staff status
    Uses is_staff=True to designate employees (no separate Employee category)
    """
    # Priority 1: Check if user is staff (overrides category)
    if user.is_staff:
        if user.category == CategoryChoices.APPLICANT:
            if user.sub_category == ApplicantSubCategoryChoices.FULL_TIME:
                return "Full-time Employee"
            elif user.sub_category == ApplicantSubCategoryChoices.CONTRACT:
                return "Contract Employee"
            elif user.sub_category == ApplicantSubCategoryChoices.INTERNSHIP:
                return "Intern Employee"
            else:
                return "Employee (Promoted from Applicant)"
        elif user.category == CategoryChoices.STUDENT:
            return "Employee (Promoted from Student)"
        elif user.category == CategoryChoices.CONSULTANT:
            return "Employee (Promoted from Consultant)"
        else:
            return "Employee (Staff Member)"
    
    # Priority 2: Check category-based status for non-staff
    if user.category == CategoryChoices.APPLICANT:
        if user.sub_category == ApplicantSubCategoryChoices.FULL_TIME:
            return "Full-time Applicant"
        elif user.sub_category == ApplicantSubCategoryChoices.CONTRACT:
            return "Contract Applicant"
        elif user.sub_category == ApplicantSubCategoryChoices.INTERNSHIP:
            return "Internship Applicant"
        else:
            return "Applicant (Unspecified)"
    
    return "Not an Employee"


def get_user_client_status(user):
    """
    Compute client status from category
    Replaces is_client boolean field
    """
    if user.category == CategoryChoices.STUDENT:
        return "Active Student"
    elif user.category == CategoryChoices.CONSULTANT:
        return "Professional Client"
    elif user.category == CategoryChoices.INVESTOR:
        return "Financial Client"
    elif user.category == CategoryChoices.CONSULTANT:
        return "Partner"
    elif user.category == CategoryChoices.INVESTOR:
        return "Investor"
    elif user.category == CategoryChoices.EXPLORER:
        return "Visitor"
    return "Not a Client"


def get_user_applicant_status(user):
    """
    Compute applicant status from category
    Replaces is_applicant boolean field
    """
    if user.category == CategoryChoices.APPLICANT:
        return "Job Applicant"
    return "Not an Applicant"


def get_user_lifecycle_stage(user):
    """
    Compute lifecycle stage from last_login + date_joined
    No stored field needed - computed from existing data
    """
    if not user.last_login:
        return "Never Logged In"

    days_inactive = (timezone.now() - user.last_login).days

    if days_inactive > 365:
        return "Inactive (>1 year)"
    elif days_inactive > 90:
        return "Dormant (>3 months)"
    elif days_inactive > 30:
        return "Low Activity (>1 month)"
    elif days_inactive > 7:
        return "Active"
    else:
        return "Recently Active"


def should_auto_deactivate(user):
    """
    Compute deactivation status from existing data
    No stored field needed - computed from last_login
    """
    if not user.last_login:
        return False

    days_inactive = (timezone.now() - user.last_login).days
    return days_inactive > 365  # 1 year inactive


def get_user_engagement_score(user):
    """
    Compute engagement from existing data
    No stored field needed - computed from date_joined and last_login
    """
    if not user.last_login:
        return 0

    days_since_joined = (timezone.now() - user.date_joined).days
    days_since_last_login = (timezone.now() - user.last_login).days

    if days_since_joined == 0:
        return 100  # Just joined

    # Calculate engagement score based on login frequency
    login_frequency = days_since_joined / max(days_since_last_login, 1)
    return min(int(login_frequency * 100), 100)


def get_user_permissions(user):
    """
    Get user permissions based on category and subcategory
    """
    permissions = {
        "can_apply_jobs": user.category == CategoryChoices.APPLICANT,
        "can_access_courses": user.category == CategoryChoices.STUDENT,
        "can_access_finance": user.category
        in [CategoryChoices.INVESTOR, CategoryChoices.CONSULTANT],
        "can_access_management": user.is_staff,
        "can_access_analytics": user.is_staff
        or user.category == CategoryChoices.CONSULTANT,
        "can_access_investment": user.category == CategoryChoices.INVESTOR,
        "can_access_visitor_resources": user.category == CategoryChoices.EXPLORER,
    }

    # Additional permissions based on subcategory
    if user.category == CategoryChoices.EXPLORER:
        if user.sub_category == ExplorerSubCategoryChoices.RESEARCH:
            permissions["can_access_research_tools"] = True
        elif user.sub_category == ExplorerSubCategoryChoices.NETWORKING:
            permissions["can_access_networking_events"] = True

    return permissions


def get_user_display_info(user):
    """
    Get comprehensive user display information
    Uses computed functions instead of stored boolean fields
    """
    permissions = get_user_permissions(user)

    # Get category display name
    category_display = dict(CategoryChoices.choices).get(user.category, "Unknown")

    # Get subcategory display name based on category
    subcategory_display = "None"
    if user.sub_category:
        if user.category == CategoryChoices.APPLICANT:
            subcategory_display = dict(SubCategoryChoices.choices).get(
                user.sub_category, "Unknown"
            )
        elif user.category == CategoryChoices.STUDENT:
            subcategory_display = dict(StudentSubCategoryChoices.choices).get(
                user.sub_category, "Unknown"
            )
        elif user.category == CategoryChoices.CONSULTANT:
            subcategory_display = dict(ConsultantSubCategoryChoices.choices).get(
                user.sub_category, "Unknown"
            )
        elif user.category == CategoryChoices.INVESTOR:
            subcategory_display = dict(InvestorSubCategoryChoices.choices).get(
                user.sub_category, "Unknown"
            )
        elif user.category == CategoryChoices.PARTNER:
            subcategory_display = dict(ExplorerSubCategoryChoices.choices).get(
                user.sub_category, "Unknown"
            )
        elif user.category == CategoryChoices.INVESTOR:
            subcategory_display = dict(InvestorSubCategoryChoices.choices).get(
                user.sub_category, "Unknown"
            )
        elif user.category == CategoryChoices.VISITOR:
            subcategory_display = dict(ExplorerSubCategoryChoices.choices).get(
                user.sub_category, "Unknown"
            )

    return {
        "category": category_display,
        "subcategory": subcategory_display,
        "employment_status": permissions["employment_status"],
        "client_status": permissions["client_status"],
        "applicant_status": permissions["applicant_status"],
        "lifecycle_stage": permissions["lifecycle_stage"],
        "engagement_level": permissions["engagement_level"],
        "status": ", ".join(
            [
                "Active" if user.is_active else "Inactive",
                "Staff Member" if user.is_staff else "",
                "Admin" if getattr(user, "is_admin", False) else "",
                "Superuser" if user.is_superuser else "",
            ]
        )
        .strip()
        .replace("  ", " "),
        "member_since": user.date_joined.strftime("%B %Y"),
        "last_active": (
            user.last_login.strftime("%B %d, %Y") if user.last_login else "Never"
        ),
        "days_since_registration": (timezone.now() - user.date_joined).days,
        "days_inactive": (
            (timezone.now() - user.last_login).days if user.last_login else None
        ),
    }


def validate_user_category_combination(category, sub_category):
    """
    Validate category and subcategory combinations
    Ensures business logic consistency
    """
    if category == CategoryChoices.APPLICANT:
        valid_subcategories = [
            ApplicantSubCategoryChoices.FULL_TIME,
            ApplicantSubCategoryChoices.CONTRACT,
            ApplicantSubCategoryChoices.INTERNSHIP,
        ]
        if sub_category not in valid_subcategories:
            return (
                False,
                f"Applicants must have subcategory: {', '.join([str(s) for s in valid_subcategories])}",
            )

    elif category == CategoryChoices.STUDENT:
        valid_subcategories = [
            StudentSubCategoryChoices.DATA_ANALYTICS,
            StudentSubCategoryChoices.PROGRAMMING,
            StudentSubCategoryChoices.OTHER,
        ]
        if sub_category not in valid_subcategories:
            return (
                False,
                f"Students must have subcategory: {', '.join([str(s) for s in valid_subcategories])}",
            )

    elif category == CategoryChoices.CONSULTANT:
        valid_subcategories = [
            ConsultantSubCategoryChoices.TECHNICAL,
            ConsultantSubCategoryChoices.BUSINESS,
            ConsultantSubCategoryChoices.CAREER,
            ConsultantSubCategoryChoices.PROJECT,
        ]
        if sub_category not in valid_subcategories:
            return (
                False,
                f"Consultants must have subcategory: {', '.join([str(s) for s in valid_subcategories])}",
            )

    elif category == CategoryChoices.INVESTOR:
        valid_subcategories = [
            InvestorSubCategoryChoices.ANGEL,
            InvestorSubCategoryChoices.VC,
            InvestorSubCategoryChoices.PRIVATE,
            InvestorSubCategoryChoices.INDIVIDUAL,
        ]
        if sub_category not in valid_subcategories:
            return (
                False,
                f"Investors must have subcategory: {', '.join([str(s) for s in valid_subcategories])}",
            )

    elif category == CategoryChoices.EXPLORER:
        valid_subcategories = [
            ExplorerSubCategoryChoices.RESEARCH,
            ExplorerSubCategoryChoices.NETWORKING,
            ExplorerSubCategoryChoices.LEARNING,
            ExplorerSubCategoryChoices.PARTNERSHIP,
        ]
        if sub_category not in valid_subcategories:
            return (
                False,
                f"Explorers must have subcategory: {', '.join([str(s) for s in valid_subcategories])}",
            )

    return True, "Valid combination"


def get_user_activity_summary(user):
    """
    Get comprehensive user activity summary
    Computed from existing data without additional fields
    """
    if not user.last_login:
        return {
            "status": "Never Logged In",
            "activity_level": "None",
            "recommendation": "Send welcome email and encourage first login",
        }

    days_inactive = (timezone.now() - user.last_login).days
    days_since_joined = (timezone.now() - user.date_joined).days

    if days_inactive > 365:
        return {
            "status": "Inactive (>1 year)",
            "activity_level": "Critical",
            "recommendation": "Consider deactivation or re-engagement campaign",
        }
    elif days_inactive > 90:
        return {
            "status": "Dormant (>3 months)",
            "activity_level": "High",
            "recommendation": "Send re-engagement email with personalized content",
        }
    elif days_inactive > 30:
        return {
            "status": "Low Activity (>1 month)",
            "activity_level": "Medium",
            "recommendation": "Send monthly newsletter or activity reminder",
        }
    elif days_inactive > 7:
        return {
            "status": "Active",
            "activity_level": "Low",
            "recommendation": "Send weekly updates or relevant content",
        }
    else:
        return {
            "status": "Recently Active",
            "activity_level": "None",
            "recommendation": "Continue current engagement strategy",
        }


def get_user_learning_path(user):
    """
    Compute learning path from category + subcategory
    No stored field needed - computed from existing data
    """
    if user.category == CategoryChoices.STUDENT:
        if user.sub_category == StudentSubCategoryChoices.DATA_ANALYTICS_STUDENT:
            return "Data Analytics Path"
        elif user.sub_category == StudentSubCategoryChoices.PROGRAMMING_STUDENT:
            return "Programming Path"
        elif user.sub_category == StudentSubCategoryChoices.BUSINESS_STUDENT:
            return "Business Path"
        elif user.sub_category == StudentSubCategoryChoices.TECHNICAL_STUDENT:
            return "Technical Path"
        else:
            return "Student (Path Unspecified)"
    return "Not a Student"


def get_user_professional_service(user):
    """
    Compute professional service type from category + subcategory
    No stored field needed - computed from existing data
    """
    if user.category == CategoryChoices.CONSULTANT:
        if user.sub_category == ProfessionalSubCategoryChoices.JOB_SUPPORT_CLIENT:
            return "Job Support Service"
        elif user.sub_category == ProfessionalSubCategoryChoices.INTERVIEW_PREP_CLIENT:
            return "Interview Preparation"
        elif (
            user.sub_category == ProfessionalSubCategoryChoices.CAREER_COUNSELING_CLIENT
        ):
            return "Career Counseling"
        elif (
            user.sub_category
            == ProfessionalSubCategoryChoices.PROJECT_CONSULTING_CLIENT
        ):
            return "Project Consulting"
        else:
            return "Professional Service (Type Unspecified)"
    return "Not a Professional Client"


def get_user_financial_service(user):
    """
    Compute financial service type from category + subcategory
    No stored field needed - computed from existing data
    """
    if user.category == CategoryChoices.INVESTOR:
        if user.sub_category == FinancialSubCategoryChoices.PERSONAL_LOAN_CLIENT:
            return "Personal Loan Service"
        elif user.sub_category == FinancialSubCategoryChoices.BUSINESS_LOAN_CLIENT:
            return "Business Loan Service"
        elif user.sub_category == FinancialSubCategoryChoices.EDUCATION_LOAN_CLIENT:
            return "Education Loan Service"
        elif (
            user.sub_category == FinancialSubCategoryChoices.INVESTMENT_ADVISORY_CLIENT
        ):
            return "Investment Advisory"
        else:
            return "Financial Service (Type Unspecified)"
    return "Not a Financial Client"


def get_user_partnership_type(user):
    """
    Compute partnership type from category + subcategory
    No stored field needed - computed from existing data
    """
    if user.category == CategoryChoices.PARTNER:
        if user.sub_category == PartnerSubCategoryChoices.EDUCATIONAL_PARTNER:
            return "Educational Partnership"
        elif user.sub_category == PartnerSubCategoryChoices.UNIVERSITY_PARTNER:
            return "University Partnership"
        elif user.sub_category == PartnerSubCategoryChoices.CORPORATE_PARTNER:
            return "Corporate Partnership"
        elif user.sub_category == PartnerSubCategoryChoices.SOFTWARE_PARTNER:
            return "Software Partnership"
        else:
            return "Partnership (Type Unspecified)"
    return "Not a Partner"


def get_user_investment_type(user):
    """
    Compute investment type from category + subcategory
    No stored field needed - computed from existing data
    """
    if user.category == CategoryChoices.INVESTOR:
        if user.sub_category == InvestorSubCategoryChoices.ANGEL_INVESTOR:
            return "Angel Investment"
        elif user.sub_category == InvestorSubCategoryChoices.VENTURE_CAPITALIST:
            return "Venture Capital"
        elif user.sub_category == InvestorSubCategoryChoices.PRIVATE_EQUITY_INVESTOR:
            return "Private Equity"
        elif user.sub_category == InvestorSubCategoryChoices.INDIVIDUAL_INVESTOR:
            return "Individual Investment"
        else:
            return "Investment (Type Unspecified)"
    return "Not an Investor"


def get_user_visitor_purpose(user):
    """
    Compute visitor purpose from category + subcategory
    No stored field needed - computed from existing data
    """
    if user.category == CategoryChoices.VISITOR:
        if user.sub_category == VisitorSubCategoryChoices.INFORMATION_SEEKER:
            return "Information Seeking"
        elif user.sub_category == VisitorSubCategoryChoices.POTENTIAL_CLIENT:
            return "Potential Client"
        elif user.sub_category == VisitorSubCategoryChoices.INDUSTRY_PROFESSIONAL:
            return "Industry Professional"
        elif user.sub_category == VisitorSubCategoryChoices.STUDENT_EXPLORER:
            return "Student Explorer"
        else:
            return "Visitor (Purpose Unspecified)"
    return "Not a Visitor"


# Legacy mapping functions for backward compatibility
def get_legacy_category_mapping(old_category_id):
    """
    Map old category IDs to new category + subcategory combinations
    For migration purposes only
    """
    legacy_mapping = {
        1: (
            CategoryChoices.APPLICANT,
            ApplicantSubCategoryChoices.FULL_TIME,
        ),  # Job_Applicant
        2: (
            CategoryChoices.APPLICANT,
            ApplicantSubCategoryChoices.FULL_TIME,
        ),  # Coda_Staff_Member
        3: (
            CategoryChoices.CONSULTANT,
            ConsultantSubCategoryChoices.CAREER,
        ),  # Jobsupport
        4: (
            CategoryChoices.STUDENT,
            StudentSubCategoryChoices.DATA_ANALYTICS,
        ),  # Student
        5: (CategoryChoices.INVESTOR, InvestorSubCategoryChoices.ANGEL),  # Investor
        6: (CategoryChoices.EXPLORER, ExplorerSubCategoryChoices.RESEARCH),  # Vendor
        7: (
            CategoryChoices.EXPLORER,
            ExplorerSubCategoryChoices.LEARNING,
        ),  # General_User
    }
    return legacy_mapping.get(
        old_category_id,
        (CategoryChoices.APPLICANT, ApplicantSubCategoryChoices.FULL_TIME),
    )


def get_legacy_subcategory_mapping(old_subcategory_id):
    """
    Map old subcategory IDs to new ones
    For migration purposes only
    """
    legacy_mapping = {
        0: ApplicantSubCategoryChoices.FULL_TIME,  # No_selection
        1: ApplicantSubCategoryChoices.FULL_TIME,  # Full_time
        2: ApplicantSubCategoryChoices.CONTRACT,  # Contractual
        3: ApplicantSubCategoryChoices.INTERNSHIP,  # Agent
        4: StudentSubCategoryChoices.DATA_ANALYTICS,  # Short_Term
        5: StudentSubCategoryChoices.PROGRAMMING,  # Long_Term
        6: ApplicantSubCategoryChoices.FULL_TIME,  # Current
        7: ApplicantSubCategoryChoices.FULL_TIME,  # Prospective
        8: ConsultantSubCategoryChoices.CAREER,  # Other
        12: ExplorerSubCategoryChoices.RESEARCH,  # FREE_RESOURCE_USER
        13: ExplorerSubCategoryChoices.LEARNING,  # Premium_User
        14: ExplorerSubCategoryChoices.PARTNERSHIP,  # Corporate_Partner
        15: ExplorerSubCategoryChoices.PARTNERSHIP,  # Government_Partner
    }
    return legacy_mapping.get(old_subcategory_id, ApplicantSubCategoryChoices.FULL_TIME)
