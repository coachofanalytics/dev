from sqlmodel import Session, select
from . import models, schemas, database
def get_search_records(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    topic: str | None = None,
    keyword: str | None = None,
    uploaded: bool | None = None,
    sort_by: str = "newest"
):
    statement = select(models.SearchRecord)

    if topic:
        statement = statement.where(models.SearchRecord.topic.contains(topic))

    if keyword:
        statement = statement.where(models.SearchRecord.question.contains(keyword))

    if uploaded is not None:
        statement = statement.where(models.SearchRecord.uploaded == uploaded)

    if sort_by == "oldest":
        statement = statement.order_by(models.SearchRecord.created_at.asc())
    else:
        statement = statement.order_by(models.SearchRecord.created_at.desc())

    statement = statement.offset(skip).limit(limit)

    return db.exec(statement).all()

def get_search_stats(db: Session):
    records = db.exec(select(models.SearchRecord)).all()

    total = len(records)
    uploaded = len([r for r in records if r.uploaded])
    pending = total - uploaded

    return {
        "total_records": total,
        "uploaded_records": uploaded,
        "pending_records": pending
    }

def create_search_record(db: Session, record: schemas.SearchRecordCreate):
    db_record = models.SearchRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record