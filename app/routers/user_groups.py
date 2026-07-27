from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Query,
    Request,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app import crud, models, schemas
from app.database import get_db
from app.dependencies.permissions import require_admin


router = APIRouter(
    prefix="/accounts/user-groups",
    tags=["User Groups Management"],
)

templates = Jinja2Templates(
    directory="app/templates"
)


# ==========================================================
# HTML: LIST ALL GROUPS
# GET /accounts/user-groups/pages/list
# ==========================================================

@router.get(
    "/pages/list",
    response_class=HTMLResponse,
)
def user_groups_page(
    request: Request,
    db: Session = Depends(get_db),
):
    statement = select(
        models.UserGroups
    ).order_by(
        models.UserGroups.name
    )

    groups = db.exec(statement).all()

    active_groups_count = 0
    featured_groups_count = 0
    total_users_assigned = 0

    for group in groups:
        # Load the users relationship.
        _ = group.users

        if group.is_active:
            active_groups_count += 1

        if group.is_featured:
            featured_groups_count += 1

        total_users_assigned += len(group.users)

    return templates.TemplateResponse(
        "usergroup_list.html",
        {
            "request": request,
            "groups": groups,
            "active_groups_count": active_groups_count,
            "featured_groups_count": featured_groups_count,
            "total_users_assigned": total_users_assigned,
        },
    )


# ==========================================================
# HTML: CREATE GROUP FORM
# GET /accounts/user-groups/pages/create
# ==========================================================

@router.get(
    "/pages/create",
    response_class=HTMLResponse,
)
def create_group_page(
    request: Request,
):
    return templates.TemplateResponse(
        "usergroup_create.html",
        {
            "request": request,
            "error": None,
            "form_data": None,
        },
    )


# ==========================================================
# HTML: CREATE GROUP
# POST /accounts/user-groups/pages/create
# ==========================================================

@router.post(
    "/pages/create",
    response_class=HTMLResponse,
)
def create_group_from_page(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    is_active: Optional[str] = Form(None),
    is_featured: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    form_data = {
        "name": name,
        "description": description,
        "is_active": is_active is not None,
        "is_featured": is_featured is not None,
    }

    try:
        payload = schemas.UserGroupCreate(
            name=name,
            description=description,
            is_active=is_active is not None,
            is_featured=is_featured is not None,
            user_ids=[],
        )

        crud.create_user_group(
            db,
            payload,
        )

    except Exception as exc:
        error_message = getattr(
            exc,
            "detail",
            str(exc),
        )

        return templates.TemplateResponse(
            "usergroup_create.html",
            {
                "request": request,
                "error": error_message,
                "form_data": form_data,
            },
            status_code=400,
        )

    return RedirectResponse(
        url="/accounts/user-groups/pages/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# ==========================================================
# HTML: GROUP DETAIL PAGE
# GET /accounts/user-groups/pages/{group_id}
# ==========================================================

@router.get(
    "/pages/{group_id}",
    response_class=HTMLResponse,
)
def group_detail_page(
    request: Request,
    group_id: int,
    db: Session = Depends(get_db),
):
    group = crud.get_group_or_404(
        db,
        group_id,
    )

    _ = group.users

    return templates.TemplateResponse(
        "usergroup_detail.html",
        {
            "request": request,
            "group": group,
        },
    )


# ==========================================================
# HTML: EDIT GROUP FORM
# GET /accounts/user-groups/pages/{group_id}/edit
# ==========================================================

@router.get(
    "/pages/{group_id}/edit",
    response_class=HTMLResponse,
)
def edit_group_page(
    request: Request,
    group_id: int,
    db: Session = Depends(get_db),
):
    group = crud.get_group_or_404(
        db,
        group_id,
    )

    _ = group.users

    return templates.TemplateResponse(
        "usergroup_edit.html",
        {
            "request": request,
            "group": group,
            "error": None,
        },
    )


# ==========================================================
# HTML: UPDATE GROUP
# POST /accounts/user-groups/pages/{group_id}/edit
# ==========================================================

@router.post(
    "/pages/{group_id}/edit",
    response_class=HTMLResponse,
)
def update_group_from_page(
    request: Request,
    group_id: int,
    name: str = Form(...),
    description: str = Form(""),
    is_active: Optional[str] = Form(None),
    is_featured: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    try:
        payload = schemas.UserGroupUpdate(
            name=name,
            description=description,
            is_active=is_active is not None,
            is_featured=is_featured is not None,
        )

        crud.update_user_group(
            db,
            group_id,
            payload,
        )

    except Exception as exc:
        error_message = getattr(
            exc,
            "detail",
            str(exc),
        )

        group = crud.get_group_or_404(
            db,
            group_id,
        )

        _ = group.users

        # Show submitted values again when validation fails.
        group.name = name
        group.description = description
        group.is_active = is_active is not None
        group.is_featured = is_featured is not None

        return templates.TemplateResponse(
            "usergroup_edit.html",
            {
                "request": request,
                "group": group,
                "error": error_message,
            },
            status_code=400,
        )

    return RedirectResponse(
        url=f"/accounts/user-groups/pages/{group_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# ==========================================================
# HTML: DELETE GROUP
# POST /accounts/user-groups/pages/{group_id}/delete
# ==========================================================

@router.post(
    "/pages/{group_id}/delete",
)
def delete_group_from_page(
    group_id: int,
    db: Session = Depends(get_db),
):
    crud.delete_user_group(
        db,
        group_id,
    )

    return RedirectResponse(
        url="/accounts/user-groups/pages/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# ==========================================================
# API: CREATE CUSTOMER USER
# POST /accounts/user-groups/users
# ==========================================================

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


# ==========================================================
# API: LIST CUSTOMER USERS
# GET /accounts/user-groups/users
# ==========================================================

@router.get(
    "/users",
    response_model=list[schemas.CustomerUserResponse],
    dependencies=[Depends(require_admin)],
)
def list_users(
    db: Session = Depends(get_db),
):
    statement = select(
        models.CustomerUser
    ).order_by(
        models.CustomerUser.username
    )

    return db.exec(statement).all()


# ==========================================================
# API: LIST ACTIVE GROUPS
# GET /accounts/user-groups/active
# ==========================================================

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
        .order_by(
            models.UserGroups.name
        )
    )

    return db.exec(statement).all()


# ==========================================================
# API: LIST FEATURED GROUPS
# GET /accounts/user-groups/featured
# ==========================================================

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
        .order_by(
            models.UserGroups.name
        )
    )

    groups = db.exec(statement).all()

    for group in groups:
        _ = group.users

    return groups


# ==========================================================
# API: LIST ALL GROUPS
# GET /accounts/user-groups/
# ==========================================================

@router.get(
    "/",
    response_model=list[schemas.UserGroupResponse],
    dependencies=[Depends(require_admin)],
)
def list_all_groups(
    is_active: Optional[bool] = Query(default=None),
    is_featured: Optional[bool] = Query(default=None),
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

    groups = db.exec(statement).all()

    for group in groups:
        _ = group.users

    return groups


# ==========================================================
# API: CREATE GROUP
# POST /accounts/user-groups/
# ==========================================================

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
    group = crud.create_user_group(
        db,
        payload,
    )

    _ = group.users

    return group


# ==========================================================
# API: GET ONE GROUP
# GET /accounts/user-groups/{group_id}
#
# Keep this below /pages, /users, /active and /featured.
# ==========================================================

@router.get(
    "/{group_id}",
    response_model=schemas.UserGroupResponse,
    dependencies=[Depends(require_admin)],
)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
):
    group = crud.get_group_or_404(
        db,
        group_id,
    )

    _ = group.users

    return group


# ==========================================================
# API: UPDATE GROUP
# PATCH /accounts/user-groups/{group_id}
# ==========================================================

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
    group = crud.update_user_group(
        db,
        group_id,
        payload,
    )

    _ = group.users

    return group


# ==========================================================
# API: UPDATE ACTIVE STATUS
# PATCH /accounts/user-groups/{group_id}/status
# ==========================================================

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

    _ = group.users

    return group


# ==========================================================
# API: UPDATE FEATURED STATUS
# PATCH /accounts/user-groups/{group_id}/featured
# ==========================================================

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

    _ = group.users

    return group


# ==========================================================
# API: ASSIGN USER TO GROUP
# POST /accounts/user-groups/{group_id}/users/{user_id}
# ==========================================================

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
    group = crud.add_user_to_group(
        db,
        group_id,
        user_id,
    )

    _ = group.users

    return group


# ==========================================================
# API: REMOVE USER FROM GROUP
# DELETE /accounts/user-groups/{group_id}/users/{user_id}
# ==========================================================

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
    group = crud.remove_user_from_group(
        db,
        group_id,
        user_id,
    )

    _ = group.users

    return group


# ==========================================================
# API: DELETE GROUP
# DELETE /accounts/user-groups/{group_id}
# ==========================================================

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