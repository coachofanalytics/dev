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

    
def customer_user_form(
    username: str,
    email: str,
):
    return {
        "username": username,
        "email": email,
        "city": "Nairobi",
        "state": "Nairobi County",
        "country": "Kenya",
        "category": "applicant",
        "is_admin": "false",
        "is_employee": "false",
        "is_client": "false",
        "is_applicant": "true",
    }


def customer_user_resume():
    return {
        "resume_file": (
            "resume.pdf",
            b"%PDF-1.4 regression resume",
            "application/pdf",
        ),
    }


def test_customer_user_create_requires_admin(
    client,
):
    response = client.post(
        "/accounts/customer-users/",
        data=customer_user_form(
            "unauthorized-user",
            "unauthorized@example.com",
        ),
        files=customer_user_resume(),
    )

    assert response.status_code == 403


def test_customer_user_duplicate_username_is_rejected(
    client,
):
    first_response = client.post(
        "/accounts/customer-users/",
        headers={
            "X-Admin": "true",
        },
        data=customer_user_form(
            "duplicate-user",
            "first@example.com",
        ),
        files=customer_user_resume(),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/accounts/customer-users/",
        headers={
            "X-Admin": "true",
        },
        data=customer_user_form(
            "duplicate-user",
            "second@example.com",
        ),
        files=customer_user_resume(),
    )

    assert second_response.status_code == 409
    assert "already exists" in (
        second_response.json()["detail"].lower()
    )


def test_customer_user_duplicate_email_is_rejected(
    client,
):
    first_response = client.post(
        "/accounts/customer-users/",
        headers={
            "X-Admin": "true",
        },
        data=customer_user_form(
            "first-email-user",
            "duplicate-email@example.com",
        ),
        files=customer_user_resume(),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/accounts/customer-users/",
        headers={
            "X-Admin": "true",
        },
        data=customer_user_form(
            "second-email-user",
            "duplicate-email@example.com",
        ),
        files=customer_user_resume(),
    )

    assert second_response.status_code == 409
    assert "already exists" in (
        second_response.json()["detail"].lower()
    )


def test_customer_user_invalid_resume_is_rejected(
    client,
):
    response = client.post(
        "/accounts/customer-users/",
        headers={
            "X-Admin": "true",
        },
        data=customer_user_form(
            "invalid-resume-user",
            "invalid-resume@example.com",
        ),
        files={
            "resume_file": (
                "resume.exe",
                b"invalid file",
                "application/octet-stream",
            ),
        },
    )

    assert response.status_code == 400


def test_customer_user_without_role_is_rejected(
    client,
):
    form_data = customer_user_form(
        "no-role-user",
        "no-role@example.com",
    )

    form_data.update(
        {
            "is_admin": "false",
            "is_employee": "false",
            "is_client": "false",
            "is_applicant": "false",
        }
    )

    response = client.post(
        "/accounts/customer-users/",
        headers={
            "X-Admin": "true",
        },
        data=form_data,
        files=customer_user_resume(),
    )

    assert response.status_code in {
        400,
        422,
    }