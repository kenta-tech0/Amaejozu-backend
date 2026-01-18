"""PriceHistory schemas"""
from datetime import datetime

from pydantic import Field

from .base import BaseSchema


class PriceHistoryBase(BaseSchema):
    """Base price history schema"""
    product_id: str = Field(..., max_length=36)
    price: int
    discount_rate: float = 0.0
    observed_at: datetime


class PriceHistoryCreate(PriceHistoryBase):
    """Schema for creating a price history"""
    id: str = Field(..., max_length=36)


class PriceHistoryResponse(PriceHistoryBase):
    """Schema for price history response"""
    id: str
    created_at: datetime
