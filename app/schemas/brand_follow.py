"""BrandFollow schemas"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .base import BaseSchema

if TYPE_CHECKING:
    from .brand import BrandResponse


class BrandFollowBase(BaseSchema):
    """Base brand follow schema"""
    user_id: str = Field(..., max_length=36)
    brand_id: str = Field(..., max_length=36)


class BrandFollowCreate(BrandFollowBase):
    """Schema for creating a brand follow"""
    id: str = Field(..., max_length=36)


class BrandFollowResponse(BrandFollowBase):
    """Schema for brand follow response"""
    id: str
    created_at: datetime
    updated_at: datetime


class BrandFollowWithBrand(BrandFollowResponse):
    """Schema for brand follow response with brand details"""
    brand: Optional[BrandResponse] = None
