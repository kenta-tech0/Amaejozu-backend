"""
通知サービス
価格下落検出時の通知処理、履歴記録、頻度制限を担当
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.watchlist import Watchlist
from app.models.product import Product
from app.models.user import User
from app.models.alert import Alert
from app.models.notification_history import Notification
from app.services.email_service import email_service
from app.services.openai_service import (
    _create_openai_client,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    validate_env_variables,
)
logger = logging.getLogger(__name__)

# 通知頻度制限（同じ商品への通知間隔）
NOTIFICATION_COOLDOWN_HOURS = 24


class NotificationService:
    """通知サービスクラス"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_and_send_price_drop_notifications(
        self,
        product_id: str,
        old_price: int,
        new_price: int
    ) -> List[Dict[str, Any]]:
        """
        価格下落時に対象ユーザーへ通知を送信
        
        Parameters:
            product_id: 商品ID
            old_price: 旧価格
            new_price: 新価格
        
        Returns:
            送信結果のリスト
        """
        # 値下げでない場合はスキップ
        if new_price >= old_price:
            logger.debug(f"値下げではないためスキップ: {old_price} → {new_price}")
            return []
        
        # 商品情報を取得
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            logger.warning(f"商品が見つかりません: {product_id}")
            return []
        
        # 下落率を計算
        drop_rate = ((old_price - new_price) / old_price) * 100
        
        # この商品をウォッチしているユーザーを取得
        watchlist_items = self.db.query(Watchlist).filter(
            Watchlist.product_id == product_id,
            Watchlist.notify_any_drop == True
        ).all()
        
        results = []
        
        for item in watchlist_items:
            # 目標価格が設定されている場合、それ以下かチェック
            if item.target_price and new_price > item.target_price:
                logger.debug(f"目標価格未達: {new_price} > {item.target_price}")
                continue
            
            # ユーザー情報を取得
            user = self.db.query(User).filter(User.id == item.user_id).first()
            if not user or not user.email:
                continue
            
            # 通知頻度制限をチェック
            if self._is_notification_cooldown(user.id, product_id):
                logger.info(f"通知クールダウン中: user={user.id}, product={product_id}")
                continue
            
            # メール通知を送信
            result = self._send_notification(
                user=user,
                product=product,
                watchlist_item=item,
                old_price=old_price,
                new_price=new_price,
                drop_rate=drop_rate
            )
            
            results.append(result)
        
        return results
    
    def _is_notification_cooldown(self, user_id: str, product_id: str) -> bool:
        """通知のクールダウン期間中かチェック"""
        cooldown_since = datetime.now() - timedelta(hours=NOTIFICATION_COOLDOWN_HOURS)
        
        # 最近の通知を確認（タイトルに商品IDが含まれるかで判定）
        recent_notification = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.sent_at >= cooldown_since,
            Notification.channel == "email"
        ).first()
        
        # 簡易的なクールダウンチェック（同じユーザーへの最近のメール通知）
        return recent_notification is not None
    
    def _send_notification(
        self,
        user: User,
        product: Product,
        watchlist_item: Watchlist,
        old_price: int,
        new_price: int,
        drop_rate: float
    ) -> Dict[str, Any]:
        """通知を送信し、履歴を記録"""
        
        # メール送信
        email_result = email_service.send_price_drop_notification(
            to=user.email,
            product_name=product.name,
            old_price=old_price,
            new_price=new_price,
            drop_rate=drop_rate,
            product_url=product.product_url,
            image_url=product.image_url
        )
        
        # アラートを作成
        alert = Alert(
            id=str(uuid.uuid4()),
            watch_item_id=watchlist_item.id,
            alert_type="price_drop",
            old_price=old_price,
            new_price=new_price,
            drop_rate=drop_rate,
            triggered_at=datetime.now()
        )
        self.db.add(alert)
        self.db.flush()  # alert.id を取得するため
        
        # 通知履歴を記録
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user.id,
            alert_id=alert.id,
            title=f"【値下げ】{product.name[:50]}",
            message=f"¥{old_price:,} → ¥{new_price:,}（{drop_rate:.1f}% OFF）",
            channel="email",
            is_read=False,
            sent_at=datetime.now()
        )
        
        self.db.add(notification)
        self.db.commit()
        
        logger.info(
            f"通知送信: user={user.email}, product={product.name[:30]}..., "
            f"success={email_result.get('success')}"
        )
        
        return {
            "user_id": user.id,
            "user_email": user.email,
            "product_id": product.id,
            "product_name": product.name,
            "old_price": old_price,
            "new_price": new_price,
            "drop_rate": drop_rate,
            "email_sent": email_result.get("success", False),
            "error": email_result.get("error")
        }
    
    def get_notification_history(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Notification]:
        """ユーザーの通知履歴を取得"""
        return self.db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(
            Notification.sent_at.desc()
        ).limit(limit).all()
    
    def generate_ai_recommendation_for_target_achieved(
        self,
        product: Product,
        registered_price: int,
        target_price: int,
        current_price: int
    ) -> Optional[str]:
        """目標価格達成時のAI推薦文を生成"""
        try:
            if not validate_env_variables():
                logger.warning("Azure OpenAI環境変数が未設定")
                return None

            savings = registered_price - current_price
            discount_rate = ((registered_price - current_price) / registered_price) * 100

            prompt = f"""あなたはメンズコスメの専門家です。ユーザーが設定した目標価格を達成した商品について、購入を後押しする推薦文を作成してください。

【商品情報】
商品名: {product.name}
登録時価格: ¥{registered_price:,}
目標価格: ¥{target_price:,}
現在価格: ¥{current_price:,}
お得額: ¥{savings:,}（{discount_rate:.1f}%OFF）

【条件】
- 100〜150文字程度で簡潔に
- 目標達成のお祝いと購入の後押しを含める
- 男性向けの親しみやすい表現
- 絵文字は使用しない
- 「今が買い時」というメッセージを含める

推薦文:"""

            client = _create_openai_client()
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは親切で専門的なメンズコスメアドバイザーです。",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"AI推薦文生成エラー: {str(e)}")
            return None

    def check_and_send_target_achieved_notifications(
        self,
        product_id: str,
        old_price: int,
        new_price: int
    ) -> List[Dict[str, Any]]:
        """目標価格達成時に通知を送信"""
        if new_price >= old_price:
            return []
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return []
        
        watchlist_items = self.db.query(Watchlist).filter(
            Watchlist.product_id == product_id,
            Watchlist.target_price.isnot(None)
        ).all()
        
        results = []
        
        for item in watchlist_items:
            if new_price > item.target_price:
                continue
            
            if old_price <= item.target_price:
                logger.debug(f"既に目標達成済み: product={product_id}")
                continue
            
            user = self.db.query(User).filter(User.id == item.user_id).first()
            if not user or not user.email:
                continue
            
            if self._is_notification_cooldown(user.id, product_id):
                logger.info(f"通知クールダウン中: user={user.id}, product={product_id}")
                continue
            
            registered_price = item.registered_price or old_price
            
            ai_recommendation = self.generate_ai_recommendation_for_target_achieved(
                product=product,
                registered_price=registered_price,
                target_price=item.target_price,
                current_price=new_price
            )
            
            email_result = email_service.send_target_price_achieved_notification(
                to=user.email,
                product_name=product.name,
                registered_price=registered_price,
                target_price=item.target_price,
                current_price=new_price,
                product_url=product.product_url,
                image_url=product.image_url,
                ai_recommendation=ai_recommendation
            )
            
            savings = registered_price - new_price
            alert = Alert(
                id=str(uuid.uuid4()),
                watch_item_id=item.id,
                alert_type="target_achieved",
                old_price=old_price,
                new_price=new_price,
                drop_rate=((registered_price - new_price) / registered_price) * 100,
                triggered_at=datetime.now()
            )
            self.db.add(alert)
            self.db.flush()
            
            notification = Notification(
                id=str(uuid.uuid4()),
                user_id=user.id,
                alert_id=alert.id,
                title=f"【目標達成】{product.name[:50]}",
                message=f"目標価格¥{item.target_price:,}を達成！現在¥{new_price:,}（{savings:,}円お得）",
                channel="email",
                is_read=False,
                sent_at=datetime.now()
            )
            self.db.add(notification)
            self.db.commit()
            
            logger.info(
                f"目標達成通知送信: user={user.email}, product={product.name[:30]}..."
            )
            
            results.append({
                "user_id": user.id,
                "user_email": user.email,
                "product_id": product.id,
                "registered_price": registered_price,
                "target_price": item.target_price,
                "current_price": new_price,
                "savings": savings,
                "email_sent": email_result.get("success", False),
            })
        
        return results

def send_price_drop_notifications(
    db: Session,
    product_id: str,
    old_price: int,
    new_price: int
) -> List[Dict[str, Any]]:
    """価格下落通知を送信するヘルパー関数"""
    service = NotificationService(db)
    return service.check_and_send_price_drop_notifications(
        product_id=product_id,
        old_price=old_price,
        new_price=new_price
    )

def send_target_achieved_notifications(
    db: Session,
    product_id: str,
    old_price: int,
    new_price: int
) -> List[Dict[str, Any]]:
    """目標価格達成通知を送信するヘルパー関数"""
    service = NotificationService(db)
    return service.check_and_send_target_achieved_notifications(
        product_id=product_id,
        old_price=old_price,
        new_price=new_price
    )