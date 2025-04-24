# import uuid
# from datetime import datetime
# from fastapi import APIRouter, Depends, Request, status
# from sqlalchemy.orm import Session

# # Import Core Sub-Modules
# from app.core.db.database import get_db
# from app.core.models.positions.positions import Positions
# from app.core.schemas.positions.positions_base import PositionSchema, PositionResponseSchema

# # Router is required
# router = APIRouter(
#     tags = ['Positions']
# )

# @router.post(
#     "/positions/batch",
#     response_model=PositionResponseSchema,
#     tags=["Positions"],
#     status_code=status.HTTP_201_CREATED,
#     summary="Fetch Information on Positions",
# )
# @custom_exception_handler
# def ext_positions_batch(positions_data: PositionsFilter, db: Session = Depends(get_db)):
#     org_id = positions_data.ids[0] if positions_data.ids else None
#     position_ids = positions_data.filter_ids

#     db_positions = (
#         db.query(Positions)
#         .join(
#             Association_Org_Position,
#             Positions.id == Association_Org_Position.position_id,
#         )
#         .filter(Association_Org_Position.org_id == org_id)
#     )

#     if position_ids:
#         db_positions = db.query(Positions).filter(Positions.id.in_(position_ids))

#     db_positions_data = db_positions.all()

#     position_not_found = detect_missing_ids_v2(
#         queried_data=db_positions_data,
#         request_payload=positions_data,
#         db_ids=None,
#         db_filter_ids="id",
#     )

#     db_position_object = {
#         "data": db_positions_data,
#         "data_not_found": position_not_found,
#     }

#     return db_position_object


