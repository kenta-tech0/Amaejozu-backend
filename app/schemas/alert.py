"""Alert schemas"""
from datetime import datetime

from pydantic import Field

from .base import BaseSchema


class AlertBase(BaseSchema):
    """Base alert schema"""
    watch_item_id: str = Field(..., max_length=36)
    alert_type: str = Field(..., max_length=50)
    old_price: int
    new_price: int
    drop_rate: float


class AlertCreate(AlertBase):
    """Schema for creating an alert"""
    id: str = Field(..., max_length=36)
    triggered_at: datetime


class AlertResponse(AlertBase):
    """Schema for alert response"""
    id: str
    triggered_at: datetime
    created_at: datetime
