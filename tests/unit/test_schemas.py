# ==========================================================
# USER GROUPS SCHEMA TESTS
# ==========================================================

import pytest
from pydantic import ValidationError

from app import schemas


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