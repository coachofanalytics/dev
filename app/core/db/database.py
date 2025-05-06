from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import dba_values

host,dbname,user,password,port = dba_values()

# Database URL: Format for PostgreSQL: 'postgresql://username:password@localhost:5432/dbname'
# DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/FASTAPI"
DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

# Create an engine for postgreSQL database connection
engine = create_engine(DATABASE_URL)

# Create a session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declare the base class for models
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()