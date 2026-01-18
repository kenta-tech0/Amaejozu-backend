"""
通知関連のAPIエンドポイント
テストメール送信、通知履歴取得など
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.email_service import email_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ========== Schemas ==========

class TestEmailRequest(BaseModel):
    """テストメール送信リクエスト"""
    email: EmailStr


class TestEmailResponse(BaseModel):
    """テストメール送信レスポンス"""
    success: bool
    message: str
    email_id: Optional[str] = None
    error: Optional[str] = None


# ========== Endpoints ==========

@router.post("/test-email", response_model=TestEmailResponse)
def send_test_email(request: TestEmailRequest):
    """
    テストメールを送信
    メール通知機能の動作確認用
    """
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