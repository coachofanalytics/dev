from fastapi import FastAPI
from api.routers import users
from core.domain.authenticator.jwt_token import create_access_token

print(create_access_token())

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
