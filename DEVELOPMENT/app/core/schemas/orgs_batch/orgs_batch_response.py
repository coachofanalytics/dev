# -*- coding: utf-8 -*-

from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict
from app.core.schemas.common import BaseSchema
from app.core.schemas.filtering import ResponseFilterClass
from app.core.schemas.orgs_batch.orgs_batch_new import OrgsBatchNew

# class OrgsBatchResponse(BaseSchema):
#     """Pydantic model for Depts Response"""

#     data: List[OrgsBatchNew] = Field(default_factory=list)
#     data_not_found: ResponseFilterClass = Field(alias="dataNotFound")


class OrgsBatchResponse(BaseSchema):
    data: list
    data_not_found: dict = Field(alias="dataNotFound")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid"  # or "allow" if needed
    )