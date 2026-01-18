"""Notification schemas"""
from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import BaseSchema


class NotificationBase(BaseSchema):
    """Base notification schema"""
    user_id: str = Field(..., max_length=36)
    alert_id: str = Field(..., max_length=36)
    title: str = Field(..., max_length=255)
    message: str
    channel: str = Field(..., max_length=50)
    is_read: bool = False
    sent_at: datetime


class NotificationCreate(NotificationBase):
    """Schema for creating a notification"""
    id: str = Field(..., max_length=36)


class NotificationUpdate(BaseSchema):
    """Schema for updating a notification"""
    is_read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    """Schema for notification response"""
    id: str
    created_at: datetime
