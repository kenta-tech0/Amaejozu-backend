"""UserInterest schemas"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .base import BaseSchema

if TYPE_CHECKING:
    from .category import CategoryResponse


class UserInterestBase(BaseSchema):
    """Base user interest schema"""
    user_id: str = Field(..., max_length=36)
    category_id: str = Field(..., max_length=36)


class UserInterestCreate(UserInterestBase):
    """Schema for creating a user interest"""
    id: str = Field(..., max_length=36)


class UserInterestResponse(UserInterestBase):
    """Schema for user interest response"""
    id: str
    created_at: datetime
    updated_at: datetime


class UserInterestWithCategory(UserInterestResponse):
    """Schema for user interest response with category details"""
    category: Optional[CategoryResponse] = None
