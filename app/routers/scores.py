from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlmodel import Session

from app import crud, schemas
from app.database import get_db


router = APIRouter(
    prefix="/accounts/scores",
    tags=["Accounts Scores"],
)

templates = Jinja2Templates(
    directory="app/templates",
)


# ==========================================================
# HTML PAGE ROUTES
# Fixed routes must appear before /pages/{score_id}
# ==========================================================

@router.get(
    "/pages/list",
    response_class=HTMLResponse,
)
def score_list_page(
    request: Request,
    db: Session = Depends(get_db),
):
    scores = crud.get_scores(
        db=db,
        skip=0,
        limit=100,
    )

    return templates.TemplateResponse(
        request=request,
        name="score_list.html",
        context={
            "scores": scores,
            "success": None,
            "error": None,
        },
    )


@router.get(
    "/pages/create",
    response_class=HTMLResponse,
)
def score_create_page(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="score_create.html",
        context={
            "error": None,
            "form_data": {},
        },
    )


@router.post(
    "/pages/create",
    response_class=HTMLResponse,
)
def score_create_page_submit(
    request: Request,
    email: str = Form(...),
    gender: str = Form(""),
    phone: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    state_name: str = Form(
        ...,
        alias="state",
    ),
    zipcode: str = Form(...),
    country: str = Form(...),
    category: str = Form(...),
    sub_category: int = Form(...),
    db: Session = Depends(get_db),
):
    form_data = {
        "email": email,
        "gender": gender,
        "phone": phone,
        "address": address,
        "city": city,
        "state": state_name,
        "zipcode": zipcode,
        "country": country,
        "category": category,
        "sub_category": sub_category,
    }

    try:
        payload = schemas.ScoreCreate(
            email=email,
            gender=gender or None,
            phone=phone,
            address=address,
            city=city,
            state=state_name,
            zipcode=zipcode,
            country=country,
            category=category,
            sub_category=sub_category,
        )

        crud.create_score(
            db,
            payload,
        )

    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="score_create.html",
            context={
                "error": str(exc),
                "form_data": form_data,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="score_create.html",
            context={
                "error": exc.detail,
                "form_data": form_data,
            },
            status_code=exc.status_code,
        )

    return RedirectResponse(
        url="/accounts/scores/pages/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get(
    "/pages/{score_id}",
    response_class=HTMLResponse,
)
def score_detail_page(
    score_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    score = crud.get_score_or_404(
        db,
        score_id,
    )

    return templates.TemplateResponse(
        request=request,
        name="score_detail.html",
        context={
            "score": score,
        },
    )


@router.get(
    "/pages/{score_id}/edit",
    response_class=HTMLResponse,
)
def score_edit_page(
    score_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    score = crud.get_score_or_404(
        db,
        score_id,
    )

    return templates.TemplateResponse(
        request=request,
        name="score_edit.html",
        context={
            "score": score,
            "error": None,
        },
    )


@router.post(
    "/pages/{score_id}/edit",
    response_class=HTMLResponse,
)
def score_edit_page_submit(
    score_id: int,
    request: Request,
    email: str = Form(...),
    gender: str = Form(""),
    phone: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    state_name: str = Form(
        ...,
        alias="state",
    ),
    zipcode: str = Form(...),
    country: str = Form(...),
    category: str = Form(...),
    sub_category: int = Form(...),
    db: Session = Depends(get_db),
):
    score = crud.get_score_or_404(
        db,
        score_id,
    )

    try:
        payload = schemas.ScoreUpdate(
            email=email,
            gender=gender or None,
            phone=phone,
            address=address,
            city=city,
            state=state_name,
            zipcode=zipcode,
            country=country,
            category=category,
            sub_category=sub_category,
        )

        updated_score = crud.update_score(
            db,
            score_id,
            payload,
        )

        if updated_score is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Score record not found.",
            )

    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="score_edit.html",
            context={
                "score": score,
                "error": str(exc),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="score_edit.html",
            context={
                "score": score,
                "error": exc.detail,
            },
            status_code=exc.status_code,
        )

    return RedirectResponse(
        url=f"/accounts/scores/pages/{score_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post(
    "/pages/{score_id}/delete",
)
def score_delete_page(
    score_id: int,
    db: Session = Depends(get_db),
):
    deleted_score = crud.delete_score(
        db,
        score_id,
    )

    if deleted_score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score record not found.",
        )

    return RedirectResponse(
        url="/accounts/scores/pages/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# ==========================================================
# API ROUTES
# ==========================================================

@router.post(
    "/",
    response_model=schemas.ScoreRead,
    status_code=status.HTTP_201_CREATED,
)
def create_score_api(
    payload: schemas.ScoreCreate,
    db: Session = Depends(get_db),
):
    return crud.create_score(
        db,
        payload,
    )


@router.get(
    "/",
    response_model=list[schemas.ScoreRead],
)
def list_scores_api(
    skip: int = 0,
    limit: int = 100,
    email: Optional[str] = None,
    gender: Optional[str] = None,
    city: Optional[str] = None,
    state_name: Optional[str] = None,
    country: Optional[str] = None,
    category: Optional[str] = None,
    sub_category: Optional[int] = None,
    db: Session = Depends(get_db),
):
    return crud.get_scores(
        db=db,
        skip=skip,
        limit=limit,
        email=email,
        gender=gender,
        city=city,
        state=state_name,
        country=country,
        category=category,
        sub_category=sub_category,
    )


@router.get(
    "/{score_id}",
    response_model=schemas.ScoreRead,
)
def get_score_api(
    score_id: int,
    db: Session = Depends(get_db),
):
    return crud.get_score_or_404(
        db,
        score_id,
    )


@router.patch(
    "/{score_id}",
    response_model=schemas.ScoreRead,
)
def update_score_api(
    score_id: int,
    payload: schemas.ScoreUpdate,
    db: Session = Depends(get_db),
):
    score = crud.update_score(
        db,
        score_id,
        payload,
    )

    if score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score record not found.",
        )

    return score


@router.delete(
    "/{score_id}",
    response_model=schemas.MessageResponse,
)
def delete_score_api(
    score_id: int,
    db: Session = Depends(get_db),
):
    score = crud.delete_score(
        db,
        score_id,
    )

    if score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score record not found.",
        )

    return {
        "message": "Score record deleted successfully.",
    }