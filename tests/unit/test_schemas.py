# ==========================================================
# USER GROUPS SCHEMA TESTS
# ==========================================================

import pytest
from pydantic import ValidationError

from app import schemas


from app.schemas import ScoreCreate, ScoreUpdate


def test_user_groups_create_schema_accepts_valid_data():
    payload = schemas.UserGroupCreate(
        name="DC48KENYA",
        description="DC48 Kenya users",
        is_active=True,
        is_featured=False,
        user_ids=[],
    )

    assert payload.name == "DC48KENYA"
    assert payload.description == "DC48 Kenya users"
    assert payload.is_active is True
    assert payload.is_featured is False
    assert payload.user_ids == []


def test_user_groups_update_schema_accepts_valid_data():
    payload = schemas.UserGroupUpdate(
        name="Updated Group",
        description="Updated description",
        is_active=True,
        is_featured=True,
    )

    assert payload.name == "Updated Group"
    assert payload.description == "Updated description"
    assert payload.is_active is True
    assert payload.is_featured is True


def test_user_groups_status_schema_accepts_boolean():
    payload = schemas.UserGroupStatusUpdate(
        is_active=False,
    )

    assert payload.is_active is False


def test_user_groups_featured_schema_accepts_boolean():
    payload = schemas.UserGroupFeaturedUpdate(
        is_featured=True,
    )

    assert payload.is_featured is True


def test_user_groups_create_schema_rejects_missing_name():
    with pytest.raises(ValidationError):
        schemas.UserGroupCreate(
            description="Group without a name",
            is_active=True,
            is_featured=False,
            user_ids=[],
        )

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




def valid_score_data():
    return {
        "email": "admin@coda.com",
        "gender": "Male",
        "phone": "+254700000001",
        "address": "CODA Office",
        "city": "Nairobi",
        "state": "Nairobi County",
        "zipcode": "00100",
        "country": "Kenya",
        "category": "Finance",
        "sub_category": 101,
    }


def test_score_create_schema_accepts_valid_data():
    payload = ScoreCreate(
        **valid_score_data()
    )

    assert payload.email == "admin@coda.com"
    assert payload.phone == "+254700000001"
    assert payload.sub_category == 101


def test_score_create_schema_rejects_invalid_email():
    data = valid_score_data()
    data["email"] = "invalid-email"

    with pytest.raises(ValidationError):
        ScoreCreate(**data)


def test_score_create_schema_rejects_invalid_phone():
    data = valid_score_data()
    data["phone"] = "123"

    with pytest.raises(ValidationError):
        ScoreCreate(**data)


def test_score_create_schema_rejects_zero_sub_category():
    data = valid_score_data()
    data["sub_category"] = 0

    with pytest.raises(ValidationError):
        ScoreCreate(**data)


def test_score_update_schema_accepts_partial_data():
    payload = ScoreUpdate(
        city="Mombasa",
        category="Operations",
    )

    assert payload.city == "Mombasa"
    assert payload.category == "Operations"