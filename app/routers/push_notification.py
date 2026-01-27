"""
プッシュ通知API
ブラウザプッシュ通知の購読管理
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
import logging

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.webpush_service import get_vapid_public_key, send_push_notification, PushResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/push", tags=["push-notifications"])


class PushSubscription(BaseModel):
    """プッシュ通知購読情報"""
    endpoint: str
    keys: dict  # {"p256dh": "...", "auth": "..."}


class TestPushRequest(BaseModel):
    """テストプッシュ通知リクエスト"""
    title: Optional[str] = "テスト通知"
    body: Optional[str] = "これはテスト通知です"


@router.get("/vapid-public-key")
def get_public_key():
    """
    VAPID公開鍵を取得
    フロントエンドでプッシュ通知を購読する際に必要
    """
    public_key = get_vapid_public_key()
    if not public_key:
        raise HTTPException(status_code=500, detail="VAPID公開鍵が設定されていません")
    return {"public_key": public_key}


@router.post("/subscribe")
def subscribe_push(
    subscription: PushSubscription,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    プッシュ通知を購読
    ブラウザから取得した購読情報をユーザーに紐付けて保存
    """
    try:
        # 購読情報をJSON文字列として保存
        subscription_json = json.dumps({
            "endpoint": subscription.endpoint,
            "keys": subscription.keys
        })
        
        current_user.device_token = subscription_json
        current_user.push_enabled = True
        db.commit()
        
        logger.info(f"プッシュ通知購読登録: user_id={current_user.id}")
        return {"success": True, "message": "プッシュ通知を有効にしました"}
        
    except Exception as e:
        logger.error(f"購読登録エラー: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="購読登録に失敗しました")


@router.post("/unsubscribe")
def unsubscribe_push(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """プッシュ通知を解除"""
    try:
        current_user.device_token = None
        current_user.push_enabled = False
        db.commit()
        
        logger.info(f"プッシュ通知購読解除: user_id={current_user.id}")
        return {"success": True, "message": "プッシュ通知を無効にしました"}
        
    except Exception as e:
        logger.error(f"購読解除エラー: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="購読解除に失敗しました")


@router.post("/test")
def send_test_push(
    request: TestPushRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """テストプッシュ通知を送信"""
    if not current_user.push_enabled or not current_user.device_token:
        raise HTTPException(status_code=400, detail="プッシュ通知が有効になっていません")

    try:
        subscription_info = json.loads(current_user.device_token)

        result = send_push_notification(
            subscription_info=subscription_info,
            title=request.title,
            body=request.body,
            url="/watchlist"
        )

        if result == PushResult.SUCCESS:
            return {"success": True, "message": "テスト通知を送信しました"}
        elif result == PushResult.SUBSCRIPTION_EXPIRED:
            # 購読が無効になっているため、DBから削除
            current_user.device_token = None
            current_user.push_enabled = False
            db.commit()
            logger.warning(f"購読期限切れのため削除: user_id={current_user.id}")
            raise HTTPException(
                status_code=410,
                detail="購読が無効になっています。再度プッシュ通知を有効にしてください"
            )
        else:
            raise HTTPException(status_code=500, detail="通知送信に失敗しました")

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="購読情報が無効です")
