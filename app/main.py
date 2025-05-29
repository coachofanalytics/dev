from fastapi import FastAPI
from app.core.models.transactions import transaction
from app.core.db.database import engine
from app.v1.transactions import transaction_delete, transaction_post, transaction_update, transaction_get



# Initialize fastAPI
app = FastAPI()


# Create database tables from the models declared in models.py 
transaction.Base.metadata.create_all(engine)


# Register endpoints
app.include_router(transaction_get.router)
app.include_router(transaction_update.router)
app.include_router(transaction_post.router)
app.include_router(transaction_delete.router)