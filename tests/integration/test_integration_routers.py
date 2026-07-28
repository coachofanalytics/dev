# ==========================================================
# USER GROUPS ROUTER INTEGRATION TESTS
# ==========================================================

from sqlmodel import select

from app import models


USER_GROUPS_LIST_URL = "/accounts/user-groups/pages/list"
USER_GROUPS_CREATE_URL = "/accounts/user-groups/pages/create"


def test_user_groups_list_page_returns_200(client):
    response = client.get(USER_GROUPS_LIST_URL)

    assert response.status_code == 200
    assert "User Groups Management" in response.text


def test_user_groups_create_page_returns_200(client):
    response = client.get(USER_GROUPS_CREATE_URL)

    assert response.status_code == 200
    assert "Create New Group" in response.text


def test_user_groups_create_from_html_form(client, session):
    response = client.post(
        USER_GROUPS_CREATE_URL,
        data={
            "name": "CODA Test Group",
            "description": "Created during integration testing",
            "is_active": "on",
            "is_featured": "on",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == USER_GROUPS_LIST_URL

    statement = select(models.UserGroups).where(
        models.UserGroups.name == "CODA Test Group"
    )

    group = session.exec(statement).first()

    assert group is not None
    assert group.name == "CODA Test Group"
    assert group.description == "Created during integration testing"
    assert group.is_active is True
    assert group.is_featured is True


def test_user_groups_created_group_appears_on_list(client):
    create_response = client.post(
        USER_GROUPS_CREATE_URL,
        data={
            "name": "Financial Training Group",
            "description": "Financial training users",
            "is_active": "on",
        },
        follow_redirects=False,
    )

    assert create_response.status_code == 303

    list_response = client.get(USER_GROUPS_LIST_URL)

    assert list_response.status_code == 200
    assert "Financial Training Group" in list_response.text


def test_user_groups_detail_page(client, session):
    group = models.UserGroups(
        name="CODA Detail Group",
        description="Group detail test",
        is_active=True,
        is_featured=False,
    )

    session.add(group)
    session.commit()
    session.refresh(group)

    response = client.get(
        f"/accounts/user-groups/pages/{group.id}"
    )

    assert response.status_code == 200
    assert "CODA Detail Group" in response.text


def test_user_groups_update_from_html_form(client, session):
    group = models.UserGroups(
        name="Old Group Name",
        description="Old description",
        is_active=True,
        is_featured=False,
    )

    session.add(group)
    session.commit()
    session.refresh(group)

    response = client.post(
        f"/accounts/user-groups/pages/{group.id}/edit",
        data={
            "name": "Updated Group Name",
            "description": "Updated description",
            "is_active": "on",
            "is_featured": "on",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        f"/accounts/user-groups/pages/{group.id}"
    )

    session.expire_all()

    updated_group = session.get(
        models.UserGroups,
        group.id,
    )

    assert updated_group is not None
    assert updated_group.name == "Updated Group Name"
    assert updated_group.description == "Updated description"
    assert updated_group.is_active is True
    assert updated_group.is_featured is True


def test_user_groups_delete_from_html_form(client, session):
    group = models.UserGroups(
        name="Temporary Test Group",
        description="This group will be deleted",
        is_active=True,
        is_featured=False,
    )

    session.add(group)
    session.commit()
    session.refresh(group)

    group_id = group.id

    response = client.post(
        f"/accounts/user-groups/pages/{group_id}/delete",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == USER_GROUPS_LIST_URL

    session.expire_all()

    deleted_group = session.get(
        models.UserGroups,
        group_id,
    )

    assert deleted_group is None