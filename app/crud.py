from sqlmodel import Session, select

from . import models, schemas
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlmodel import Session

from app import models

from sqlmodel import Session, select

from app import models, schemas


def get_group_or_404(
    db: Session,
    group_id: int,
):
    group = db.get(
        models.UserGroups,
        group_id,
    )

    if not group:
        raise HTTPException(
            status_code=404,
            detail="Group not found",
        )

    return group


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

    from fastapi import HTTPException
from sqlmodel import Session, select

from app import models, schemas


def create_user_group(
    db: Session,
    payload: schemas.UserGroupCreate,
):
    existing_group = db.exec(
        select(models.UserGroups).where(
            models.UserGroups.name == payload.name
        )
    ).first()

    if existing_group:
        raise HTTPException(
            status_code=400,
            detail="A group with this name already exists.",
        )

    if payload.is_featured and not payload.is_active:
        raise HTTPException(
            status_code=400,
            detail="An inactive group cannot be featured.",
        )

    group = models.UserGroups(
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
        is_featured=payload.is_featured,
    )

    if payload.user_ids:
        users = []

        for user_id in payload.user_ids:
            user = db.get(
                models.CustomerUser,
                user_id,
            )

            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=f"User with ID {user_id} was not found.",
                )

            users.append(user)

        group.users = users

    db.add(group)
    db.commit()
    db.refresh(group)

    return group

    from fastapi import HTTPException
from sqlmodel import Session, select

from app import models, schemas


def create_customer_user(
    db: Session,
    payload: schemas.CustomerUserCreate,
):
    existing_username = db.exec(
        select(models.CustomerUser).where(
            models.CustomerUser.username == payload.username
        )
    ).first()

    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="A user with this username already exists.",
        )

    existing_email = db.exec(
        select(models.CustomerUser).where(
            models.CustomerUser.email == payload.email
        )
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )

    user = models.CustomerUser(
        username=payload.username,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        is_active=payload.is_active,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
from fastapi import HTTPException
from sqlmodel import Session

from app import models


def get_user_or_404(
    db: Session,
    user_id: int,
):
    user = db.get(
        models.CustomerUser,
        user_id,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user


def add_user_to_group(
    db: Session,
    group_id: int,
    user_id: int,
):
    group = get_group_or_404(
        db,
        group_id,
    )

    user = get_user_or_404(
        db,
        user_id,
    )

    if user in group.users:
        raise HTTPException(
            status_code=400,
            detail="User is already assigned to this group.",
        )

    group.users.append(user)

    db.add(group)
    db.commit()
    db.refresh(group)

    _ = group.users

    return group
from fastapi import HTTPException


def validate_group_status(
    is_active: bool,
    is_featured: bool,
):
    if is_featured and not is_active:
        raise HTTPException(
            status_code=400,
            detail="An inactive group cannot be featured.",
        )


from fastapi import HTTPException
from sqlmodel import Session, select

from app import models, schemas


def update_user_group(
    db: Session,
    group_id: int,
    payload: schemas.UserGroupUpdate,
):
    group = get_group_or_404(
        db,
        group_id,
    )

    update_data = (
        payload.model_dump(exclude_unset=True)
        if hasattr(payload, "model_dump")
        else payload.dict(exclude_unset=True)
    )

    new_name = update_data.get("name")

    if new_name and new_name != group.name:
        existing_group = db.exec(
            select(models.UserGroups).where(
                models.UserGroups.name == new_name
            )
        ).first()

        if existing_group:
            raise HTTPException(
                status_code=400,
                detail="A group with this name already exists.",
            )

    final_is_active = update_data.get(
        "is_active",
        group.is_active,
    )

    final_is_featured = update_data.get(
        "is_featured",
        group.is_featured,
    )

    validate_group_status(
        final_is_active,
        final_is_featured,
    )

    user_ids = update_data.pop(
        "user_ids",
        None,
    )

    for field_name, value in update_data.items():
        setattr(
            group,
            field_name,
            value,
        )

    if user_ids is not None:
        users = []

        for user_id in user_ids:
            user = get_user_or_404(
                db,
                user_id,
            )
            users.append(user)

        group.users = users

    db.add(group)
    db.commit()
    db.refresh(group)

    _ = group.users

    return group
from sqlmodel import Session

from app import models


def delete_user_group(
    db: Session,
    group_id: int,
):
    group = get_group_or_404(
        db,
        group_id,
    )

    # Clear relationships first.
    group.users.clear()

    db.add(group)
    db.commit()

    db.delete(group)
    db.commit()