from fastapi import FastAPI
from . import models
from  .database import engine
from .routers import product, user, project, login


# Initialize fastAPI
app = FastAPI(
    title="Products API",
    description = "Fetch the details for all products on our website"
)

# creats the database tables from models declared in models.py
models.Base.metadata.create_all(engine)


app.include_router(product.router)
app.include_router(user.router)
app.include_router(project.router)
app.include_router(login.router)