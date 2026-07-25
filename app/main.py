from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session, select

from . import crud, database, models
from .database import get_db
from .models import JobDetails
from .routers import search
from .schemas import JobDetailsCreate, JobDetailsUpdate
# from app.routers import job_details


from fastapi import FastAPI

from .routers import scores, search
from fastapi import FastAPI
from sqlmodel import SQLModel

from app.database import engine
from app.routers import user_groups
from fastapi import FastAPI
from sqlmodel import SQLModel

from app.database import engine
# from app.routers import job_details


app = FastAPI(
    title="FastAPI Application"
)


@app.on_event("startup")
def startup_event():
    SQLModel.metadata.create_all(engine)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to FastAPI"
    }


# app.include_router(
#     job_details.router
# )


app = FastAPI(
    title="CODA API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.include_router(search.router)
app.include_router(scores.router)
templates = Jinja2Templates(directory="app/templates")

app.include_router(search.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI!"}

# ==========================================================
# SEARCH DASHBOARD ROUTES
# ==========================================================

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


# ==========================================================
# JOB DETAILS HTML PAGE
# ==========================================================

@app.get("/application/jobs/pages/list", response_class=HTMLResponse, tags=["Job Details"])
def jobs_page(
    request: Request,
    search: Optional[str] = None,
    project_type: Optional[str] = None,
    engagement_level: Optional[str] = None,
    status: Optional[str] = None,
   session: Session = Depends(get_db)
):
    statement = select(JobDetails)

    if search:
        statement = statement.where(JobDetails.title.contains(search))

    if project_type:
        statement = statement.where(JobDetails.project_type == project_type)

    if engagement_level:
        statement = statement.where(JobDetails.engagement_level == engagement_level)

    if status:
        statement = statement.where(JobDetails.status == status)

    jobs = session.exec(statement).all()

    all_jobs = session.exec(select(JobDetails)).all()

    total_jobs = len(all_jobs)
    open_jobs = len([job for job in all_jobs if job.status == "open"])
    draft_jobs = len([job for job in all_jobs if job.status == "draft"])
    closed_jobs = len([job for job in all_jobs if job.status == "closed"])

    return templates.TemplateResponse(
        "JobDetails_list.html",
        {
            "request": request,
            "jobs": jobs,
            "search": search,
            "project_type": project_type,
            "engagement_level": engagement_level,
            "status": status,
            "total_jobs": total_jobs,
            "open_jobs": open_jobs,
            "draft_jobs": draft_jobs,
            "closed_jobs": closed_jobs
        }
    )

@app.get("/application/jobs/", response_model=List[JobDetails], tags=["Job Details"])
def list_jobs(
    search: Optional[str] = None,
    project_type: Optional[str] = None,
    engagement_level: Optional[str] = None,
    status: Optional[str] = None,
   session: Session = Depends(get_db)
):
    statement = select(JobDetails)

    if search:
        statement = statement.where(JobDetails.title.contains(search))

    if project_type:
        statement = statement.where(JobDetails.project_type == project_type)

    if engagement_level:
        statement = statement.where(JobDetails.engagement_level == engagement_level)

    if status:
        statement = statement.where(JobDetails.status == status)

    jobs = session.exec(statement).all()
    return jobs

@app.get("/application/jobs/pages/create/form", response_class=HTMLResponse, tags=["Job Details"])
def create_job_form(request: Request):
    return templates.TemplateResponse(
        "JobDetails_create.html",
        {
            "request": request
        }
    )


@app.post("/application/jobs/pages/create/form", tags=["Job Details"])
def create_job_from_form(
    title: str = Form(...),
    company_name: str = Form(""),
    description: str = Form(...),
    skills_required: str = Form(...),
    deliverables: str = Form(...),
    payment_min: float = Form(...),
    payment_max: float = Form(...),
    currency: str = Form("USD"),
    duration_value: int = Form(...),
    duration_unit: str = Form("weeks"),
    project_type: str = Form("fixed"),
    engagement_level: str = Form("medium"),
    external_reference_links: str = Form(""),
    status: str = Form("open"),
    session: Session = Depends(get_db)
):
    if payment_max < payment_min:
        raise HTTPException(
            status_code=400,
            detail="Maximum payment cannot be less than minimum payment"
        )

    job = JobDetails(
        title=title,
        company_name=company_name,
        description=description,
        skills_required=skills_required,
        deliverables=deliverables,
        payment_min=payment_min,
        payment_max=payment_max,
        currency=currency,
        duration_value=duration_value,
        duration_unit=duration_unit,
        project_type=project_type,
        engagement_level=engagement_level,
        external_reference_links=external_reference_links,
        status=status
    )

    session.add(job)
    session.commit()
    session.refresh(job)

    return RedirectResponse(
        url="/application/jobs/pages/list",
        status_code=303
    )


@app.post("/application/jobs/", response_model=JobDetails, tags=["Job Details"])
def create_job(
    job: JobDetailsCreate,
    session: Session = Depends(get_db)
):
    if job.payment_max < job.payment_min:
        raise HTTPException(
            status_code=400,
            detail="payment_max cannot be less than payment_min"
        )

    db_job = JobDetails(**job.dict())

    session.add(db_job)
    session.commit()
    session.refresh(db_job)

    return db_job


@app.get("/application/jobs/{job_id}", response_model=JobDetails, tags=["Job Details"])
def get_job(
    job_id: int,
  session: Session = Depends(get_db)
):
    job = session.get(JobDetails, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@app.patch("/application/jobs/{job_id}", response_model=JobDetails, tags=["Job Details"])
def update_job(
    job_id: int,
    job_update: JobDetailsUpdate,
   session: Session = Depends(get_db)
):
    job = session.get(JobDetails, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    update_data = job_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(job, key, value)

    if job.payment_max < job.payment_min:
        raise HTTPException(
            status_code=400,
            detail="payment_max cannot be less than payment_min"
        )

    job.updated_at = datetime.utcnow()

    session.add(job)
    session.commit()
    session.refresh(job)

    return job


@app.delete("/application/jobs/{job_id}", tags=["Job Details"])
def delete_job(
    job_id: int,
    session: Session = Depends(get_db)
):
    job = session.get(JobDetails, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    session.delete(job)
    session.commit()

    return {"message": "Job deleted successfully"}

@app.get("/application/jobs/pages/{job_id}", response_class=HTMLResponse, tags=["Job Details"])
def job_detail_page(
    job_id: int,
    request: Request,
    session: Session = Depends(get_db)
):
    job = session.get(JobDetails, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    skills = [
        skill.strip()
        for skill in job.skills_required.split(",")
        if skill.strip()
    ]

    links = []

    if job.external_reference_links:
        links = [
            link.strip()
            for link in job.external_reference_links.splitlines()
            if link.strip()
        ]

    return templates.TemplateResponse(
        "JobDetails_detail.html",
        {
            "request": request,
            "job": job,
            "skills": skills,
            "links": links
        }
    )

@app.get("/application/jobs/pages/{job_id}/edit", response_class=HTMLResponse, tags=["Job Details"])
def edit_job_form(
    job_id: int,
    request: Request,
    session: Session = Depends(get_db)
):
    job = session.get(JobDetails, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return templates.TemplateResponse(
        "JobDetails_edit.html",
        {
            "request": request,
            "job": job
        }
    )


@app.post("/application/jobs/pages/{job_id}/edit", tags=["Job Details"])
def update_job_from_form(
    job_id: int,
    title: str = Form(...),
    company_name: str = Form(""),
    description: str = Form(...),
    skills_required: str = Form(...),
    deliverables: str = Form(...),
    payment_min: float = Form(...),
    payment_max: float = Form(...),
    currency: str = Form("USD"),
    duration_value: int = Form(...),
    duration_unit: str = Form("weeks"),
    project_type: str = Form("fixed"),
    engagement_level: str = Form("medium"),
    external_reference_links: str = Form(""),
    status: str = Form("open"),
    session: Session = Depends(get_db)
):
    job = session.get(JobDetails, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if payment_max < payment_min:
        raise HTTPException(
            status_code=400,
            detail="Maximum payment cannot be less than minimum payment"
        )

    job.title = title
    job.company_name = company_name
    job.description = description
    job.skills_required = skills_required
    job.deliverables = deliverables
    job.payment_min = payment_min
    job.payment_max = payment_max
    job.currency = currency
    job.duration_value = duration_value
    job.duration_unit = duration_unit
    job.project_type = project_type
    job.engagement_level = engagement_level
    job.external_reference_links = external_reference_links
    job.status = status
    job.updated_at = datetime.utcnow()

    session.add(job)
    session.commit()
    session.refresh(job)

    return RedirectResponse(
        url=f"/application/jobs/pages/{job.id}",
        status_code=303
    )


@app.post("/application/jobs/pages/{job_id}/delete", tags=["Job Details"])
def delete_job_from_page(
    job_id: int,
   session: Session = Depends(get_db)
):
    job = session.get(JobDetails, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    session.delete(job)
    session.commit()

    return RedirectResponse(
        url="/application/jobs/pages/list",
        status_code=303
    )

from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select


DATABASE_URL = "sqlite:///document_app.db"
engine = create_engine(DATABASE_URL, echo=True)


# class DocumentApplication(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     user_id: int
#     service_type: str
#     first_name: str
#     last_name: str
#     id_number: str
#     district: str
#     sub_county: str
#     reason: str
#     status: str = "draft"
#     fee: Decimal = Field(default=0, max_digits=12, decimal_places=2)
#     submitted_at: datetime = Field(default_factory=datetime.utcnow)
#     last_modified: datetime = Field(default_factory=datetime.utcnow)


# def create_db_and_tables():
#     SQLModel.metadata.create_all(engine)


# app = FastAPI()


# @app.on_event("startup")
# def on_startup():
#     create_db_and_tables()


# # LIST VIEW
# @app.get("/document-applications/", response_model=List[DocumentApplication])
# def list_document_applications(
#     status: Optional[str] = None,
#     service_type: Optional[str] = None,
#     skip: int = 0,
#     limit: int = 10
# ):
#     with Session(engine) as session:
#         statement = select(DocumentApplication)

#         if status:
#             statement = statement.where(DocumentApplication.status == status)

#         if service_type:
#             statement = statement.where(DocumentApplication.service_type == service_type)

#         statement = statement.offset(skip).limit(limit)

#         applications = session.exec(statement).all()
#         return applications


# # CREATE VIEW
# @app.post("/document-applications/", response_model=DocumentApplication)
# def create_document_application(application: DocumentApplication):
#     with Session(engine) as session:
#         session.add(application)
#         session.commit()
#         session.refresh(application)
#         return application


# # UPDATE VIEW
# @app.put("/document-applications/{application_id}", response_model=DocumentApplication)
# def update_document_application(application_id: int, updated_application: DocumentApplication):
#     with Session(engine) as session:
#         application = session.get(DocumentApplication, application_id)

#         if not application:
#             raise HTTPException(status_code=404, detail="Application not found")

#         application.user_id = updated_application.user_id
#         application.service_type = updated_application.service_type
#         application.first_name = updated_application.first_name
#         application.last_name = updated_application.last_name
#         application.id_number = updated_application.id_number
#         application.district = updated_application.district
#         application.sub_county = updated_application.sub_county
#         application.reason = updated_application.reason
#         application.status = updated_application.status
#         application.fee = updated_application.fee
#         application.last_modified = datetime.utcnow()

#         session.add(application)
#         session.commit()
#         session.refresh(application)

#         return application



# @app.delete("/document-applications/{application_id}")
# def delete_document_application(application_id: int):
#     with Session(engine) as session:
#         application = session.get(DocumentApplication, application_id)

#         if not application:
#             raise HTTPException(
#                 status_code=404,
#                 detail="Application not found"
#             )

#         session.delete(application)
#         session.commit()

#         return {
#             "message": "Document application deleted successfully."
#         }




app = FastAPI(
    title="User Groups Management API",
)


@app.on_event("startup")
def startup_event():
    SQLModel.metadata.create_all(engine)


@app.get("/")
def root():
    return {
        "message": "FastAPI application is running."
    }


app.include_router(
    user_groups.router
)