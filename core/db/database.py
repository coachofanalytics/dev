# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from core.config.settings import Settings

# from core.config.utils import get_settings


def get_db():
    """DB Session Dependency for App APIs"""
    settings = Settings()

    if settings.SQL_DIALECT == "postgresql" and settings.MSI_SECRET:
        conn_str = settings.get_postgres_engine()
        engine = create_engine(
            conn_str,
            echo=settings.debug,
            pool_pre_ping=True,
            poolclass=NullPool,
        )
    else:
        engine = create_engine(
            settings.get_connection_string(),
            echo=settings.debug,
            pool_pre_ping=True,
            poolclass=NullPool,
            use_insertmanyvalues=True,
        ).execution_options(insertmanyvalues_page_size=32767)

    db = Session(engine, future=True)
    try:
        yield db
    finally:
        db.close()
        engine.dispose()
