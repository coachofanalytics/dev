from pydantic import BaseSettings, Field


class SQLSubModule(BaseSettings):
    """SQL Settings submodule"""

    # Original environment variable based settings
    sql_uid: str = Field(..., alias="SQL_UID")
    sql_pwd: str = Field(..., alias="SQL_PWD")
    driver: str = Field("ODBC Driver 17 for SQL Server", alias="SQL_DRIVER")
    server: str = Field(..., alias="SQL_SERVER")
    database: str = Field(..., alias="APP_DATABASE")


    class Config:
        case_sensitive = True


class DBSubModule(BaseSettings):
    """Database Settings submodule"""

    # Original environment variable based settings
    db_schema: str = Field("public", alias="APP_DB_SCHEMA")

    # Hardcoded values for development
    # db_schema: str = "public"

    @property
    def table_args(self):
        return {"schema": self.db_schema}

    class Config:
        case_sensitive = True
