from fastapi import FastAPI
from api.routers import users

app = FastAPI(
    title="FastAPI App",
    description="FastAPI application with SQLAlchemy",
    version="1.0.0",
)

# Include routers
app.include_router(users.router)


@app.get("/")
async def home():
    return {"message": "Welcome to FastAPI"}
