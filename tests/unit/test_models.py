# ==========================================================
# USER GROUPS MODEL TESTS
# ==========================================================

from app import models
from app.models import (
    CustomerUser,
    Score,
    UserGroups,
)


def test_user_groups_model_accepts_valid_data():
    group = models.UserGroups(
        name="CODA Analytics",
        description="CODA Analytics operational group",
        is_active=True,
        is_featured=False,
    )

    assert group.name == "CODA Analytics"
    assert group.description == "CODA Analytics operational group"
    assert group.is_active is True
    assert group.is_featured is False


def test_user_groups_model_default_values():
    group = models.UserGroups(
        name="Training Group",
        description="CODA training group",
    )

    assert group.name == "Training Group"
    assert group.description == "CODA training group"


def test_user_groups_model_allows_featured_group():
    group = models.UserGroups(
        name="Featured Group",
        description="Featured CODA group",
        is_active=True,
        is_featured=True,
    )

    assert group.is_active is True
    assert group.is_featured is True

    from app import models


def test_customer_user_model_has_required_fields():
    customer_user = models.CustomerUser(
        username="brenda",
        email="brenda@example.com",
        city="Nairobi",
        state="Nairobi County",
        country="Kenya",
        category="applicant",
        is_admin=False,
        is_employee=False,
        is_client=False,
        is_applicant=True,
        resume_file="resumes/brenda.pdf",
    )

    assert customer_user.username == "brenda"
    assert customer_user.city == "Nairobi"
    assert customer_user.state == "Nairobi County"
    assert customer_user.country == "Kenya"
    assert customer_user.category == "applicant"
    assert customer_user.is_applicant is True
    assert customer_user.is_admin is False
    assert customer_user.resume_file.endswith(
        ".pdf"
    )


def test_customer_user_role_defaults_are_false():
    customer_user = models.CustomerUser(
        username="default-user",
        email="default@example.com",
        city="Nairobi",
        state="Nairobi County",
        country="Kenya",
        category="client",
        resume_file="resumes/default.pdf",
    )

    assert customer_user.is_admin is False
    assert customer_user.is_employee is False
    assert customer_user.is_client is False
    assert customer_user.is_applicant is False

from app.models import Score


def test_score_model_accepts_valid_data():
    score = Score(
        email="admin@coda.com",
        gender="Male",
        phone="+254700000001",
        address="CODA Office",
        city="Nairobi",
        state="Nairobi County",
        zipcode="00100",
        country="Kenya",
        category="Finance",
        sub_category=101,
    )

    assert score.email == "admin@coda.com"
    assert score.city == "Nairobi"
    assert score.category == "Finance"
    assert score.sub_category == 101


def test_score_model_allows_optional_gender():
    score = Score(
        email="client@coda.com",
        gender=None,
        phone="+254700000002",
        address="Westlands",
        city="Nairobi",
        state="Nairobi County",
        zipcode="00100",
        country="Kenya",
        category="Client",
        sub_category=201,
    )

    assert score.gender is None


def test_score_model_has_default_timestamps():
    score = Score(
        email="employee@coda.com",
        phone="+254700000003",
        address="Kitale Office",
        city="Kitale",
        state="Trans Nzoia",
        zipcode="30200",
        country="Kenya",
        category="Employee",
        sub_category=301,
    )

    assert score.created_at is not None
    assert score.updated_at is not None