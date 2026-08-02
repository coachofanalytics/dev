from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import (
    Session,
    SQLModel,
    create_engine,
)
from sqlmodel.pool import StaticPool

from app.database import get_db
from app.main import app


@pytest.fixture(name="session")
def session_fixture() -> Generator[
    Session,
    None,
    None,
]:
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(
    session: Session,
) -> Generator[
    TestClient,
    None,
    None,
]:
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = (
        override_get_db
    )

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()