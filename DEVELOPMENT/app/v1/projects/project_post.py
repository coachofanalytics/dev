import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

# Import Core Sub-Modules
from app.core.db.database import get_db
# from app.core.decorators import custom_exception_handler
# from app.core.authentication.auth import get_user, validate_user_access
# from app.core.models import Projects, Access
from app.core.models.projects.projects import Projects
# from app.core.schemas.projects import ProjectsCreate, ProjectResponse
from app.core.schemas.projects.project_create import ProjectsCreate #ProjectSchema

# Router is required
router = APIRouter(
    tags = ['Projects']
)

# @router.post("/projects",
#     response_model=ProjectResponse,
#     tags=["Projects"],
#     status_code=status.HTTP_201_CREATED,
#     summary="Creates a new project")

# @custom_exception_handler
# def projects_post(request: Request, project_data: ProjectsCreate, db: Session = Depends(get_db)):
#     user_data = get_user(request, metadata=True)
#     is_user_auth = validate_user_access(["Admin", "User"], user_data["access_level"])
#     project_id = uuid.uuid4()

#     if is_user_auth:
#         new_project = Projects(
#             id=project_id,
#             name=project_data.name,
#             description=project_data.description,
#             engagement_code=project_data.engagement_code,
#             engagement_type=project_data.engagement_type,
#             partner=project_data.partner,
#             is_active=True,
#             created_by=user_data["name"],
#             creator_name=user_data["name"],
#             created_date=datetime.utcnow(),
#         )

#         user_list = project_data.access
#         if "Admin" not in user_data["access_level"]:
#             user_list.append(user_data["id"])
        
#         if len(user_list) != 0:
#             new_project.access = [
#                 Access(
#                     id=uuid.uuid4(),
#                     user_id=x,
#                     project_id=new_project.id,
#                     access_level="base",
#                     created_date=datetime.utcnow(),
#                     created_by=x,
#                 ) for x in user_list
#             ]

#         new_project.save(db)
#         db.refresh(new_project)
#         return new_project


# @router.post('/project', status_code=status.HTTP_201_CREATED)
# def create_project(request:ProjectSchema, db:Session=Depends(get_db)):
#     new_project = Projects(
#         name = request.name,
#         description = request.description,
#         engagement_code = request.engagement_code,
#         engagement_type = request.engagement_type,
#         partner = request.partner,
#         is_active = request.is_active,
#         creator_name = request.creator_name,
#         id = request.id,
#         created_by = request.created_by,
#         created_date = request.created_date,
#         updated_by = request.updated_by,
#         updated_date = request.updated_date,

#     )
#     db.add(new_project)
#     db.commit()
#     return request

