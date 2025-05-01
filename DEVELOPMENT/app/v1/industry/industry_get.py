from fastapi import status, Response, HTTPException, APIRouter,Request
from fastapi.params import Depends
from  app.core.db.database import get_db
from sqlalchemy.orm import Session
from app.core.schemas.industry.industry_base import DisplayIndustrySchema
from app.core.models.industry.industry import Industry
from typing import List
from app.routers.login import get_current_user


from app.core.db.database import get_db
from app.core.models.orgs.org_id.orgs import Orgs
from app.core.models.industry.industry import Industry
from app.core.models.projects.projects import Projects
from app.core.schemas.orgs.org_id.orgs_base import OrgSchema
from app.core.authenticator.auth import get_user
from app.utils.check_access import  check_user_access

# Router is required
router = APIRouter(
    tags=['Industry'],
    # prefix="/industry"
)

@router.get('/industry', response_model=List[DisplayIndustrySchema])
def get_industrys(
    request:Request,
    db: Session = Depends(get_db)):
    
    # print('here')

    # Fetch and validate user
    user_data = get_user(request, metadata=True)
    print(user_data) 
    # print(user_data["access_level"],user_data["email"])
    # validate_user_access(
    #     expected_access_level=["Admin", "User", "Viewer"],
    #     actual_access_level=user_data["access_level"],
    # )

    # # Enforce access control for Users and Viewers
    if "User" in user_data["access_level"] or "Viewer" in user_data["access_level"]:
        print("Type of User :",user_data["access_level"])
        check_user_access(
            db=db,user_data=user_data, single_project=False
        )

        # check_user_access(
        #     db=db, project_id=project_id, user_data=user_data, single_project=False
        # )

    industry = db.query(Industry).all()
    return industry





