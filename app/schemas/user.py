"""User schemas"""
from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field

from .base import BaseSchema


class UserBase(BaseSchema):
    """Base user schema"""
    email: EmailStr
    nickname: str = Field(..., max_length=100)
    device_token: Optional[str] = Field(None, max_length=255)
    push_enabled: bool = False
    email_enabled: bool = True


class UserCreate(UserBase):
    """Schema for creating a user"""
    id: str = Field(..., max_length=36)


class UserUpdate(BaseSchema):
    """Schema for updating a user"""
    nickname: Optional[str] = Field(None, max_length=100)
    device_token: Optional[str] = Field(None, max_length=255)
    push_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: str
    created_at: datetime
    updated_at: datetime
