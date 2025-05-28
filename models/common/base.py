# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

from models.common.commonbase import CommonBase
from core.config.settings import Settings

settings = Settings()
DB_SCHEMA = settings.db_schema

meta = MetaData(schema=DB_SCHEMA)
Base = declarative_base(metadata=meta, cls=CommonBase)
