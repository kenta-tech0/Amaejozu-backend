"""
User Settings API - ユーザー設定管理
プロフィール・パスワード・通知設定の管理
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.auth import get_current_user, hash_password, verify_password


# ============================================
# Pydantic スキーマ
# ============================================

class ProfileResponse(BaseModel):
    """プロフィール取得レスポンス"""
    id: str = Field(..., description="ユーザーID")
    email: str = Field(..., description="メールアドレス")
    name: str = Field(..., description="ニックネーム")
    created_at: str = Field(..., description="登録日時")

    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):
    """プロフィール更新リクエスト"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="ニックネーム")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "新しいニックネーム"
            }
        }


class PasswordChangeRequest(BaseModel):
    """パスワード変更リクエスト"""
    current_password: str = Field(..., min_length=1, description="現在のパスワード")
    new_password: str = Field(..., min_length=8, max_length=100, description="新しいパスワード（8文字以上）")

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "currentpass123",
                "new_password": "newsecurepass456"
            }
        }


class NotificationSettingsResponse(BaseModel):
    """通知設定レスポンス"""
    email_notifications: bool = Field(..., description="メール通知の有効/無効")
    notification_frequency: str = Field(..., description="通知頻度（instant/daily/weekly）")


class NotificationSettingsUpdateRequest(BaseModel):
    """通知設定更新リクエスト"""
    email_notifications: Optional[bool] = Field(None, description="メール通知の有効/無効")
    notification_frequency: Optional[str] = Field(
        None, 
        pattern="^(instant|daily|weekly)$",
        description="通知頻度（instant/daily/weekly）"
    )

  class Config:
        json_schema_extra = {
            "example": {
                "email_notifications": True,
                "notification_frequency": "daily"
            }
        }

class MessageResponse(BaseModel):
    """汎用メッセージレスポンス"""
    success: bool = Field(..., description="処理成功フラグ")
    message: str = Field(..., description="メッセージ")

# ============================================
# ルーター設定
# ============================================

@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="プロフィール取得",
    description="""
ログインユーザーのプロフィール情報を取得します。

## 認証
`Authorization: Bearer {token}` ヘッダーが必要です。
""",
    responses={
        200: {
            "description": "取得成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "user@example.com",
                        "name": "ユーザー名",
                        "created_at": "2026-01-01T00:00:00"
                    }
                }
            }
        },
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "認証トークンが必要です"}
                }
            }
        }
    }
)
def get_profile(current_user: User = Depends(get_current_user)):
    """プロフィール取得エンドポイント"""
    return ProfileResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.nickname,
        created_at=current_user.created_at.isoformat()
    )


@router.put(
    "/profile",
    response_model=ProfileResponse,
    summary="プロフィール更新",
    description="""
ログインユーザーのプロフィール情報を更新します。

## 認証
`Authorization: Bearer {token}` ヘッダーが必要です。

## パスワード要件
- 新しいパスワードは8文字以上
- 現在のパスワードの検証が必要
""",
    responses={
        200: {
            "description": "変更成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "パスワードを変更しました"
                    }
                }
            }
        },
        400: {
            "description": "現在のパスワードが不正",
            "content": {
                "application/json": {
                    "example": {"detail": "現在のパスワードが正しくありません"}
                }
            }
        },
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "認証トークンが必要です"}
                }
            }
        }
    }
)
def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """パスワード変更エンドポイント"""
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="現在のパスワードが正しくありません"
        )
    
    current_user.password_hash = hash_password(request.new_password)
    db.commit()
    
    return MessageResponse(
        success=True,
        message="パスワードを変更しました"
    )


@router.get(
    "/notification-settings",
    response_model=NotificationSettingsResponse,
    summary="通知設定取得",
    description="""
ログインユーザーの通知設定を取得します。

## 認証
`Authorization: Bearer {token}` ヘッダーが必要です。

## 設定項目
- **email_notifications**: メール通知の有効/無効
- **notification_frequency**: 通知頻度（instant/daily/weekly）
""",
    responses={
        200: {
            "description": "取得成功",
            "content": {
                "application/json": {
                    "example": {
                        "email_notifications": True,
                        "notification_frequency": "daily"
                    }
                }
            }
        },
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "認証トークンが必要です"}
                }
            }
        }
    }
)
def get_notification_settings(current_user: User = Depends(get_current_user)):
    """通知設定取得エンドポイント"""
    frequency = "daily" if current_user.email_enabled else "instant"
    
    return NotificationSettingsResponse(
        email_notifications=current_user.email_enabled,
        notification_frequency=frequency
    )


@router.put(
    "/notification-settings",
    response_model=NotificationSettingsResponse,
    summary="通知設定更新",
    description="""
ログインユーザーの通知設定を更新します。

## 認証
`Authorization: Bearer {token}` ヘッダーが必要です。

## 更新可能な項目
- **email_notifications**: メール通知の有効/無効
- **notification_frequency**: 通知頻度（instant/daily/weekly）
""",
    responses={
        200: {
            "description": "更新成功",
            "content": {
                "application/json": {
                    "example": {
                        "email_notifications": False,
                        "notification_frequency": "weekly"
                    }
                }
            }
        },
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "認証トークンが必要です"}
                }
            }
        }
    }
)
def update_notification_settings(
    request: NotificationSettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """通知設定更新エンドポイント"""
    if request.email_notifications is not None:
        current_user.email_enabled = request.email_notifications
    
    db.commit()
    db.refresh(current_user)
    
    frequency = "daily" if current_user.email_enabled else "instant"
    
    return NotificationSettingsResponse(
        email_notifications=current_user.email_enabled,
        notification_frequency=frequency
    )


@router.delete(
    "/account",
    response_model=MessageResponse,
    summary="アカウント削除",
    description="""
ログインユーザーのアカウントを削除します。

## 認証
`Authorization: Bearer {token}` ヘッダーが必要です。

## 注意
- この操作は取り消せません
- 関連するウォッチリストなどのデータも削除されます
""",
    responses={
        200: {
            "description": "削除成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "アカウントを削除しました"
                    }
                }
            }
        },
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "認証トークンが必要です"}
                }
            }
        }
    }
)
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """アカウント削除エンドポイント"""
    db.delete(current_user)
    db.commit()
    
    return MessageResponse(
        success=True,
        message="アカウントを削除しました"
    )