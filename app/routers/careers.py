from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)

from app import crud
from app.database import get_db


router = APIRouter(
    prefix="/careers",
    tags=["Careers"],
)

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get(
    "/",
    response_class=HTMLResponse,
)
def careers_page(
    request: Request,
    db: Session = Depends(get_db),
):
    vacancies = crud.list_career_vacancies(
        db,
        active_only=True,
    )

    return templates.TemplateResponse(
        request=request,
        name="careers_list.html",
        context={
            "vacancies": vacancies,
        },
    )


@router.get(
    "/{slug}",
    response_class=HTMLResponse,
)
def career_detail_page(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
):
    vacancy = crud.get_career_vacancy_by_slug(
        db,
        slug,
    )

    return templates.TemplateResponse(
        request=request,
        name="career_detail.html",
        context={
            "vacancy": vacancy,
            "can_apply": can_accept_applications(
                vacancy
            ),
            "status_label": vacancy_status_label(
                vacancy
            ),
        },
    )


@router.get(
    "/{slug}/apply",
    response_class=HTMLResponse,
)
def career_apply_page(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
):
    vacancy = crud.get_career_vacancy_by_slug(
        db,
        slug,
    )

    if not can_accept_applications(
        vacancy
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "This vacancy is not currently "
                "accepting applications."
            ),
        )

    return templates.TemplateResponse(
        request=request,
        name="career_apply.html",
        context={
            "vacancy": vacancy,
            "error": None,
            "form_data": {},
        },
    )


@router.post(
    "/{slug}/apply",
    response_class=HTMLResponse,
)
async def career_apply_submit(
    slug: str,
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    location: str = Form(""),
    cover_letter: str = Form(""),
    privacy_confirmed: bool = Form(False),
    resume_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    vacancy = crud.get_career_vacancy_by_slug(
        db,
        slug,
    )

    if not can_accept_applications(
        vacancy
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "This vacancy is not currently "
                "accepting applications."
            ),
        )

    resume_path = None

    try:
        payload = schemas.CareerApplicationCreate(
            full_name=full_name,
            email=email,
            phone=phone or None,
            location=location or None,
            cover_letter=cover_letter or None,
            privacy_confirmed=privacy_confirmed,
        )

        resume_path = await save_resume_file(
            resume_file
        )

        application = crud.create_career_application(
            db,
            vacancy.id,
            payload,
            resume_path,
        )

    except ValidationError as exc:
        if resume_path:
            delete_resume_file(
                resume_path
            )

        return templates.TemplateResponse(
            request=request,
            name="career_apply.html",
            context={
                "vacancy": vacancy,
                "error": str(exc),
                "form_data": {
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "location": location,
                    "cover_letter": cover_letter,
                },
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(
        url=(
            f"/careers/{slug}/confirmation"
            f"?application_id={application.id}"
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get(
    "/{slug}/confirmation",
    response_class=HTMLResponse,
)
def application_confirmation(
    slug: str,
    request: Request,
    application_id: int,
    db: Session = Depends(get_db),
):
    vacancy = crud.get_career_vacancy_by_slug(
        db,
        slug,
    )

    return templates.TemplateResponse(
        request=request,
        name="career_confirmation.html",
        context={
            "vacancy": vacancy,
            "application_id": application_id,
        },
    )