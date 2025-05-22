from fastapi import FastAPI
from app.core.models.industry import industry
from app.core.db.database import engine
from app.v1.industry import industry_get, industry_post, industry_update, industry_delete


# Initialize fastAPI
app = FastAPI()

# creats the database tables from models declared in models.py
industry.Base.metadata.create_all(engine)


# Registers the endpoints
app.include_router(industry_get.router)
app.include_router(industry_post.router)
app.include_router(industry_update.router)
app.include_router(industry_delete.router)
