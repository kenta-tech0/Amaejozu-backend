"""Brand schemas"""
from datetime import datetime
from typing import Optional, List

from pydantic import Field

from .base import BaseSchema


class BrandBase(BaseSchema):
    """Base brand schema"""
    name: str = Field(..., max_length=255)
    shop_code: str = Field(..., max_length=100)
    logo_url: Optional[str] = Field(None, max_length=500)


class BrandCreate(BrandBase):
    """Schema for creating a brand"""
    id: str = Field(..., max_length=36)


class BrandUpdate(BaseSchema):
    """Schema for updating a brand"""
    name: Optional[str] = Field(None, max_length=255)
    shop_code: Optional[str] = Field(None, max_length=100)
    logo_url: Optional[str] = Field(None, max_length=500)


class BrandResponse(BrandBase):
    """Schema for brand response"""
    id: str
    created_at: datetime
    updated_at: datetime


class BrandSummary(BaseSchema):
    """ブランドサマリー（一覧用の軽量版）"""
    id: str
    name: str
    shop_code: str


class BrandListResponse(BaseSchema):
    """ブランド一覧レスポンス"""
    status: str = "ok"
    brands: List[BrandSummary]
    count: int
