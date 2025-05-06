from fastapi import status, Response, HTTPException, APIRouter,Request
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.core.schemas.industry.industry_base import DisplayIndustrySchema
from app.core.models.industry.industry import Industry
from typing import List
from app.routers.login import get_current_user


from app.core.db.database import get_db
from app.core.models.orgs.org_id.orgs import Orgs
from app.core.models.industry.industry import Industry
from app.core.models.projects.projects import Projects
from app.core.schemas.orgs.org_id.orgs_base import OrgSchema
from app.core.authenticator.auth import get_user
from app.utils.check_access import  check_user_access

# app/main.py
from fastapi import FastAPI, HTTPException, Query
from azure.storage.blob import BlobServiceClient
import pandas as pd
import io
import os


from azure.storage.blob import BlobServiceClient


# Initialize BlobServiceClient
# # conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
# conn_str = "https://codanalytics.blob.core.windows.net/?sv=2024-11-04&ss=bfqt&srt=c&sp=rwdlacupiytfx&se=2026-05-03T10:06:56Z&st=2025-05-03T02:06:56Z&spr=https&sig=vbtri66fxk627xmZjV4tICR6JfyY2EiBKUGpxg4EWTk%3D"
# if not conn_str:
#     raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING is not set")

# # blob_service = BlobServiceClient.from_connection_string(conn_str)
# blob_service = BlobServiceClient(conn_str)
# container_client = blob_service.get_container_client("kpm")

# print("WE ARE HERE")


# # Router is required
# router = APIRouter(
#     tags=['Azure_data_lake'],
#     # prefix="/industry"
# )

# @router.get("/data/", summary="Fetch CSV data as JSON")
# def get_csv_data(

#     request:Request,
#     filename: str = Query(..., description="Name of the CSV blob, e.g. 'records.csv'"),
#     db: Session = Depends(get_db)):

#     """
#     Downloads `filename` from the blob container, parses it, and returns JSON.
#     """
#     print('HERE AZURE')
#     try:
#         blob_client = container_client.get_blob_client(blob=filename)
#         downloader = blob_client.download_blob()
#         data = downloader.readall()
#     except Exception:
#         raise HTTPException(status_code=404, detail=f"Blob not found: {filename}")

#     try:
#         df = pd.read_csv(io.BytesIO(data))
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

#     print("NOW HERE")
    
#     records = df.to_dict(orient="records")
#     return {
#         "filename": filename,
#         "row_count": len(records),
#         "data": records
#     }



# app = FastAPI(title="CSV → JSON API")

# # Initialize BlobServiceClient
# # conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
# conn_str = "https://codanalytics.blob.core.windows.net/?sv=2024-11-04&ss=bfqt&srt=c&sp=rwdlacupiytfx&se=2026-05-03T10:06:56Z&st=2025-05-03T02:06:56Z&spr=https&sig=vbtri66fxk627xmZjV4tICR6JfyY2EiBKUGpxg4EWTk%3D"
# if not conn_str:
#     raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING is not set")

# # blob_service = BlobServiceClient.from_connection_string(conn_str)
# blob_service = BlobServiceClient(conn_str)
# container_client = blob_service.get_container_client("kpm")

# print("WE ARE HERE")

# @app.get("/data/", summary="Fetch CSV data as JSON")
# def get_csv_data(
#     filename: str = Query(..., description="Name of the CSV blob, e.g. 'records.csv'")
# ):
#     """
#     Downloads `filename` from the blob container, parses it, and returns JSON.
#     """
#     try:
#         blob_client = container_client.get_blob_client(blob=filename)
#         downloader = blob_client.download_blob()
#         data = downloader.readall()
#     except Exception:
#         raise HTTPException(status_code=404, detail=f"Blob not found: {filename}")

#     try:
#         df = pd.read_csv(io.BytesIO(data))
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

#     print("NOW HERE")
    
#     records = df.to_dict(orient="records")
#     return {
#         "filename": filename,
#         "row_count": len(records),
#         "data": records
#     }



# Replace with your Blob service SAS URL
sas_url = "https://codanalytics.blob.core.windows.net/?sv=2024-11-04&ss=bfqt&srt=c&sp=rwdlacupiytfx&se=2026-05-03T10:06:56Z&st=2025-05-03T02:06:56Z&spr=https&sig=vbtri66fxk627xmZjV4tICR6JfyY2EiBKUGpxg4EWTk%3D"

# Create the BlobServiceClient using the SAS URL
blob_service_client = BlobServiceClient(account_url=sas_url)

# Access the container (replace with your actual container name)
container_name = 'kpm'
container_client = blob_service_client.get_container_client(container_name)

# Router is required
router = APIRouter(
    tags=['Azure_data_lake'],
    # prefix="/industry"
)

@router.get("/data/", summary="Fetch CSV data as JSON")
def get_csv_data(
):
# List all blobs in the container
    blobs = container_client.list_blobs()
    csv_file=None
    for blob in blobs:
        csv_file = blob.name
        print(f"Blob Name: {blob.name}")

    # csv_file=[blob.name for blob in blobs]
    print(f"Blob Name: {csv_file}")

    try:
        blob_client = container_client.get_blob_client(blob='fastapi.csv')
        print(blob_client)
        downloader = blob_client.download_blob()
        print(downloader)
        data = downloader.readall()
        print(data)
    except Exception as e:
        # Raise a detailed 404 error
        raise HTTPException(status_code=404, detail=f"Blob not found: {e}")

    try:
        df = pd.read_csv(io.BytesIO(data))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

    print("NOW HERE")
    
    records = df.to_dict(orient="records")
    return {
        "filename": filename,
        "row_count": len(records),
        "data": records
    }