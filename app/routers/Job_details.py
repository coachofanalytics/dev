from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import get_session
from app.models.job_details import JobDetails
from app.schemas.job_details import JobDetailsCreate, JobDetailsUpdate


router = APIRouter(
    prefix="/application/jobs",
    tags=["Job Details"]
)

templates = Jinja2Templates(directory="templates")

@router.get("/pages/list", response_class=HTMLResponse)
def jobs_page(
    request: Request,
    search: Optional[str] = None,
    session: Session = Depends(get_session)
):
    statement = select(JobDetails)

    if search:
        statement = statement.where(JobDetails.title.contains(search))

    jobs = session.exec(statement).all()

    return templates.TemplateResponse(
        "JobDetails_list.html",
        {
            "request": request,
            "jobs": jobs,
            "search": search
        }
    )


# -------------------------
# API: CREATE JOB
# -------------------------
@router.post("/", response_model=JobDetails)
def create_job(
    job: JobDetailsCreate,
    session: Session = Depends(get_session)
):
    if job.payment_max < job.payment_min:
        raise HTTPException(
            status_code=400,
            detail="payment_max cannot be less than payment_min"
        )

    db_job = JobDetails(**job.model_dump())
    session.add(db_job)
    session.commit()
    session.refresh(db_job)

    return db_job


# -------------------------
# API: UPDATE JOB
# -------------------------
@router.patch("/{job_id}", response_model=JobDetails)
def update_job(
    job_id: int,
    job_update: JobDetailsUpdate,
    session: Session = Depends(get_session)
):
    job = session.get(JobDetails, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    update_data = job_update.model_dump(exclude_unset=True)

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


# -------------------------
# NUMBER 7: HTML LIST PAGE
# -------------------------
@router.get("/pages/list", response_class=HTMLResponse)
def jobs_page(
    request: Request,
    search: Optional[str] = None,
    session: Session = Depends(get_session)
):
    statement = select(JobDetails)

    if search:
        statement = statement.where(JobDetails.title.contains(search))

    jobs = session.exec(statement).all()

    return templates.TemplateResponse(
        "job_details/list.html",
        {
            "request": request,
            "jobs": jobs,
            "search": search
        }
    )


# -------------------------
# NUMBER 7: HTML DETAIL PAGE
# -------------------------
@router.get("/pages/{job_id}", response_class=HTMLResponse)
def job_detail_page(
    request: Request,
    job_id: int,
    session: Session = Depends(get_session)
):
    job = session.get(JobDetails, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    skills = [
        skill.strip()
        for skill in job.skills_required.replace("\n", ",").split(",")
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
        "job_details/detail.html",
        {
            "request": request,
            "job": job,
            "skills": skills,
            "links": links
        }
    )


# -------------------------
# API: JOB DETAIL
# Keep this AFTER /pages/list and /pages/{job_id}
# -------------------------
@router.get("/{job_id}", response_model=JobDetails)
def get_job(
    job_id: int,
    session: Session = Depends(get_session)
):
    job = session.get(JobDetails, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


# -------------------------
# API: DELETE JOB
# -------------------------
@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    session: Session = Depends(get_session)
):
    job = session.get(JobDetails, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    session.delete(job)
    session.commit()

    return {"message": "Job deleted successfully"}