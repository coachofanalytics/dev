from fastapi import FastAPI

from . import models, database
from .routers import transactions

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.include_router(transactions.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI!"}


@app.get("/hello")
def hello():
    return {"message": "Hello, world!"}