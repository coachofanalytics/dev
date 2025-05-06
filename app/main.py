from fastapi import FastAPI
from app.core.models.industry import industry
from app.core.db.database import engine
from app.v1.industry import industry_get


# Initialize fastAPI
app = FastAPI()

# creats the database tables from models declared in models.py
industry.Base.metadata.create_all(engine)


# Registers the endpoints
app.include_router(industry_get.router)
