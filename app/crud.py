from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app import models, schemas
from app.services.customer_user_service import validate_roles


def get_search_record(db: Session, record_id: int):
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
    total_records = len(records)
    uploaded_records = len([record for record in records if record.uploaded])
    return {
        "total_records": total_records,
        "uploaded_records": uploaded_records,
        "pending_records": total_records - uploaded_records,
    }


def create_search_record(db: Session, record: schemas.SearchRecordCreate):
    db_record = models.SearchRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def delete_search_record(db: Session, record_id: int):
    db_record = db.get(models.SearchRecord, record_id)
    if db_record is None:
        return None
    db.delete(db_record)
    db.commit()
    return db_record


# SCORE CRUD

def create_score(db: Session, score_data: schemas.ScoreCreate):
    db_score = models.Score(**score_data.model_dump())
    db.add(db_score)
    try:
        db.commit()
        db.refresh(db_score)
    except Exception:
        db.rollback()
        raise
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
        statement = statement.where(models.Score.email.contains(email))
    if gender:
        statement = statement.where(models.Score.gender == gender)
    if city:
        statement = statement.where(models.Score.city.contains(city))
    if state:
        statement = statement.where(models.Score.state.contains(state))
    if country:
        statement = statement.where(models.Score.country.contains(country))
    if category:
        statement = statement.where(models.Score.category == category)
    if sub_category is not None:
        statement = statement.where(models.Score.sub_category == sub_category)

    statement = (
        statement.order_by(models.Score.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.exec(statement).all()


def get_score(db: Session, score_id: int):
    return db.get(models.Score, score_id)


def get_score_or_404(db: Session, score_id: int) -> models.Score:
    score = get_score(db, score_id)
    if score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score not found.",
        )
    return score


def update_score(db: Session, score_id: int, score_data: schemas.ScoreUpdate):
    db_score = get_score(db, score_id)
    if db_score is None:
        return None

    update_data = score_data.model_dump(exclude_unset=True)
    for field_name, field_value in update_data.items():
        setattr(db_score, field_name, field_value)

    db_score.updated_at = datetime.now(timezone.utc)
    db.add(db_score)
    try:
        db.commit()
        db.refresh(db_score)
    except Exception:
        db.rollback()
        raise
    return db_score


def delete_score(
    db: Session,
    score_id: int,
):
    score = db.get(
        models.Score,
        score_id,
    )

    if score is None:
        return None

    db.delete(score)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return score


# USER GROUP CRUD

def get_group_or_404(db: Session, group_id: int):
    group = db.get(models.UserGroups, group_id)
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found.",
        )
    return group


def get_user_or_404(db: Session, user_id: int):
    user = db.get(models.CustomerUser, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


def validate_group_status(is_active: bool, is_featured: bool):
    if is_featured and not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An inactive group cannot be featured.",
        )


def create_user_group(db: Session, payload: schemas.UserGroupCreate):
    existing_group = db.exec(
        select(models.UserGroups).where(models.UserGroups.name == payload.name)
    ).first()
    if existing_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A group with this name already exists.",
        )

    validate_group_status(payload.is_active, payload.is_featured)

    group = models.UserGroups(
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
        is_featured=payload.is_featured,
    )

    if payload.user_ids:
        group.users = [get_user_or_404(db, user_id) for user_id in payload.user_ids]

    db.add(group)
    try:
        db.commit()
        db.refresh(group)
    except Exception:
        db.rollback()
        raise
    return group


def add_user_to_group(db: Session, group_id: int, user_id: int):
    group = get_group_or_404(db, group_id)
    user = get_user_or_404(db, user_id)

    if user in group.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already assigned to this group.",
        )

    group.users.append(user)
    db.add(group)
    db.commit()
    db.refresh(group)
    _ = group.users
    return group


def update_user_group(db: Session, group_id: int, payload: schemas.UserGroupUpdate):
    group = get_group_or_404(db, group_id)
    update_data = payload.model_dump(exclude_unset=True)

    new_name = update_data.get("name")
    if new_name and new_name != group.name:
        existing_group = db.exec(
            select(models.UserGroups).where(models.UserGroups.name == new_name)
        ).first()
        if existing_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A group with this name already exists.",
            )

    validate_group_status(
        update_data.get("is_active", group.is_active),
        update_data.get("is_featured", group.is_featured),
    )

    user_ids = update_data.pop("user_ids", None)
    for field_name, value in update_data.items():
        setattr(group, field_name, value)

    if user_ids is not None:
        group.users = [get_user_or_404(db, user_id) for user_id in user_ids]

    db.add(group)
    try:
        db.commit()
        db.refresh(group)
    except Exception:
        db.rollback()
        raise
    _ = group.users
    return group


def delete_user_group(db: Session, group_id: int):
    group = get_group_or_404(db, group_id)
    group.users.clear()
    db.add(group)
    db.commit()
    db.delete(group)
    db.commit()


# CUSTOMER USER CRUD

def get_customer_user(db: Session, customer_user_id: int) -> models.CustomerUser | None:
    return db.get(models.CustomerUser, customer_user_id)


def get_customer_user_or_404(db: Session, customer_user_id: int) -> models.CustomerUser:
    customer_user = get_customer_user(db, customer_user_id)
    if customer_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer user not found.",
        )
    return customer_user


def get_customer_user_by_username(db: Session, username: str) -> models.CustomerUser | None:
    statement = select(models.CustomerUser).where(
        models.CustomerUser.username == username
    )
    return db.exec(statement).first()


def get_customer_user_by_email(db: Session, email: str) -> models.CustomerUser | None:
    statement = select(models.CustomerUser).where(
        models.CustomerUser.email == email
    )
    return db.exec(statement).first()


def list_customer_users(
    db: Session,
    *,
    city: str | None = None,
    state_name: str | None = None,
    country: str | None = None,
    category: str | None = None,
    is_admin: bool | None = None,
    is_employee: bool | None = None,
    is_client: bool | None = None,
    is_applicant: bool | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[models.CustomerUser]:
    statement = select(models.CustomerUser)

    if city:
        statement = statement.where(models.CustomerUser.city == city)
    if state_name:
        statement = statement.where(models.CustomerUser.state == state_name)
    if country:
        statement = statement.where(models.CustomerUser.country == country)
    if category:
        statement = statement.where(models.CustomerUser.category == category)
    if is_admin is not None:
        statement = statement.where(models.CustomerUser.is_admin == is_admin)
    if is_employee is not None:
        statement = statement.where(models.CustomerUser.is_employee == is_employee)
    if is_client is not None:
        statement = statement.where(models.CustomerUser.is_client == is_client)
    if is_applicant is not None:
        statement = statement.where(models.CustomerUser.is_applicant == is_applicant)

    statement = (
        statement.order_by(models.CustomerUser.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.exec(statement).all())


def create_customer_user(
    db: Session,
    payload: schemas.CustomerUserCreate,
    resume_path: str,
) -> models.CustomerUser:
    if get_customer_user_by_username(db, payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The username already exists.",
        )

    if get_customer_user_by_email(db, str(payload.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The email address already exists.",
        )

    validate_roles(
        is_admin=payload.is_admin,
        is_employee=payload.is_employee,
        is_client=payload.is_client,
        is_applicant=payload.is_applicant,
    )

    customer_user = models.CustomerUser(
        username=payload.username,
        email=str(payload.email),
        city=payload.city,
        state=payload.state,
        country=payload.country,
        category=payload.category,
        is_admin=payload.is_admin,
        is_employee=payload.is_employee,
        is_client=payload.is_client,
        is_applicant=payload.is_applicant,
        is_active=payload.is_active,
        resume_file=resume_path,
    )

    db.add(customer_user)
    try:
        db.commit()
        db.refresh(customer_user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A customer user with this username or email already exists.",
        ) from exc
    except Exception:
        db.rollback()
        raise

    return customer_user


def update_customer_user(
    db: Session,
    customer_user: models.CustomerUser,
    payload: schemas.CustomerUserUpdate,
    resume_path: str | None = None,
) -> models.CustomerUser:
    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)

    username = update_data.get("username")
    if username and username != customer_user.username:
        if get_customer_user_by_username(db, username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The username already exists.",
            )

    email = update_data.get("email")
    if email:
        email = str(email)
        update_data["email"] = email

    if email and email != customer_user.email:
        if get_customer_user_by_email(db, email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The email address already exists.",
            )

    for field_name, value in update_data.items():
        setattr(customer_user, field_name, value)

    if resume_path:
        customer_user.resume_file = resume_path

    validate_roles(
        is_admin=customer_user.is_admin,
        is_employee=customer_user.is_employee,
        is_client=customer_user.is_client,
        is_applicant=customer_user.is_applicant,
    )

    customer_user.updated_at = datetime.now(timezone.utc)
    db.add(customer_user)

    try:
        db.commit()
        db.refresh(customer_user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A customer user with this username or email already exists.",
        ) from exc
    except Exception:
        db.rollback()
        raise

    return customer_user


def delete_customer_user(db: Session, customer_user: models.CustomerUser) -> None:
    db.delete(customer_user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise