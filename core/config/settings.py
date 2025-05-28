# -*- coding: utf-8 -*-
# config.py
import os
from typing import Optional
from pydantic import BaseSettings, Field
from sqlalchemy.engine import URL

# from sqlalchemy.pool import NullPool


# class Settings(BaseSettings):
#     """API Settings Object"""
#     app_name: str = Field("Application Name", env="APP_NAME")
#     MSI_SECRET: Optional[str]
#     WEBSITE_HOSTNAME: Optional[str]
#     debug: bool = Field(False, env="DEBUG")
#     SQL_SETTINGS: SQLSubModule
#     DB_SETTINGS: DBSubModule
#     SQL_DIALECT: str = Field(..., env="SQL_DIALECT")
#     APP_ROOT_PATH: str = ""

#     def __init__(self, **kwargs):
#         print("\n=== Required Environment Variables ===")
#         print("SQL Settings:")
#         print(f"SQL_UID: {os.getenv('SQL_UID', 'MISSING')}")
#         print(f"SQL_PWD: {os.getenv('SQL_PWD', 'MISSING')}")
#         print(f"SQL_DRIVER: {os.getenv('SQL_DRIVER', 'MISSING')}")
#         print(f"SQL_SERVER: {os.getenv('SQL_SERVER', 'MISSING')}")
#         print(f"SQL_DATABASE: {os.getenv('SQL_DATABASE', 'MISSING')}")
#         print(f"SQL_DIALECT: {os.getenv('SQL_DIALECT', 'MISSING')}")
#         print("\nCurrent working directory:", os.getcwd())
#         print("Environment files being checked:", self.Config.env_file)
#         print("=====================================\n")
#         super().__init__(**kwargs)

#     class Config(BaseSettings.Config):
#         """Config sub object"""

#         WEBSITE_NAME = os.environ.get("WEBSITE_SITE_NAME", "")
#         lookup = {
#             "coda": ".env.dev",
#             "dck": ".env.qa",
#             "biashara": ".env.fpp.dev",
#         }

#         allow_mutation = False
#         case_sensitive = True
#         env_file = (
#             lookup.get(WEBSITE_NAME, ".env"),
#             ".env.local",
#         )
#         env_file_encoding = "utf-8"
#         env_nested_delimiter = "__"

#     def get_postgres_engine(self):
#         """Returns postgres engine for MSI"""
#         credential = DefaultAzureCredential()

#         # Acquire an access token for the PostgreSQL resource
#         token = credential.get_token(
#             "https://ossrdbms-aad.database.windows.net/.default"
#         )
#         user = os.environ["WEBSITE_SITE_NAME"]
#         return URL.create(
#             "postgresql",
#             username=user,
#             password=token.token,
#             host=self.SQL_SETTINGS.server,
#             port=5432,
#             database=self.SQL_SETTINGS.database,
#         )

#     def get_connection_string(self):
#         """Creates connection string for SQL database

#         Returns:
#             URL connection string
#         """
#         if self.SQL_DIALECT == "postgresql":
#             connection_object = URL.create(
#                 "postgresql",
#                 # username=self.SQL_SETTINGS.sql_uid,
#                 # password=self.SQL_SETTINGS.sql_pwd,
#                 # host=self.SQL_SETTINGS.server,
#                 # database=self.SQL_SETTINGS.database,
#                 username="postgres",
#                 password="MANAGER2030",
#                 host="localhost",
#                 database="CODA_DEV",
#             )
#             return connection_object
#         connection_string = (
#             f"DRIVER={self.SQL_SETTINGS.driver};"
#             f"SERVER={self.SQL_SETTINGS.server};"
#             f"DATABASE={self.SQL_SETTINGS.database};"
#         )
#         if self.MSI_SECRET:
#             connection_string += "Authentication=ActiveDirectoryMsi"
#         else:
#             connection_string += (
#                 f"Uid={self.SQL_SETTINGS.sql_uid};"
#                 f"Pwd={self.SQL_SETTINGS.sql_pwd};"
#                 "Encrypt=yes;"
#                 "TrustServerCertificate=yes;"
#                 "Connection Timeout=30;"
#             )
#         return URL.create(
#             "mssql+pyodbc",
#             query={"odbc_connect": connection_string},
#         )


class Settings(BaseSettings):
    """API Settings Object"""

    # Basic settings
    app_name: str = "CODA_APP"
    debug: bool = True
    APP_ROOT_PATH: str = ""

    # Database settings
    SQL_DIALECT: str = "postgresql"
    db_schema: str = Field(
        "public", alias="schema"
    )  # Using alias to maintain compatibility

    # Database connection settings
    db_host: str = os.environ.get("POSTGRESDB_HOST")
    db_name: str = os.environ.get("POSTGRES_DB_NAME")
    db_user: str = os.environ.get("POSTGRESDB_USER")
    db_password: str = os.environ.get("POSTGRESSPASS")
    db_port: int = 5432

    # Optional settings
    MSI_SECRET: Optional[str] = None
    WEBSITE_HOSTNAME: Optional[str] = None

    # Table configuration
    table_args: dict = {
        "mysql_collate": "utf8mb4_unicode_ci",
        "mysql_character": "utf8",
    }

    def get_postgres_engine(self):
        """Returns postgres engine for local development"""
        return URL.create(
            "postgresql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )

    def get_connection_string(self):
        """Creates connection string for SQL database"""
        if self.SQL_DIALECT == "postgresql":
            return URL.create(
                "postgresql",
                username=self.db_user,
                password=self.db_password,
                host=self.db_host,
                database=self.db_name,
            )

        # For MS SQL Server
        connection_string = (
            f"DRIVER={''};" f"SERVER={self.db_host};" f"DATABASE={self.db_name};"
        )
        if self.MSI_SECRET:
            connection_string += "Authentication=ActiveDirectoryMsi"
        else:
            connection_string += (
                f"Uid={self.db_user};"
                f"Pwd={self.db_password};"
                "Encrypt=yes;"
                "TrustServerCertificate=yes;"
                "Connection Timeout=30;"
            )
        return URL.create(
            "mssql+pyodbc",
            query={"odbc_connect": connection_string},
        )

    def dba_values(self):
        """Get database connection values based on environment"""
        if os.environ.get("ENVIRONMENT") == "production":
            return (
                os.environ.get("PROD_FASTAPI_DB_HOST"),
                os.environ.get("PROD_FASTAPI_DB_NAME"),
                os.environ.get("PROD_FASTAPI_DB_USER"),
                os.environ.get("PROD_FASTAPI_DB_PASS"),
                5432,
            )
        elif os.environ.get("ENVIRONMENT") == "staging":
            return (
                os.environ.get("STG_FASTAPI_DB_HOST"),
                os.environ.get("STG_FASTAPI_DB_NAME"),
                os.environ.get("STG_FASTAPI_DB_USER"),
                os.environ.get("STG_FASTAPI_DB_PASSWORD"),
                5432,
            )
        else:
            # Local development
            return (
                self.db_host,
                self.db_name,
                self.db_user,
                self.db_password,
                self.db_port,
            )
