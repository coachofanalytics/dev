# -*- coding: utf-8 -*-
from app.core.models.access.access import Access


def check_user_access(db, user_data, single_project=True):
    """checking access to the project"""
    if single_project:
        user_access_data = (
            db.query(Access)
            .filter(Access.user_id == user_data["id"])
            .all()
        )
    else:
        user_access_data = (
            db.query(Access)
            .filter(
                Access.project_id.in_([project_id]), Access.user_id == user_data["id"]
            )
            .all()
        )
    if len(user_access_data) != 1:
        raise ValueError(
            "User does not have access to this project. "
            "Please contact project owners or administrators"
        )


# def check_user_access(db, project_id='4443dfhedfd94394', user_data, single_project=True):
#     """checking access to the project"""
#     if single_project:
#         user_access_data = (
#             db.query(Access)
#             .filter(Access.project_id == project_id, Access.user_id == user_data["id"])
#             .all()
#         )
#     else:
#         user_access_data = (
#             db.query(Access)
#             .filter(
#                 Access.project_id.in_([project_id]), Access.user_id == user_data["id"]
#             )
#             .all()
#         )
#     if len(user_access_data) != 1:
#         raise ValueError(
#             "User does not have access to this project. "
#             "Please contact project owners or administrators"
#         )
