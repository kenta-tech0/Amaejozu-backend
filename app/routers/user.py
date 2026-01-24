"""
User Settings API - ユーザー設定管理
Issue #9
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.auth import get_current_user, hash_password, verify_password


# ============================================
# Pydantic スキーマ
# ============================================

class ProfileResponse(BaseModel):
    """プロフィール取得レスポンス"""
    id: str
    email: str
    name: str
    created_at: str

    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):
    """プロフィール更新リクエスト"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class PasswordChangeRequest(BaseModel):
    """パスワード変更リクエスト"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


class NotificationSettingsResponse(BaseModel):
    """通知設定レスポンス"""
    email_notifications: bool
    notification_frequency: str  # instant, daily, weekly


class NotificationSettingsUpdateRequest(BaseModel):
    """通知設定更新リクエスト"""
    email_notifications: Optional[bool] = None
    notification_frequency: Optional[str] = Field(None, pattern="^(instant|daily|weekly)$")


class MessageResponse(BaseModel):
    """汎用メッセージレスポンス"""
    success: bool
    message: str


# ============================================
# ルーター設定
# ============================================

router = APIRouter(
    prefix="/api/user",
    tags=["user-settings"]
)


# ============================================
# エンドポイント
# ============================================

@router.get("/profile", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """
    プロフィール取得エンドポイント
    GET /api/user/profile
    """
    return ProfileResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.nickname,
        created_at=current_user.created_at.isoformat()
    )


@router.put("/profile", response_model=ProfileResponse)
def update_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    プロフィール更新エンドポイント
    PUT /api/user/profile
    """
    if request.name is not None:
        current_user.nickname = request.name
    
    db.commit()
    db.refresh(current_user)
    
    return ProfileResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.nickname,
        created_at=current_user.created_at.isoformat()
    )


@router.put("/password", response_model=MessageResponse)
def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    パスワード変更エンドポイント
    PUT /api/user/password
    """
    # 現在のパスワードを検証
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="現在のパスワードが正しくありません"
        )
    
    # 新しいパスワードをハッシュ化して保存
    current_user.password_hash = hash_password(request.new_password)
    db.commit()
    
    return MessageResponse(
        success=True,
        message="パスワードを変更しました"
    )


@router.get("/notification-settings", response_model=NotificationSettingsResponse)
def get_notification_settings(current_user: User = Depends(get_current_user)):
    """
    通知設定取得エンドポイント
    GET /api/user/notification-settings
    """
    # email_enabled から notification_frequency を推定
    # 現状のモデルには frequency がないので、email_enabled を基に返す
    frequency = "daily" if current_user.email_enabled else "instant"
    
    return NotificationSettingsResponse(
        email_notifications=current_user.email_enabled,
        notification_frequency=frequency
    )


@router.put("/notification-settings", response_model=NotificationSettingsResponse)
def update_notification_settings(
    request: NotificationSettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    通知設定更新エンドポイント
    PUT /api/user/notification-settings
    """
    if request.email_notifications is not None:
        current_user.email_enabled = request.email_notifications
    
    db.commit()
    db.refresh(current_user)
    
    frequency = "daily" if current_user.email_enabled else "instant"
    
    return NotificationSettingsResponse(
        email_notifications=current_user.email_enabled,
        notification_frequency=frequency
    )


@router.delete("/account", response_model=MessageResponse)
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    アカウント削除エンドポイント
    DELETE /api/user/account
    """
    db.delete(current_user)
    db.commit()
    
    return MessageResponse(
        success=True,
        message="アカウントを削除しました"
    )