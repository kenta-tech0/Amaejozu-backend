"""Watchlist schemas"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .base import BaseSchema

if TYPE_CHECKING:
    from .product import ProductResponse


class WatchlistBase(BaseSchema):
    """Base watchlist schema"""
    user_id: str = Field(..., max_length=36)
    product_id: str = Field(..., max_length=36)
    target_price: Optional[int] = None
    notify_any_drop: bool = True


class WatchlistCreate(WatchlistBase):
    """Schema for creating a watchlist item"""
    id: str = Field(..., max_length=36)


class WatchlistUpdate(BaseSchema):
    """Schema for updating a watchlist item"""
    target_price: Optional[int] = None
    notify_any_drop: Optional[bool] = None


class WatchlistResponse(WatchlistBase):
    """Schema for watchlist response"""
    id: str
    created_at: datetime
    updated_at: datetime


class WatchlistWithProduct(WatchlistResponse):
    """Schema for watchlist response with product details"""
    product: Optional[ProductResponse] = None
