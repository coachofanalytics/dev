from django.db import models


# =========================
# TOP-LEVEL CATEGORIES
# =========================
class UserCategory(models.IntegerChoices):
    APPLICANT = 1  # Want to work for CODA
    STUDENT = 2  # Taking courses
    CONSULTANT = 3  # Professionals, advisors, service providers
    INVESTOR = 4  # Financial, strategic, KCC members
    EXPLORER = 5  # Visitors, researchers, networkers


# =========================
# SUBCATEGORIES PER CATEGORY
# IDs are compact and stable
# =========================
class ApplicantSubCategoryChoices(models.IntegerChoices):
    FULL_TIME = 1  # Full-time positions
    CONTRACT = 2  # Contract work
    INTERNSHIP = 3  # Internship opportunities


class StudentSubCategoryChoices(models.IntegerChoices):
    DATA_ANALYTICS = 1  # Data Science, Data Analysis courses
    PROGRAMMING = 2  # Programming, Software Development courses
    OTHER = 3  # Business/Technical/Other courses


class ConsultantSubCategoryChoices(models.IntegerChoices):
    TECHNICAL = 1  # Technical consulting, system architecture
    BUSINESS = 2  # Business strategy, operations consulting
    CAREER = 3  # Career development, job placement
    PROJECT = 4  # Project management, implementation


class InvestorSubCategoryChoices(models.IntegerChoices):
    ANGEL = 1, "Angel"  # Angel investors, early-stage
    VC = 2, "VC"  # Venture capital, growth-stage
    PRIVATE = 3, "Private"  # Private equity, mature companies
    INDIVIDUAL = 4, "Individual"  # Personal investors, KCC/loans


class ExplorerSubCategoryChoices(models.IntegerChoices):
    RESEARCH = 1  # Information seekers, prospects
    NETWORKING = 2  # Industry professionals, networking
    LEARNING = 3  # Exploring learning paths
    PARTNERSHIP = 4  # Exploring partnerships/business


# =========================
# HELPERS (safe for forms/views)
# =========================
CATEGORY_TO_SUBCATEGORY_ENUM = {
    UserCategory.APPLICANT: ApplicantSubCategoryChoices,
    UserCategory.STUDENT: StudentSubCategoryChoices,
    UserCategory.CONSULTANT: ConsultantSubCategoryChoices,
    UserCategory.INVESTOR: InvestorSubCategoryChoices,
    UserCategory.EXPLORER: ExplorerSubCategoryChoices,
}


def get_subcategory_choices(category_id: int):
    """
    Return (value, label) choices for a given category id.
    Works even if model fields don't bind choices= (no migration needed).
    """
    enum_cls = CATEGORY_TO_SUBCATEGORY_ENUM.get(category_id)
    return enum_cls.choices if enum_cls else ()


def get_category_display_name(category_id: int) -> str:
    return dict(UserCategory.choices).get(category_id, "Unknown")


def get_subcategory_display_name(category_id: int, subcategory_id: int) -> str:
    enum_cls = CATEGORY_TO_SUBCATEGORY_ENUM.get(category_id)
    if not enum_cls:
        return "Unknown"
    return dict(enum_cls.choices).get(subcategory_id, "Unknown")


# =========================
# BACKWARD COMPATIBILITY (optional)
# =========================
CategoryChoices = UserCategory
