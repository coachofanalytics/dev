# ==========================================================
# USER GROUPS MODEL TESTS
# ==========================================================

from app import models


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