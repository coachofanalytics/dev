# ==========================================================
# USER GROUPS ROUTER REGRESSION TESTS
# ==========================================================

from sqlmodel import select

from app import models


USER_GROUPS_LIST_URL = "/accounts/user-groups/pages/list"
USER_GROUPS_CREATE_URL = "/accounts/user-groups/pages/create"


def test_user_groups_list_route_is_not_treated_as_group_id(client):
    response = client.get(USER_GROUPS_LIST_URL)

    assert response.status_code == 200
    assert "User Groups Management" in response.text


def test_user_groups_empty_list_page_does_not_crash(client):
    response = client.get(USER_GROUPS_LIST_URL)

    assert response.status_code == 200


def test_user_groups_invalid_detail_id_returns_404(client):
    response = client.get(
        "/accounts/user-groups/pages/99999999"
    )

    assert response.status_code == 404


def test_user_groups_duplicate_name_returns_form_error(
    client,
    session,
):
    existing_group = models.UserGroups(
        name="Duplicate Test Group",
        description="Original group",
        is_active=True,
        is_featured=False,
    )

    session.add(existing_group)
    session.commit()

    response = client.post(
        USER_GROUPS_CREATE_URL,
        data={
            "name": "Duplicate Test Group",
            "description": "Duplicate group",
            "is_active": "on",
        },
    )

    assert response.status_code == 400
    assert "already exists" in response.text.lower()


def test_user_groups_duplicate_name_does_not_create_second_record(
    client,
    session,
):
    existing_group = models.UserGroups(
        name="Single Record Group",
        description="Original record",
        is_active=True,
        is_featured=False,
    )

    session.add(existing_group)
    session.commit()

    client.post(
        USER_GROUPS_CREATE_URL,
        data={
            "name": "Single Record Group",
            "description": "Attempted duplicate",
            "is_active": "on",
        },
    )

    statement = select(models.UserGroups).where(
        models.UserGroups.name == "Single Record Group"
    )

    matching_groups = session.exec(statement).all()

    assert len(matching_groups) == 1


def test_user_groups_duplicate_form_preserves_submitted_values(
    client,
    session,
):
    existing_group = models.UserGroups(
        name="Existing CODA Group",
        description="Existing record",
        is_active=True,
        is_featured=False,
    )

    session.add(existing_group)
    session.commit()

    response = client.post(
        USER_GROUPS_CREATE_URL,
        data={
            "name": "Existing CODA Group",
            "description": "Submitted test description",
            "is_active": "on",
            "is_featured": "on",
        },
    )

    assert response.status_code == 400
    assert "Existing CODA Group" in response.text
    assert "Submitted test description" in response.text