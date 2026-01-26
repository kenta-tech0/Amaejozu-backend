"""
Web Push通知サービス
ブラウザプッシュ通知を送信する
"""
import os
import json
import logging
from typing import Optional
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS_EMAIL = os.getenv("VAPID_CLAIMS_EMAIL", "mailto:admin@example.com")


def send_push_notification(
    subscription_info: dict,
    title: str,
    body: str,
    url: Optional[str] = None,
    icon: Optional[str] = None,
) -> bool:
    """
    ブラウザプッシュ通知を送信
    
    Args:
        subscription_info: ブラウザから取得した購読情報（endpoint, keys）
        title: 通知タイトル
        body: 通知本文
        url: クリック時の遷移先URL
        icon: 通知アイコンURL
    
    Returns:
        成功時True、失敗時False
    """
    if not VAPID_PUBLIC_KEY or not VAPID_PRIVATE_KEY:
        logger.error("VAPID鍵が設定されていません")
        return False
    
    try:
        payload = {
            "title": title,
            "body": body,
            "icon": icon or "/icon-192x192.png",
            "badge": "/badge-72x72.png",
            "data": {
                "url": url or "/"
            }
        }
        
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_CLAIMS_EMAIL}
        )
        
        logger.info(f"プッシュ通知送信成功: {title}")
        return True
        
    except WebPushException as e:
        logger.error(f"プッシュ通知送信エラー: {str(e)}")
        # 購読が無効な場合（410 Gone）は購読を削除する必要がある
        if e.response and e.response.status_code == 410:
            logger.warning("購読が無効になっています（ブラウザで解除された可能性）")
        return False
    except Exception as e:
        logger.error(f"プッシュ通知エラー: {str(e)}")
        return False


def get_vapid_public_key() -> str:
    """フロントエンド用のVAPID公開鍵を取得"""
    return VAPID_PUBLIC_KEY
