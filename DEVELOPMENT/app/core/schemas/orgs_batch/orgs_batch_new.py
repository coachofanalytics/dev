from typing import Optional, List
import uuid
from datetime import datetime, date
from pydantic import Field
from app.core.schemas.common import BaseSchema
from app.core.schemas.fields.fields import Fields


class OrgsBatchNew(BaseSchema):
    """Pydantic Schema for orgs_batch table"""

    id: uuid.UUID
    project_id: uuid.UUID = Field(alias="projectId")
    industry_id: uuid.UUID = Field(alias="industryId")
    name: str
    preceeding_org_id: Optional[uuid.UUID] = Field(alias="preceedingOrgLayer")
    description: Optional[str]
    is_sub_org: bool = Field(alias="isSubOrg")
    sub_org_desc: Optional[str] = Field(alias="subOrgDesc")
    is_benchmarked: bool = Field(alias="isBenchmarked")
    census_date: date = Field(alias="censusDate")
    raw_path: Optional[str] = Field(alias="rawPath")
    low_span_threshold: Optional[int] = Field(alias="lowSpanThreshold")
    is_low_span_threshold_changed: Optional[bool] = Field(
        alias="isLowSpanThresholdChanged"
    )
    benchmark_date: Optional[date] = Field(alias="benchmarkDate")
    is_avail_external: Optional[bool] = Field(alias="isAvailExternal")
    is_published: Optional[bool] = Field(alias="isPublished")
    published_desc: Optional[str] = Field(alias="publishedDesc")
    publisher: Optional[str]
    published_date: Optional[date] = Field(alias="publishedDate")
    publication_name: Optional[str] = Field(alias="publicationName")
    is_active: bool = Field(alias="isActive")
    created_date: Optional[datetime] = Field(alias="createdDate")
    updated_date: Optional[datetime] = Field(alias="updatedDate")
    created_by: Optional[uuid.UUID] = Field(alias="createdBy")
    updated_by: Optional[uuid.UUID] = Field(alias="updatedBy")
    total_compensation: Optional[float] = Field(alias="totalCompensation")
    number_of_reportees: Optional[int] = Field(alias="numberOfReportees", default=0)
    number_of_layers: Optional[int] = Field(alias="numberOfLayers", default=0)
    fields: Optional[List[Fields]]