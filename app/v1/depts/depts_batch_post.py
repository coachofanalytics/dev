import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

# Import Core Sub-Modules
from app.core.db.database import get_db
from app.core.models.depts.departments import Departments
from app.core.schemas.depts.depts_base import DepartmentSchema, DepartmentResponseSchema

# Router is required
router = APIRouter(
    tags = ['Departments']
)


@router.post('/department', status_code=status.HTTP_201_CREATED)
def add_department(request:DepartmentSchema, db: Session = Depends(get_db)):
    new_dept = Departments(
        bus_unit = request.bus_unit,
        bus_func = request.bus_func,
        bus_subfunc = request.bus_subfunc,
        created_by = request.created_by,
        created_date = request.created_date,
        updated_by = request.updated_by,
        updated_date = request.updated_date
    )
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    return request