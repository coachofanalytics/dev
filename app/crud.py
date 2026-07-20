from sqlmodel import Session, select

from . import models, schemas
from datetime import datetime, timezone


def get_search_record(
    db: Session,
    record_id: int,
):
    """Return one search record by ID."""
    statement = select(models.SearchRecord).where(
        models.SearchRecord.id == record_id
    )

    return db.exec(statement).first()


def get_search_records(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    topic: str | None = None,
    keyword: str | None = None,
    uploaded: bool | None = None,
    sort_by: str = "newest",
):
    """Return search records with optional filtering and pagination."""
    statement = select(models.SearchRecord)

    if topic:
        statement = statement.where(
            models.SearchRecord.topic.contains(topic)
        )

    if keyword:
        statement = statement.where(
            models.SearchRecord.question.contains(keyword)
        )

    if uploaded is not None:
        statement = statement.where(
            models.SearchRecord.uploaded == uploaded
        )

    if sort_by == "oldest":
        statement = statement.order_by(
            models.SearchRecord.created_at.asc()
        )
    else:
        statement = statement.order_by(
            models.SearchRecord.created_at.desc()
        )

    statement = statement.offset(skip).limit(limit)

    return db.exec(statement).all()


def get_search_stats(db: Session):
    """Return summary statistics for search records."""
    records = db.exec(
        select(models.SearchRecord)
    ).all()

    total_records = len(records)
    uploaded_records = len(
        [record for record in records if record.uploaded]
    )
    pending_records = total_records - uploaded_records

    return {
        "total_records": total_records,
        "uploaded_records": uploaded_records,
        "pending_records": pending_records,
    }


def create_search_record(
    db: Session,
    record: schemas.SearchRecordCreate,
):
    """Create and save a search record."""
    db_record = models.SearchRecord(
        **record.model_dump()
    )

    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    return db_record



def delete_search_record(
    db: Session,
    record_id: int,
):
    db_record = db.get(models.SearchRecord, record_id)

    if db_record is None:
        return None

    db.delete(db_record)
    db.commit()

    return db_record






def create_score(
    db: Session,
    score_data: schemas.ScoreCreate,
):
    db_score = models.Score(
        **score_data.model_dump()
    )

    db.add(db_score)
    db.commit()
    db.refresh(db_score)

    return db_score


def get_scores(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    email: str | None = None,
    gender: str | None = None,
    city: str | None = None,
    state: str | None = None,
    country: str | None = None,
    category: str | None = None,
    sub_category: int | None = None,
):
    statement = select(models.Score)

    if email:
        statement = statement.where(
            models.Score.email.contains(email)
        )

    if gender:
        statement = statement.where(
            models.Score.gender == gender
        )

    if city:
        statement = statement.where(
            models.Score.city.contains(city)
        )

    if state:
        statement = statement.where(
            models.Score.state.contains(state)
        )

    if country:
        statement = statement.where(
            models.Score.country.contains(country)
        )

    if category:
        statement = statement.where(
            models.Score.category == category
        )

    if sub_category is not None:
        statement = statement.where(
            models.Score.sub_category == sub_category
        )

    statement = (
        statement
        .order_by(models.Score.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    return db.exec(statement).all()


def get_score(
    db: Session,
    score_id: int,
):
    return db.get(
        models.Score,
        score_id,
    )


def update_score(
    db: Session,
    score_id: int,
    score_data: schemas.ScoreUpdate,
):
    db_score = db.get(
        models.Score,
        score_id,
    )

    if db_score is None:
        return None

    update_data = score_data.model_dump(
        exclude_unset=True
    )

    for field_name, field_value in update_data.items():
        setattr(
            db_score,
            field_name,
            field_value,
        )

    db_score.updated_at = datetime.now(
        timezone.utc
    )

    db.add(db_score)
    db.commit()
    db.refresh(db_score)

    return db_score