from fastapi import APIRouter
import snowflake.connector
import pandas as pd
import os
import requests
from io import StringIO
from azure.storage.blob import BlobServiceClient
from io import BytesIO

router = APIRouter()

import logging
from typing import Union
from sqlalchemy import desc, select, Column
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.models import Base


def get_data(
    db: Session,
    orm_model: Base,
    order_desc: bool = False,
    order_by_col: object = None,
    limit: int = 0,
    dataframe: bool = False,
    filter_value: Union[int, str] = 0,
    orm_filter_field: Column = None,
    expect_single_record: bool = False,
) -> list[Base]:
   
    statement = select(orm_model)

    # If provided a id and id field we will filter to matches
    if filter_value and orm_filter_field:
        statement = statement.where(orm_filter_field == filter_value)

    # Order data
    if order_desc and order_by_col:
        statement = statement.order_by(desc(order_by_col))
    elif not order_desc and order_by_col:
        statement = statement.order_by(order_by_col)

    if limit > 0:
        statement = statement.limit(limit)
    data = db.execute(statement).scalars().all()

    # Validate that data is not empty or != 1 if we expect it to be
    if len(data) == 0:
        message = "No record found"
        logging.info(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    if len(data) != 1 and expect_single_record:
        message = f"Expected 1 record, Actual {len(data)}"
        logging.error(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    if expect_single_record:
        return data[0]

    return data


@router.get("/datalake/azure")
def fetch_from_azure(container_name: str, blob_name: str):
    try:
        print(f"🔄 Connecting to Azure Blob: Container={container_name}, Blob={blob_name}")
        blob_service = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)

        print("📥 Downloading blob content...")
        download_stream = blob_client.download_blob()
        content = download_stream.readall()

        print("📊 Converting blob to DataFrame...")
        df = pd.read_csv(BytesIO(content))  # Use read_parquet() if needed

        print("✅ Successfully fetched and converted data")
        return {"data": df.to_dict(orient="records")}
    
    except Exception as e:
        print(f"❌ Error fetching from Azure: {e}")
        return {"error": str(e)}


# @router.get("/datalake/snowflake")
# def fetch_from_snowflake(query: str):
#     try:
#         print("🔄 Connecting to Snowflake...")
#         conn = snowflake.connector.connect(
#             user=os.getenv("SNOWFLAKE_USER"),
#             password=os.getenv("SNOWFLAKE_PASSWORD"),
#             account=os.getenv("SNOWFLAKE_ACCOUNT"),
#             warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
#             database=os.getenv("SNOWFLAKE_DATABASE"),
#             schema=os.getenv("SNOWFLAKE_SCHEMA"),
#         )

#         print(f"📊 Executing query: {query}")
#         cursor = conn.cursor()
#         cursor.execute(query)
#         df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

#         cursor.close()
#         conn.close()

#         print("✅ Query successful and data fetched")
#         return {"data": df.to_dict(orient="records")}

#     except Exception as e:
#         print(f"❌ Error querying Snowflake: {e}")
#         return {"error": str(e)}






# @router.get("/datalake/databricks")
# def fetch_from_databricks(path: str):
#     DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
#     DATABRICKS_HOST = "https://<your-workspace>.cloud.databricks.com"
#     try:
#         print(f"🔄 Fetching file from Databricks DBFS: {path}")
#         url = f"{DATABRICKS_HOST}/api/2.0/dbfs/read"
#         headers = {"Authorization": f"Bearer {DATABRICKS_TOKEN}"}
#         payload = {"path": path}

#         response = requests.get(url, headers=headers, params=payload)

#         if response.status_code == 200:
#             print("📥 File successfully fetched from Databricks DBFS")
#             import base64
#             content = base64.b64decode(response.json()['data']).decode()

#             print("📊 Parsing CSV from response...")
#             df = pd.read_csv(StringIO(content))  # Adjust to your file format

#             print("✅ Data processed successfully")
#             return {"data": df.to_dict(orient="records")}
#         else:
#             print(f"❌ Databricks API error: {response.status_code} - {response.text}")
#             return {"error": response.text}
    
#     except Exception as e:
#         print(f"❌ Exception while fetching from Databricks: {e}")
#         return {"error": str(e)}
