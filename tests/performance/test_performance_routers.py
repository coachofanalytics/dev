# ==========================================================
# USER GROUPS ROUTER PERFORMANCE TESTS
# ==========================================================

import time

from app import models


USER_GROUPS_LIST_URL = "/accounts/user-groups/pages/list"


def test_user_groups_list_page_performance(
    client,
    session,
):
    groups = [
        models.UserGroups(
            name=f"Performance Group {number}",
            description=f"Performance group number {number}",
            is_active=True,
            is_featured=False,
        )
        for number in range(1, 101)
    ]

    session.add_all(groups)
    session.commit()

    start_time = time.perf_counter()

    response = client.get(USER_GROUPS_LIST_URL)

    elapsed_time = time.perf_counter() - start_time

    assert response.status_code == 200
    assert elapsed_time < 2.0


def test_user_groups_repeated_list_requests(
    client,
    session,
):
    groups = [
        models.UserGroups(
            name=f"Repeated Group {number}",
            description="Repeated request test",
            is_active=True,
            is_featured=False,
        )
        for number in range(1, 21)
    ]

    session.add_all(groups)
    session.commit()

    start_time = time.perf_counter()

    for _ in range(10):
        response = client.get(USER_GROUPS_LIST_URL)
        assert response.status_code == 200

    elapsed_time = time.perf_counter() - start_time

    assert elapsed_time < 5.0