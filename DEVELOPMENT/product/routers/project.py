from fastapi import status, Response, HTTPException, APIRouter
from fastapi.params import Depends
from  product.database import get_db
from sqlalchemy.orm import Session
from product import schemas, models
from typing import List


router = APIRouter(
    tags=['Projects']
)

# Create a Project
@router.post('/project', status_code=status.HTTP_201_CREATED, response_model=schemas.DisplayProject)
def create_project(request:schemas.Project, db:Session=Depends(get_db)):
    new_project = models.Project(
        name = request.name,
        user_id = 1,
    )
    db.add(new_project)
    db.commit()
    return request