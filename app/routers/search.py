from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas, database


router = APIRouter(
    prefix="/search",
    tags=["Search Records"]
)


def get_db():
    with database.SessionLocal() as db:
        yield db


@router.post("/", response_model=schemas.SearchRecord)
def create_record(
    record: schemas.SearchRecordCreate,
    db: Session = Depends(get_db)
):
    return crud.create_search_record(db=db, record=record)

@router.get("/", response_model=list[schemas.SearchRecord])
def read_records(
    skip: int = 0,
    limit: int = 10,
    topic: str | None = None,
    keyword: str | None = None,
    uploaded: bool | None = None,
    sort_by: str = "newest",
    db: Session = Depends(get_db)
):
    return crud.get_search_records(
        db=db,
        skip=skip,
        limit=limit,
        topic=topic,
        keyword=keyword,
        uploaded=uploaded,
        sort_by=sort_by
    )
    
@router.get("/stats/summary")
def search_stats(db: Session = Depends(get_db)):
    return crud.get_search_stats(db=db)

@router.get("/{record_id}", response_model=schemas.SearchRecord)
def read_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    db_record = crud.get_search_record(db=db, record_id=record_id)

    if db_record is None:
        raise HTTPException(status_code=404, detail="Search record not found")

    return db_record


@router.put("/{record_id}", response_model=schemas.SearchRecord)
def update_record(
    record_id: int,
    record: schemas.SearchRecordUpdate,
    db: Session = Depends(get_db)
):
    db_record = crud.update_search_record(
        db=db,
        record_id=record_id,
        record=record
    )

    if db_record is None:
        raise HTTPException(status_code=404, detail="Search record not found")

    return db_record


@router.delete("/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    db_record = crud.delete_search_record(db=db, record_id=record_id)

    if db_record is None:
        raise HTTPException(status_code=404, detail="Search record not found")

    return {"message": "Search record deleted successfully"}