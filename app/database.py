from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from collections.abc import Generator
from sqlmodel import Session, create_engine


DATABASE_URL = "sqlite:///./fastapi.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()




DATABASE_URL ="sqlite:///user_groups.db"

engine = create_engine(DATABASE_URL,echo=True,connect_args={"check_same_thread":False}) 


def get_db():
    with Session(engine) as session:
        yield session