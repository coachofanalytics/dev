from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from core.config.settings import Settings

settings = Settings()
DB_SCHEMA = settings.db_schema

meta = MetaData(schema=DB_SCHEMA)
DjangoBase = declarative_base(metadata=meta)
