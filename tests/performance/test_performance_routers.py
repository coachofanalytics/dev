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




def performance_score_payload(
    number: int,
):
    return {
        "email": f"performance{number}@coda.com",
        "gender": "Male",
        "phone": f"+2547000{number:05d}",
        "address": "Performance Office",
        "city": "Nairobi",
        "state": "Nairobi County",
        "zipcode": "00100",
        "country": "Kenya",
        "category": "Performance",
        "sub_category": number + 1,
    }


def test_score_create_performance(client):
    start_time = time.perf_counter()

    response = client.post(
        "/accounts/scores/",
        json=performance_score_payload(1),
    )

    elapsed = (
        time.perf_counter() - start_time
    )

    assert response.status_code == 201
    assert elapsed < 2.0


def test_score_list_performance(client):
    for number in range(1, 21):
        response = client.post(
            "/accounts/scores/",
            json=performance_score_payload(
                number
            ),
        )

        assert response.status_code == 201

    start_time = time.perf_counter()

    response = client.get(
        "/accounts/scores/"
    )

    elapsed = (
        time.perf_counter() - start_time
    )

    assert response.status_code == 200
    assert len(response.json()) >= 20
    assert elapsed < 2.0


def test_score_detail_performance(client):
    create_response = client.post(
        "/accounts/scores/",
        json=performance_score_payload(50),
    )

    score_id = create_response.json()["id"]

    start_time = time.perf_counter()

    response = client.get(
        f"/accounts/scores/{score_id}"
    )

    elapsed = (
        time.perf_counter() - start_time
    )

    assert response.status_code == 200
    assert elapsed < 1.0