from sqlmodel import select

from app.models import Score


def test_score_database_insert_and_select(
    session,
):
    score = Score(
        email="database@coda.com",
        phone="+254700000011",
        address="Database Office",
        city="Kisumu",
        state="Kisumu County",
        zipcode="40100",
        country="Kenya",
        category="Database",
        sub_category=501,
    )

    session.add(score)
    session.commit()

    statement = select(Score).where(
        Score.email == "database@coda.com"
    )

    result = session.exec(
        statement
    ).first()

    assert result is not None
    assert result.city == "Kisumu"