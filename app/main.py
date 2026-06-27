from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel, Session

from . import models, database, crud
from .routers import search

SQLModel.metadata.create_all(database.engine)

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")

app.include_router(search.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI!"}


@app.get("/search-dashboard")
def search_dashboard(request: Request):
    with Session(database.engine) as db:
        stats = crud.get_search_stats(db)
        records = crud.get_search_records(db=db, skip=0, limit=100)

    return templates.TemplateResponse(
        "search_dashboard.html",
        {
            "request": request,
            "total_records": stats["total_records"],
            "uploaded_records": stats["uploaded_records"],
            "pending_records": stats["pending_records"],
            "records": records
        }
    )


@app.post("/search-dashboard/create")
def create_search_record(
    topic: str = Form(...),
    question: str = Form(...),
    uploaded: bool = Form(False)
):
    with Session(database.engine) as db:
        record = models.SearchRecord(
            topic=topic,
            question=question,
            uploaded=uploaded
        )

        db.add(record)
        db.commit()

    return RedirectResponse(
        url="/search-dashboard",
        status_code=303
    )


@app.get("/search-dashboard/edit/{record_id}")
def edit_record(record_id: int, request: Request):
    with Session(database.engine) as db:
        record = db.get(models.SearchRecord, record_id)

        if not record:
            return RedirectResponse(
                url="/search-dashboard",
                status_code=303
            )

    return templates.TemplateResponse(
        "edit_record.html",
        {
            "request": request,
            "record": record
        }
    )


@app.post("/search-dashboard/update/{record_id}")
def update_record(
    record_id: int,
    topic: str = Form(...),
    question: str = Form(...),
    uploaded: bool = Form(False)
):
    with Session(database.engine) as db:
        record = db.get(models.SearchRecord, record_id)

        if record:
            record.topic = topic
            record.question = question
            record.uploaded = uploaded

            db.add(record)
            db.commit()

    return RedirectResponse(
        url="/search-dashboard",
        status_code=303
    )


@app.post("/search-dashboard/delete/{record_id}")
def delete_search_dashboard_record(record_id: int):
    with Session(database.engine) as db:
        record = db.get(models.SearchRecord, record_id)

        if record:
            db.delete(record)
            db.commit()

    return RedirectResponse(
        url="/search-dashboard",
        status_code=303
    )