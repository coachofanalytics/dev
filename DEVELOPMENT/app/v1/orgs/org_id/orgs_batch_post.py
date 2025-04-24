# import uuid
# from datetime import datetime
# from fastapi import APIRouter, Depends, Request, status
# from sqlalchemy.orm import Session
# # Import Core Sub-Modules
# from app.core.db.database import get_db
# from app.core.models.orgs.org_id.orgs import Orgs
# from app.core.schemas.orgs.org_id.orgs_base import OrgSchema

# # Router is required
# router = APIRouter(
#     tags = ['orgs']
# )

# @router.post(
#     "/orgs/batch",
#     tags=["Organizations"],
#     response_model=OrgsBatchResponse,
# )
# @custom_exception_handler
# def orgs_batch(
#     request: Request, orgs_data: OrgsBatchFilter, db: Session = Depends(get_db)
# ):
#     # Fetch and validate user
#     user_data = get_user(request, metadata=True)
#     validate_user_access(
#         expected_access_level=["Admin", "User", "Viewer"],
#         actual_access_level=user_data["access_level"],
#     )

#     # Get project_id from orgs_data or fallback from DB
#     project_id = orgs_data.ids[0] if orgs_data.ids else None
#     orgs_id_list = orgs_data.filter_ids

#     if not project_id:
#         project_id = (
#             db.query(Orgs.project_id)
#             .filter(Orgs.id.in_(orgs_id_list))
#             .distinct()
#             .first()
#         )
#         project_id = project_id[0] if project_id else None

#     # Enforce access control for Users and Viewers
#     if "User" in user_data["access_level"] or "Viewer" in user_data["access_level"]:
#         check_user_access(
#             db=db, project_id=project_id, user_data=user_data, single_project=False
#         )

#     # Fetch organizations data
#     db_orgs_query = db.query(Orgs).filter(
#         Orgs.project_id == project_id, Orgs.is_active.is_(True)
#     )

#     if orgs_id_list:
#         db_orgs_query = db.query(Orgs).filter(Orgs.id.in_(orgs_id_list))

#     db_orgs_data = db_orgs_query.all()

#     if not db_orgs_data:
#         return OrgsBatchResponse(data=[], data_not_found=[])

#     org_ids = [item.id for item in db_orgs_data]

#     # Pull org hierarchy attributes
#     orgs_attributes = (
#         db.query(
#             Org_Hier.org_id,
#             func.max(Org_Hier.layer).label("number_of_layers"),
#             func.count().label("number_of_reportees"),
#         )
#         .group_by(Org_Hier.org_id)
#         .filter(Org_Hier.org_id.in_(org_ids))
#         .all()
#     )

#     # Convert to DataFrames and merge
#     orgs_attributes_df = pd.DataFrame(
#         orgs_attributes,
#         columns=["org_id", "number_of_layers", "number_of_reportees"]
#     )

#     orgs_data_df = pd.DataFrame([item.__dict__ for item in db_orgs_data])
#     orgs_data_df = orgs_data_df.drop(columns=["_sa_instance_state"], errors='ignore')

#     master_df = (
#         orgs_data_df
#         .merge(orgs_attributes_df, left_on="id", right_on="org_id", how="left")
#         .drop(columns=["org_id"], errors='ignore')
#     )

#     for col in ["total_compensation", "number_of_layers", "number_of_reportees"]:
#         if col in master_df.columns:
#             master_df[col] = master_df[col].fillna(0)

#     return_object = master_df.to_dict(orient="records")

#     # Add related fields if requested
#     if orgs_data.fields:
#         fields = db.query(Fields).filter(Fields.org_id.in_(org_ids)).all()
#         for item in return_object:
#             item["fields"] = [
#                 field for field in fields if field.org_id == item["id"]
#             ]

#     # Detect missing orgs
#     orgs_not_found = detect_missing_ids_v2(
#         queried_data=return_object,
#         request_payload=orgs_data,
#         db_ids="project_id",
#         id_filter_ids="id",
#         queried_data_dict=True,
#     )

#     # Optional debug print
#     print("orgsBatchResponse:", {
#         "data_count": len(return_object),
#         "not_found_count": len(orgs_not_found),
#     })

#     return OrgsBatchResponse(
#         data=return_object,
#         data_not_found=orgs_not_found
#     )
