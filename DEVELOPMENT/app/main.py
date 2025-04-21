from fastapi import FastAPI
from app.core.models.industry import industry
from app.core.models.projects import projects
from app.core.models.depts import departments
from app.core.models.locations import locations
from app.core.models.positions import positions
from app.core.models.ext_positions import ext_positions
from app.core.models.orgs_hierarchy import orgs_hierarchy
from app.core.models.orgs.org_id import orgs
from app.core.db.database import engine
from app import models
from app.routers import product, user, project, login
from app.v1.industry import industry_get
from app.v1.projects import project_post
from app.v1.depts import depts_batch_post
from app.v1.locations import locations_batch_post
from app.v1.positions import positions_batch_post
from app.v1.ext_positions import ext_positions_batch_post
from app.v1.orgs_hierarchy import orgs_hierarchy_batch_post
from app.v1.orgs.org_id import orgs_batch_post, orgs_post, orgs_edit, orgs_delete




# Initialize fastAPI
app = FastAPI(
    # title="Products API",
    # description = "Fetch the details for all products on our website"
)

# creats the database tables from models declared in models.py
industry.Base.metadata.create_all(engine)
projects.Base.metadata.create_all(engine)
departments.Base.metadata.create_all(engine)
locations.Base.metadata.create_all(engine)
positions.Base.metadata.create_all(engine)
ext_positions.Base.metadata.create_all(engine)
orgs_hierarchy.Base.metadata.create_all(engine)
orgs.Base.metadata.create_all(engine)
models.Base.metadata.create_all(engine)


app.include_router(product.router)
app.include_router(user.router)
app.include_router(project.router)
app.include_router(login.router)
#------------------------------------------------------------
app.include_router(industry_get.router)
app.include_router(project_post.router)
app.include_router(depts_batch_post.router)
app.include_router(locations_batch_post.router)
app.include_router(positions_batch_post.router)
app.include_router(ext_positions_batch_post.router)
app.include_router(orgs_hierarchy_batch_post.router)
app.include_router(orgs_batch_post.router)
app.include_router(orgs_post.router)
app.include_router(orgs_edit.router)
app.include_router(orgs_delete.router)