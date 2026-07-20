from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from .. import crud, schemas
from ..database import get_db


router = APIRouter(
    prefix="/accounts/scores",
    tags=["Accounts Scores"],
)


@router.post(
    "/",
    response_model=schemas.ScoreRead,
    status_code=status.HTTP_201_CREATED,
)
def create_score(
    score_data: schemas.ScoreCreate,
    db: Session = Depends(get_db),
):
    return crud.create_score(
        db=db,
        score_data=score_data,
    )


@router.get(
    "/",
    response_model=list[schemas.ScoreRead],
)
def list_scores(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    email: str | None = None,
    gender: str | None = None,
    city: str | None = None,
    state: str | None = None,
    country: str | None = None,
    category: str | None = None,
    sub_category: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
):
    return crud.get_scores(
        db=db,
        skip=skip,
        limit=limit,
        email=email,
        gender=gender,
        city=city,
        state=state,
        country=country,
        category=category,
        sub_category=sub_category,
    )


@router.get(
    "/{score_id}",
    response_model=schemas.ScoreRead,
)
def retrieve_score(
    score_id: int,
    db: Session = Depends(get_db),
):
    score = crud.get_score(
        db=db,
        score_id=score_id,
    )

    if score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score record not found",
        )

    return score


@router.patch(
    "/{score_id}",
    response_model=schemas.ScoreRead,
)
def update_score(
    score_id: int,
    score_data: schemas.ScoreUpdate,
    db: Session = Depends(get_db),
):
    score = crud.update_score(
        db=db,
        score_id=score_id,
        score_data=score_data,
    )

    if score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score record not found",
        )

    return score