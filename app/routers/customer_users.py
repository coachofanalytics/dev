from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    RedirectResponse,
)
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlmodel import Session

from app import crud, schemas
from app.database import get_db
from app.dependencies.permissions import require_admin
from app.services.resume_service import (
    delete_resume_file,
    get_resume_full_path,
    save_resume_file,
)


router = APIRouter(
    prefix="/accounts/customer-users",
    tags=["Customer Users"],
)

templates = Jinja2Templates(
    directory="app/templates"
)


def validation_error_message(
    exc: ValidationError,
) -> str:
    errors = exc.errors()

    if not errors:
        return "The submitted information is invalid."

    return str(
        errors[0].get(
            "msg",
            "The submitted information is invalid.",
        )
    )


# -------------------------------------------------
# API ROUTES
# -------------------------------------------------

@router.post(
    "/",
    response_model=schemas.CustomerUserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_customer_user_api(
    username: str = Form(...),
    email: str = Form(...),
    city: str = Form(...),
    state_name: str = Form(
        ...,
        alias="state",
    ),
    country: str = Form(...),
    category: str = Form(...),
    is_admin: bool = Form(False),
    is_employee: bool = Form(False),
    is_client: bool = Form(False),
    is_applicant: bool = Form(False),
    resume_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        payload = schemas.CustomerUserCreate(
            username=username,
            email=email,
            city=city,
            state=state_name,
            country=country,
            category=category,
            is_admin=is_admin,
            is_employee=is_employee,
            is_client=is_client,
            is_applicant=is_applicant,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_error_message(exc),
        ) from exc

    resume_path = await save_resume_file(
        resume_file,
    )

    try:
        return crud.create_customer_user(
            db,
            payload,
            resume_path,
        )
    except Exception:
        delete_resume_file(resume_path)
        raise


@router.get(
    "/",
    response_model=list[
        schemas.CustomerUserResponse
    ],
    dependencies=[Depends(require_admin)],
)
def list_customer_users_api(
    city: Optional[str] = None,
    state_name: Optional[str] = Query(
        default=None,
        alias="state",
    ),
    country: Optional[str] = None,
    category: Optional[str] = None,
    is_admin: Optional[bool] = None,
    is_employee: Optional[bool] = None,
    is_client: Optional[bool] = None,
    is_applicant: Optional[bool] = None,
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
):
    return crud.list_customer_users(
        db,
        city=city,
        state_name=state_name,
        country=country,
        category=category,
        is_admin=is_admin,
        is_employee=is_employee,
        is_client=is_client,
        is_applicant=is_applicant,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{customer_user_id}",
    response_model=schemas.CustomerUserResponse,
    dependencies=[Depends(require_admin)],
)
def get_customer_user_api(
    customer_user_id: int,
    db: Session = Depends(get_db),
):
    return crud.get_customer_user_or_404(
        db,
        customer_user_id,
    )


@router.put(
    "/{customer_user_id}",
    response_model=schemas.CustomerUserResponse,
    dependencies=[Depends(require_admin)],
)
async def update_customer_user_api(
    customer_user_id: int,
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state_name: Optional[str] = Form(
        default=None,
        alias="state",
    ),
    country: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    is_admin: Optional[bool] = Form(None),
    is_employee: Optional[bool] = Form(None),
    is_client: Optional[bool] = Form(None),
    is_applicant: Optional[bool] = Form(None),
    resume_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    customer_user = (
        crud.get_customer_user_or_404(
            db,
            customer_user_id,
        )
    )

    payload = schemas.CustomerUserUpdate(
        username=username,
        email=email,
        city=city,
        state=state_name,
        country=country,
        category=category,
        is_admin=is_admin,
        is_employee=is_employee,
        is_client=is_client,
        is_applicant=is_applicant,
    )

    previous_resume = customer_user.resume_file
    new_resume = None

    if (
        resume_file is not None
        and resume_file.filename
    ):
        new_resume = await save_resume_file(
            resume_file
        )

    try:
        updated_user = crud.update_customer_user(
            db,
            customer_user,
            payload,
            new_resume,
        )
    except Exception:
        delete_resume_file(new_resume)
        raise

    if new_resume:
        delete_resume_file(previous_resume)

    return updated_user


@router.delete(
    "/{customer_user_id}",
    response_model=schemas.MessageResponse,
    dependencies=[Depends(require_admin)],
)
def delete_customer_user_api(
    customer_user_id: int,
    db: Session = Depends(get_db),
):
    customer_user = (
        crud.get_customer_user_or_404(
            db,
            customer_user_id,
        )
    )

    resume_path = customer_user.resume_file

    crud.delete_customer_user(
        db,
        customer_user,
    )

    delete_resume_file(resume_path)

    return {
        "message": "Customer user deleted successfully."
    }


@router.get(
    "/{customer_user_id}/resume/download",
    dependencies=[Depends(require_admin)],
)
def download_customer_user_resume(
    customer_user_id: int,
    db: Session = Depends(get_db),
):
    customer_user = (
        crud.get_customer_user_or_404(
            db,
            customer_user_id,
        )
    )

    full_path = get_resume_full_path(
        customer_user.resume_file,
    )

    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file not found.",
        )

    return FileResponse(
        path=full_path,
        filename=full_path.name,
        media_type="application/octet-stream",
    )


# -------------------------------------------------
# HTML PAGE ROUTES
# -------------------------------------------------

@router.get(
    "/pages/list",
    response_class=HTMLResponse,
)
def customer_user_list_page(
    request: Request,
    city: Optional[str] = None,
    state_name: Optional[str] = Query(
        default=None,
        alias="state",
    ),
    country: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    customer_users = crud.list_customer_users(
        db,
        city=city,
        state_name=state_name,
        country=country,
        category=category,
    )

    return templates.TemplateResponse(
        request=request,
        name="customeruser_list.html",
        context={
            "customer_users": customer_users,
            "city": city or "",
            "state": state_name or "",
            "country": country or "",
            "category": category or "",
        },
    )


@router.get(
    "/pages/create",
    response_class=HTMLResponse,
)
def customer_user_create_page(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="customeruser_create.html",
        context={
            "error": None,
            "form_data": {},
        },
    )


@router.post(
    "/pages/create",
    response_class=HTMLResponse,
)
async def customer_user_create_page_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    city: str = Form(...),
    state_name: str = Form(
        ...,
        alias="state",
    ),
    country: str = Form(...),
    category: str = Form(...),
    is_admin: bool = Form(False),
    is_employee: bool = Form(False),
    is_client: bool = Form(False),
    is_applicant: bool = Form(False),
    resume_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    form_data = {
        "username": username,
        "email": email,
        "city": city,
        "state": state_name,
        "country": country,
        "category": category,
        "is_admin": is_admin,
        "is_employee": is_employee,
        "is_client": is_client,
        "is_applicant": is_applicant,
    }

    try:
        payload = schemas.CustomerUserCreate(
            **form_data
        )

        resume_path = await save_resume_file(
            resume_file
        )

        try:
            crud.create_customer_user(
                db,
                payload,
                resume_path,
            )
        except Exception:
            delete_resume_file(resume_path)
            raise

    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="customeruser_create.html",
            context={
                "error": validation_error_message(
                    exc
                ),
                "form_data": form_data,
            },
            status_code=400,
        )

    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="customeruser_create.html",
            context={
                "error": exc.detail,
                "form_data": form_data,
            },
            status_code=exc.status_code,
        )

    return RedirectResponse(
        url="/accounts/customer-users/pages/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get(
    "/pages/{customer_user_id}",
    response_class=HTMLResponse,
)
def customer_user_detail_page(
    customer_user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    customer_user = (
        crud.get_customer_user_or_404(
            db,
            customer_user_id,
        )
    )

    return templates.TemplateResponse(
        request=request,
        name="customeruser_detail.html",
        context={
            "customer_user": customer_user,
        },
    )


@router.get(
    "/pages/{customer_user_id}/edit",
    response_class=HTMLResponse,
)
def customer_user_edit_page(
    customer_user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    customer_user = (
        crud.get_customer_user_or_404(
            db,
            customer_user_id,
        )
    )

    return templates.TemplateResponse(
        request=request,
        name="customeruser_edit.html",
        context={
            "customer_user": customer_user,
            "error": None,
        },
    )


@router.post(
    "/pages/{customer_user_id}/edit",
    response_class=HTMLResponse,
)
async def customer_user_edit_page_submit(
    customer_user_id: int,
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    city: str = Form(...),
    state_name: str = Form(
        ...,
        alias="state",
    ),
    country: str = Form(...),
    category: str = Form(...),
    is_admin: bool = Form(False),
    is_employee: bool = Form(False),
    is_client: bool = Form(False),
    is_applicant: bool = Form(False),
    resume_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    customer_user = crud.get_customer_user_or_404(
        db,
        customer_user_id,
    )

    old_resume = customer_user.resume_file
    new_resume = None

    try:
        payload = schemas.CustomerUserUpdate(
            username=username,
            email=email,
            city=city,
            state=state_name,
            country=country,
            category=category,
            is_admin=is_admin,
            is_employee=is_employee,
            is_client=is_client,
            is_applicant=is_applicant,
        )

        if (
            resume_file is not None
            and resume_file.filename
        ):
            new_resume = await save_resume_file(
                resume_file,
            )

        crud.update_customer_user(
            db,
            customer_user,
            payload,
            new_resume,
        )

    except ValidationError as exc:
        if new_resume:
            delete_resume_file(
                new_resume,
            )

        return templates.TemplateResponse(
            request=request,
            name="customeruser_edit.html",
            context={
                "customer_user": customer_user,
                "error": validation_error_message(exc),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    except HTTPException as exc:
        if new_resume:
            delete_resume_file(
                new_resume,
            )

        return templates.TemplateResponse(
            request=request,
            name="customeruser_edit.html",
            context={
                "customer_user": customer_user,
                "error": exc.detail,
            },
            status_code=exc.status_code,
        )

    except Exception:
        if new_resume:
            delete_resume_file(
                new_resume,
            )
        raise

    if new_resume:
        delete_resume_file(
            old_resume,
        )

    return RedirectResponse(
        url=(
            "/accounts/customer-users/"
            f"pages/{customer_user_id}"
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post(
    "/pages/{customer_user_id}/delete",
)
def customer_user_delete_page(
    customer_user_id: int,
    db: Session = Depends(get_db),
):
    customer_user = (
        crud.get_customer_user_or_404(
            db,
            customer_user_id,
        )
    )

    resume_path = customer_user.resume_file

    crud.delete_customer_user(
        db,
        customer_user,
    )

    delete_resume_file(resume_path)

    return RedirectResponse(
        url="/accounts/customer-users/pages/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )