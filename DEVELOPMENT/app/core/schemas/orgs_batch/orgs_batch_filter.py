# -*- coding: utf-8 -*-

from pydantic import Field
from app.core.schemas.filtering import FilterClass


class OrgsBatchFilter(FilterClass):
    """Pydantic Schema for filtering Depts table"""
