"""Category schemas"""
from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import BaseSchema


class CategoryBase(BaseSchema):
    """Base category schema"""
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=100)
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    """Schema for creating a category"""
    id: str = Field(..., max_length=36)


class CategoryUpdate(BaseSchema):
    """Schema for updating a category"""
    name: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=100)
    sort_order: Optional[int] = None


class CategoryResponse(CategoryBase):
    """Schema for category response"""
    id: str
    created_at: datetime
    updated_at: datetime
