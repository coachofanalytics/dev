from sqlmodel import create_engine, Session

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL, echo=True)

def SessionLocal():
    return Session(engine)