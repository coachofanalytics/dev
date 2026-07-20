from fastapi.testclient import TestClient


VALID_SCORE = {
    "email": "student@example.com",
    "gender": "Female",
    "phone": "+254712345678",
    "address": "123 Training Road",
    "city": "Nairobi",
    "state": "Nairobi County",
    "zipcode": "00100",
    "country": "Kenya",
    "category": "Training",
    "sub_category": 1,
}


def test_list_scores(client: TestClient):
    response = client.get("/accounts/scores/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_score(client: TestClient):
    response = client.post(
        "/accounts/scores/",
        json=VALID_SCORE,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["email"] == "student@example.com"
    assert data["city"] == "Nairobi"
    assert data["category"] == "Training"


def test_retrieve_score(client: TestClient):
    create_response = client.post(
        "/accounts/scores/",
        json=VALID_SCORE,
    )

    assert create_response.status_code == 201

    score_id = create_response.json()["id"]

    response = client.get(
        f"/accounts/scores/{score_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == score_id


def test_update_score(client: TestClient):
    create_response = client.post(
        "/accounts/scores/",
        json=VALID_SCORE,
    )

    score_id = create_response.json()["id"]

    response = client.patch(
        f"/accounts/scores/{score_id}",
        json={
            "city": "Mombasa",
            "state": "Mombasa County",
            "sub_category": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["city"] == "Mombasa"
    assert data["state"] == "Mombasa County"
    assert data["sub_category"] == 2


def test_invalid_email_is_rejected(client: TestClient):
    invalid_score = {
        **VALID_SCORE,
        "email": "invalid-email",
    }

    response = client.post(
        "/accounts/scores/",
        json=invalid_score,
    )

    assert response.status_code == 422


def test_missing_score_returns_404(client: TestClient):
    response = client.get(
        "/accounts/scores/99999"
    )

    assert response.status_code == 404