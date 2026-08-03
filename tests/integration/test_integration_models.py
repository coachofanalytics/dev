from app.models import Score


def test_score_model_can_be_saved_to_database(
    session,
):
    score = Score(
        email="integration@coda.com",
        gender="Female",
        phone="+254700000010",
        address="Integration Office",
        city="Nakuru",
        state="Nakuru County",
        zipcode="20100",
        country="Kenya",
        category="Integration",
        sub_category=401,
    )

    session.add(score)
    session.commit()
    session.refresh(score)

    assert score.id is not None
    assert score.email == "integration@coda.com"