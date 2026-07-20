from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session, select

from app import crud, models, schemas
from app.database import get_db
from app.dependencies.permissions import require_admin


router = APIRouter(
    prefix="/accounts/user-groups",
    tags=["User Groups Management"],
)


@router.post(
    "/users",
    response_model=schemas.CustomerUserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_user(
    payload: schemas.CustomerUserCreate,
    db: Session = Depends(get_db),
):
    return crud.create_customer_user(
        db,
        payload,
    )


@router.get(
    "/active",
    response_model=list[schemas.ActiveGroupResponse],
)
def list_active_groups(
    db: Session = Depends(get_db),
):
    statement = (
        select(models.UserGroups)
        .where(
            models.UserGroups.is_active.is_(True)
        )
        .order_by(models.UserGroups.name)
    )

    return db.exec(statement).all()


@router.get(
    "/featured",
    response_model=list[schemas.UserGroupResponse],
)
def list_featured_groups(
    db: Session = Depends(get_db),
):
    statement = (
        select(models.UserGroups)
        .where(
            models.UserGroups.is_active.is_(True),
            models.UserGroups.is_featured.is_(True),
        )
        .order_by(models.UserGroups.name)
    )

    return db.exec(statement).all()


@router.get(
    "/",
    response_model=list[schemas.UserGroupResponse],
    dependencies=[Depends(require_admin)],
)
def list_all_groups(
    is_active: bool | None = Query(default=None),
    is_featured: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    statement = select(
        models.UserGroups
    ).order_by(
        models.UserGroups.name
    )

    if is_active is not None:
        statement = statement.where(
            models.UserGroups.is_active == is_active
        )

    if is_featured is not None:
        statement = statement.where(
            models.UserGroups.is_featured == is_featured
        )

    return db.exec(statement).all()


@router.get(
    "/{group_id}",
    response_model=schemas.UserGroupResponse,
    dependencies=[Depends(require_admin)],
)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
):
    return crud.get_group_or_404(
        db,
        group_id,
    )


@router.post(
    "/",
    response_model=schemas.UserGroupResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_group(
    payload: schemas.UserGroupCreate,
    db: Session = Depends(get_db),
):
    return crud.create_user_group(
        db,
        payload,
    )


@router.patch(
    "/{group_id}",
    response_model=schemas.UserGroupResponse,
    dependencies=[Depends(require_admin)],
)
def update_group(
    group_id: int,
    payload: schemas.UserGroupUpdate,
    db: Session = Depends(get_db),
):
    return crud.update_user_group(
        db,
        group_id,
        payload,
    )


@router.patch(
    "/{group_id}/status",
    response_model=schemas.UserGroupResponse,
    dependencies=[Depends(require_admin)],
)
def update_group_status(
    group_id: int,
    payload: schemas.UserGroupStatusUpdate,
    db: Session = Depends(get_db),
):
    group = crud.get_group_or_404(
        db,
        group_id,
    )

    group.is_active = payload.is_active

    if not payload.is_active:
        group.is_featured = False

    db.add(group)
    db.commit()
    db.refresh(group)

    return group


@router.patch(
    "/{group_id}/featured",
    response_model=schemas.UserGroupResponse,
    dependencies=[Depends(require_admin)],
)
def update_featured_status(
    group_id: int,
    payload: schemas.UserGroupFeaturedUpdate,
    db: Session = Depends(get_db),
):
    group = crud.get_group_or_404(
        db,
        group_id,
    )

    crud.validate_group_status(
        group.is_active,
        payload.is_featured,
    )

    group.is_featured = payload.is_featured

    db.add(group)
    db.commit()
    db.refresh(group)

    return group


@router.post(
    "/{group_id}/users/{user_id}",
    response_model=schemas.UserGroupResponse,
    dependencies=[Depends(require_admin)],
)
def assign_user(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    return crud.add_user_to_group(
        db,
        group_id,
        user_id,
    )


@router.delete(
    "/{group_id}/users/{user_id}",
    response_model=schemas.UserGroupResponse,
    dependencies=[Depends(require_admin)],
)
def remove_user(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    return crud.remove_user_from_group(
        db,
        group_id,
        user_id,
    )


@router.delete(
    "/{group_id}",
    response_model=schemas.MessageResponse,
    dependencies=[Depends(require_admin)],
)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
):
    crud.delete_user_group(
        db,
        group_id,
    )

    return {
        "message": (
            "Group deleted successfully. "
            "User accounts were not deleted."
        )
    }