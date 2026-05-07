from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define the database URL (replace with your actual database URL)
DATABASE_URL = "sqlite:///./test.db"  # For SQLite or change to PostgreSQL, MySQL, etc.

# Create the database engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a sessionmaker for handling sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the base class for SQLAlchemy models
Base = declarative_base()