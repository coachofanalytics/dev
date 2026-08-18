from collections.abc import Generator

from sqlmodel import Session, create_engine


DATABASE_URL = "sqlite:///./user_groups.db"
DATABASE_URL = "sqlite:///./transaction.db"


engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={
        "check_same_thread": False,
    },
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session