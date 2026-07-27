from pathlib import Path

output = Path("/mnt/data/main_with_account_profile.py")

# code = r'''from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session, select

from . import crud, database, models
from .database import get_db
from .models import JobDetails
from .routers import scores, search, user_groups
from .schemas import JobDetailsCreate, JobDetailsUpdate


# ==========================================================
# FASTAPI APPLICATION
# ==========================================================

app = FastAPI(
    title="CODA API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIRECTORY = Path("app/uploads/resumes")
UPLOAD_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


@app.on_event("startup")
def startup_event():
    SQLModel.metadata.create_all(database.engine)


app.include_router(search.router)
app.include_router(scores.router)
app.include_router(user_groups.router)


@app.get("/")
def read_root():
    return {
        "message": "FastAPI application is running."
    }


# ==========================================================
# ACCOUNT PROFILE ROUTES
# ==========================================================

@app.get(
    "/accounts/profile",
    response_class=HTMLResponse,
    tags=["Account Profile"],
)
def account_profile_page(
    request: Request,
):
    return templates.TemplateResponse(
        "account_profile.html",
        {
            "request": request,
            "profile": None,
            "success": None,
            "error": None,
        },
    )


@app.post(
    "/accounts/profile",
    response_class=HTMLResponse,
    tags=["Account Profile"],
)
async def save_account_profile(
    request: Request,
    city: str = Form(""),
    state: str = Form(""),
    country: str = Form(""),
    is_admin: Optional[str] = Form(None),
    is_employee: Optional[str] = Form(None),
    is_client: Optional[str] = Form(None),
    is_applicant: Optional[str] = Form(None),
    resume: Optional[UploadFile] = File(None),
):
    profile = {
        "city": city,
        "state": state,
        "country": country,
        "is_admin": is_admin is not None,
        "is_employee": is_employee is not None,
        "is_client": is_client is not None,
        "is_applicant": is_applicant is not None,
    }

    if resume and resume.filename:
        allowed_extensions = {
            ".pdf",
            ".doc",
            ".docx",
        }

        safe_filename = Path(resume.filename).name
        extension = Path(safe_filename).suffix.lower()

        if extension not in allowed_extensions:
            return templates.TemplateResponse(
                "account_profile.html",
                {
                    "request": request,
                    "profile": profile,
                    "success": None,
                    "error": "Only PDF, DOC, and DOCX files are allowed.",
                },
                status_code=400,
            )

        file_content = await resume.read()
        maximum_size = 5 * 1024 * 1024

        if len(file_content) > maximum_size:
            return templates.TemplateResponse(
                "account_profile.html",
                {
                    "request": request,
                    "profile": profile,
                    "success": None,
                    "error": "The resume must not exceed 5 MB.",
                },
                status_code=400,
            )

        destination = UPLOAD_DIRECTORY / safe_filename
        destination.write_bytes(file_content)

        profile["resume_filename"] = safe_filename

    return templates.TemplateResponse(
        "account_profile.html",
        {
            "request": request,
            "profile": profile,
            "success": "Account profile saved successfully.",
            "error": None,
        },
    )


# ==========================================================
# SEARCH DASHBOARD ROUTES
# ==========================================================

@app.get(
    "/search-dashboard",
    response_class=HTMLResponse,
)
def search_dashboard(
    request: Request,
):
    with Session(database.engine) as db:
        stats = crud.get_search_stats(db)
        records = crud.get_search_records(
            db=db,
            skip=0,
            limit=100,
        )

    return templates.TemplateResponse(
        "search_dashboard.html",
        {
            "request": request,
            "total_records": stats["total_records"],
            "uploaded_records": stats["uploaded_records"],
            "pending_records": stats["pending_records"],
            "records": records,
        },
    )


@app.post("/search-dashboard/create")
def create_search_record(
    topic: str = Form(...),
    question: str = Form(...),
    uploaded: bool = Form(False),
):
    with Session(database.engine) as db:
        record = models.SearchRecord(
            topic=topic,
            question=question,
            uploaded=uploaded,
        )

        db.add(record)
        db.commit()

    return RedirectResponse(
        url="/search-dashboard",
        status_code=303,
    )


@app.get(
    "/search-dashboard/edit/{record_id}",
    response_class=HTMLResponse,
)
def edit_record(
    record_id: int,
    request: Request,
):
    with Session(database.engine) as db:
        record = db.get(
            models.SearchRecord,
            record_id,
        )

        if not record:
            return RedirectResponse(
                url="/search-dashboard",
                status_code=303,
            )

    return templates.TemplateResponse(
        "edit_record.html",
        {
            "request": request,
            "record": record,
        },
    )


@app.post("/search-dashboard/update/{record_id}")
def update_record(
    record_id: int,
    topic: str = Form(...),
    question: str = Form(...),
    uploaded: bool = Form(False),
):
    with Session(database.engine) as db:
        record = db.get(
            models.SearchRecord,
            record_id,
        )

        if record:
            record.topic = topic
            record.question = question
            record.uploaded = uploaded

            db.add(record)
            db.commit()

    return RedirectResponse(
        url="/search-dashboard",
        status_code=303,
    )


@app.post("/search-dashboard/delete/{record_id}")
def delete_search_dashboard_record(
    record_id: int,
):
    with Session(database.engine) as db:
        record = db.get(
            models.SearchRecord,
            record_id,
        )

        if record:
            db.delete(record)
            db.commit()

    return RedirectResponse(
        url="/search-dashboard",
        status_code=303,
    )


# ==========================================================
# JOB DETAILS HTML ROUTES
# ==========================================================

@app.get(
    "/application/jobs/pages/list",
    response_class=HTMLResponse,
    tags=["Job Details"],
)
def jobs_page(
    request: Request,
    search: Optional[str] = None,
    project_type: Optional[str] = None,
    engagement_level: Optional[str] = None,
    status: Optional[str] = None,
    session: Session = Depends(get_db),
):
    statement = select(JobDetails)

    if search:
        statement = statement.where(
            JobDetails.title.contains(search)
        )

    if project_type:
        statement = statement.where(
            JobDetails.project_type == project_type
        )

    if engagement_level:
        statement = statement.where(
            JobDetails.engagement_level == engagement_level
        )

    if status:
        statement = statement.where(
            JobDetails.status == status
        )

    jobs = session.exec(statement).all()
    all_jobs = session.exec(
        select(JobDetails)
    ).all()

    total_jobs = len(all_jobs)
    open_jobs = len(
        [job for job in all_jobs if job.status == "open"]
    )
    draft_jobs = len(
        [job for job in all_jobs if job.status == "draft"]
    )
    closed_jobs = len(
        [job for job in all_jobs if job.status == "closed"]
    )

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
            "closed_jobs": closed_jobs,
        },
    )


@app.get(
    "/application/jobs/pages/create/form",
    response_class=HTMLResponse,
    tags=["Job Details"],
)
def create_job_form(
    request: Request,
):
    return templates.TemplateResponse(
        "JobDetails_create.html",
        {
            "request": request,
        },
    )


@app.post(
    "/application/jobs/pages/create/form",
    tags=["Job Details"],
)
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
    session: Session = Depends(get_db),
):
    if payment_max < payment_min:
        raise HTTPException(
            status_code=400,
            detail="Maximum payment cannot be less than minimum payment",
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
        status=status,
    )

    session.add(job)
    session.commit()
    session.refresh(job)

    return RedirectResponse(
        url="/application/jobs/pages/list",
        status_code=303,
    )


@app.get(
    "/application/jobs/pages/{job_id}",
    response_class=HTMLResponse,
    tags=["Job Details"],
)
def job_detail_page(
    job_id: int,
    request: Request,
    session: Session = Depends(get_db),
):
    job = session.get(
        JobDetails,
        job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    skills = []

    if job.skills_required:
        skills = [
            skill.strip()
            for skill in job.skills_required.replace(
                "\n",
                ",",
            ).split(",")
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
            "links": links,
        },
    )


@app.get(
    "/application/jobs/pages/{job_id}/edit",
    response_class=HTMLResponse,
    tags=["Job Details"],
)
def edit_job_form(
    job_id: int,
    request: Request,
    session: Session = Depends(get_db),
):
    job = session.get(
        JobDetails,
        job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return templates.TemplateResponse(
        "JobDetails_edit.html",
        {
            "request": request,
            "job": job,
        },
    )


@app.post(
    "/application/jobs/pages/{job_id}/edit",
    tags=["Job Details"],
)
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
    session: Session = Depends(get_db),
):
    job = session.get(
        JobDetails,
        job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if payment_max < payment_min:
        raise HTTPException(
            status_code=400,
            detail="Maximum payment cannot be less than minimum payment",
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
        status_code=303,
    )


@app.post(
    "/application/jobs/pages/{job_id}/delete",
    tags=["Job Details"],
)
def delete_job_from_page(
    job_id: int,
    session: Session = Depends(get_db),
):
    job = session.get(
        JobDetails,
        job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    session.delete(job)
    session.commit()

    return RedirectResponse(
        url="/application/jobs/pages/list",
        status_code=303,
    )


# ==========================================================
# JOB DETAILS API ROUTES
# ==========================================================

@app.get(
    "/application/jobs/",
    response_model=List[JobDetails],
    tags=["Job Details"],
)
def list_jobs(
    search: Optional[str] = None,
    project_type: Optional[str] = None,
    engagement_level: Optional[str] = None,
    status: Optional[str] = None,
    session: Session = Depends(get_db),
):
    statement = select(JobDetails)

    if search:
        statement = statement.where(
            JobDetails.title.contains(search)
        )

    if project_type:
        statement = statement.where(
            JobDetails.project_type == project_type
        )

    if engagement_level:
        statement = statement.where(
            JobDetails.engagement_level == engagement_level
        )

    if status:
        statement = statement.where(
            JobDetails.status == status
        )

    return session.exec(statement).all()


@app.post(
    "/application/jobs/",
    response_model=JobDetails,
    status_code=201,
    tags=["Job Details"],
)
def create_job(
    job: JobDetailsCreate,
    session: Session = Depends(get_db),
):
    if job.payment_max < job.payment_min:
        raise HTTPException(
            status_code=400,
            detail="payment_max cannot be less than payment_min",
        )

    job_data = (
        job.model_dump()
        if hasattr(job, "model_dump")
        else job.dict()
    )

    db_job = JobDetails(**job_data)

    session.add(db_job)
    session.commit()
    session.refresh(db_job)

    return db_job


@app.get(
    "/application/jobs/{job_id}",
    response_model=JobDetails,
    tags=["Job Details"],
)
def get_job(
    job_id: int,
    session: Session = Depends(get_db),
):
    job = session.get(
        JobDetails,
        job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job


@app.patch(
    "/application/jobs/{job_id}",
    response_model=JobDetails,
    tags=["Job Details"],
)
def update_job(
    job_id: int,
    job_update: JobDetailsUpdate,
    session: Session = Depends(get_db),
):
    job = session.get(
        JobDetails,
        job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    update_data = (
        job_update.model_dump(exclude_unset=True)
        if hasattr(job_update, "model_dump")
        else job_update.dict(exclude_unset=True)
    )

    for key, value in update_data.items():
        setattr(
            job,
            key,
            value,
        )

    if job.payment_max < job.payment_min:
        raise HTTPException(
            status_code=400,
            detail="payment_max cannot be less than payment_min",
        )

    job.updated_at = datetime.utcnow()

    session.add(job)
    session.commit()
    session.refresh(job)

    return job


@app.delete(
    "/application/jobs/{job_id}",
    tags=["Job Details"],
)
def delete_job(
    job_id: int,
    session: Session = Depends(get_db),
):
    job = session.get(
        JobDetails,
        job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    session.delete(job)
    session.commit()

    return {
        "message": "Job deleted successfully"
    }
# '''

# compile(code, str(output), "exec")
# output.write_text(code, encoding="utf-8")

# print(f"Created {output}")
