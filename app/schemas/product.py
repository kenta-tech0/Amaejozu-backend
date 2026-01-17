"""Product schemas"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .base import BaseSchema

if TYPE_CHECKING:
    from .brand import BrandResponse
    from .category import CategoryResponse


class ProductBase(BaseSchema):
    """Base product schema"""
    brand_id: str = Field(..., max_length=36)
    category_id: str = Field(..., max_length=36)
    rakuten_item_code: str = Field(..., max_length=100)
    name: str = Field(..., max_length=500)
    image_url: Optional[str] = Field(None, max_length=1000)
    product_url: str = Field(..., max_length=1000)
    affiliate_url: Optional[str] = Field(None, max_length=1000)
    current_price: int
    original_price: int
    lowest_price: Optional[int] = None
    discount_rate: float = 0.0
    is_on_sale: bool = False
    checked_at: datetime
    review_score: Optional[int] = None
    review_count: Optional[int] = None
    ranking: Optional[int] = None
    ranking_prev: Optional[int] = None


class ProductCreate(ProductBase):
    """Schema for creating a product"""
    id: str = Field(..., max_length=36)


class ProductUpdate(BaseSchema):
    """Schema for updating a product"""
    name: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = Field(None, max_length=1000)
    product_url: Optional[str] = Field(None, max_length=1000)
    affiliate_url: Optional[str] = Field(None, max_length=1000)
    current_price: Optional[int] = None
    original_price: Optional[int] = None
    lowest_price: Optional[int] = None
    discount_rate: Optional[float] = None
    is_on_sale: Optional[bool] = None
    checked_at: Optional[datetime] = None
    review_score: Optional[int] = None
    review_count: Optional[int] = None
    ranking: Optional[int] = None
    ranking_prev: Optional[int] = None


class ProductResponse(ProductBase):
    """Schema for product response"""
    id: str
    created_at: datetime
    updated_at: datetime


class ProductWithBrandCategory(ProductResponse):
    """Schema for product response with brand and category details"""
    brand: Optional[BrandResponse] = None
    category: Optional[CategoryResponse] = None
