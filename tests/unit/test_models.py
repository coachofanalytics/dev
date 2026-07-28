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