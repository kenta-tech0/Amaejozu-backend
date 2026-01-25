"""
通知関連のAPIエンドポイント
テストメール送信、通知履歴取得など
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.email_service import email_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ============================================
# Pydantic スキーマ
# ============================================

class TestEmailRequest(BaseModel):
    """テストメール送信リクエスト"""
    email: EmailStr = Field(..., description="送信先メールアドレス")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "test@example.com"
            }
        }
    )


class TestEmailResponse(BaseModel):
    """テストメール送信レスポンス"""
    success: bool = Field(..., description="送信成功フラグ")
    message: str = Field(..., description="結果メッセージ")
    email_id: Optional[str] = Field(None, description="送信されたメールのID")
    error: Optional[str] = Field(None, description="エラーメッセージ（失敗時）")


# ============================================
# エンドポイント
# ============================================

@router.post(
    "/test-email",
    response_model=TestEmailResponse,
    summary="テストメール送信",
    description="""
テストメールを送信して、メール通知機能の動作確認を行います。

## 用途
- メール通知機能の動作確認
- Resend APIとの接続テスト

## 注意
- 実際にメールが送信されます
- 送信先メールアドレスは有効なものを指定してください
""",
    responses={
        200: {
            "description": "送信成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "テストメールを test@example.com に送信しました",
                        "email_id": "abc123-def456",
                        "error": None
                    }
                }
            }
        },
        200: {
            "description": "送信失敗",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "テストメールの送信に失敗しました",
                        "email_id": None,
                        "error": "Invalid API key"
                    }
                }
            }
        }
    }
)
def send_test_email(request: TestEmailRequest):
    """テストメールを送信"""
    result = email_service.send_test_email(to=request.email)
    
    if result.get("success"):
        return TestEmailResponse(
            success=True,
            message=f"テストメールを {request.email} に送信しました",
            email_id=result.get("id")
        )
    else:
        return TestEmailResponse(
            success=False,
            message="テストメールの送信に失敗しました",
            error=result.get("error")
        )