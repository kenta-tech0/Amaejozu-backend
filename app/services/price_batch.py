"""
価格更新バッチ処理
ウォッチリスト商品の価格を定期的にチェックし、履歴を記録する
"""
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.product import Product
from app.models.watchlist import Watchlist
from app.models.price_history import PriceHistory
from app.services.rakuten_api import search_products, APIError
from app.services.notification_service import send_price_drop_notifications

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PriceBatchProcessor:
    """価格更新バッチ処理クラス"""
    
    def __init__(self, db: Session):
        self.db = db
        self.updated_count = 0
        self.error_count = 0
        self.price_changes: List[Dict[str, Any]] = []
    
    def get_watchlist_products(self) -> List[Product]:
        """ウォッチリストに登録されている商品を取得"""
        # ウォッチリストに登録されている商品IDを取得
        watchlist_items = self.db.query(Watchlist.product_id).distinct().all()
        product_ids = [item.product_id for item in watchlist_items]
        
        if not product_ids:
            logger.info("ウォッチリストに商品がありません")
            return []
        
        # 商品情報を取得
        products = self.db.query(Product).filter(
            Product.id.in_(product_ids)
        ).all()
        
        logger.info(f"ウォッチリスト商品数: {len(products)}")
        return products
    
    def fetch_latest_price(self, product: Product, max_retries: int = 3) -> Optional[int]:
        """楽天APIから最新価格を取得（リトライ付き）"""
        import time
        
        for attempt in range(max_retries):
            try:
                # 商品名で検索
                result = search_products(product.name[:50], hits=1)
                
                if result and "Items" in result and len(result["Items"]) > 0:
                    item = result["Items"][0]
                    return item.get("itemPrice")
                
                logger.warning(f"商品が見つかりません: {product.name[:30]}...")
                return None
                
            except APIError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1秒, 2秒, 4秒...
                    logger.warning(
                        f"APIエラー、リトライします ({attempt + 1}/{max_retries}): "
                        f"{wait_time}秒待機 - {str(e)}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"最大リトライ回数に到達: {product.name[:30]}... - {str(e)}"
                    )
                    self.error_count += 1
                    return None
            except Exception as e:
                logger.error(f"予期しないエラー: {product.name[:30]}... - {str(e)}")
                self.error_count += 1
                return None
        
        return None
    
    def detect_price_change(self, product: Product, new_price: int) -> Dict[str, Any]:
        """価格変動を検出"""
        old_price = product.current_price
        price_diff = new_price - old_price
        
        change_info = {
            "product_id": product.id,
            "product_name": product.name,
            "old_price": old_price,
            "new_price": new_price,
            "price_diff": price_diff,
            "is_price_drop": price_diff < 0,
            "change_percent": round((price_diff / old_price) * 100, 2) if old_price > 0 else 0
        }
        
        if price_diff != 0:
            logger.info(
                f"価格変動検出: {product.name[:30]}... "
                f"¥{old_price:,} → ¥{new_price:,} ({change_info['change_percent']:+.1f}%)"
            )
        
        return change_info
    
    def record_price_history(self, product: Product, new_price: int) -> None:
        """価格履歴をDBに記録"""
        price_history = PriceHistory(
            id=str(uuid.uuid4()),
            product_id=product.id,
            price=new_price,
            discount_rate=0.0,  # 必要に応じて計算
            observed_at=datetime.now()
        )
        
        self.db.add(price_history)
        logger.debug(f"価格履歴を記録: {product.id} - ¥{new_price:,}")
    
    def update_product_price(self, product: Product, new_price: int) -> None:
        """商品の現在価格を更新"""
        product.current_price = new_price
        product.checked_at = datetime.now()
        
        # 最安値を更新
        if product.lowest_price is None or new_price < product.lowest_price:
            product.lowest_price = new_price
            logger.info(f"最安値更新: {product.name[:30]}... - ¥{new_price:,}")
    
    def process_product(self, product: Product) -> bool:
        """1商品の価格更新処理"""
        try:
            # 最新価格を取得
            new_price = self.fetch_latest_price(product)
            
            if new_price is None:
                return False
            
            # 価格変動を検出
            change_info = self.detect_price_change(product, new_price)
            
            # 価格が変わっていなくても履歴は記録
            self.record_price_history(product, new_price)
            
            # 価格変動があった場合のみ商品を更新
            if change_info["price_diff"] != 0:
                self.update_product_price(product, new_price)
                self.price_changes.append(change_info)
                
                # 値下げの場合は通知を送信
                if change_info["is_price_drop"]:
                    try:
                        send_price_drop_notifications(
                            db=self.db,
                            product_id=product.id,
                            old_price=change_info["old_price"],
                            new_price=change_info["new_price"]
                        )
                        logger.info(f"価格下落通知を送信: {product.name[:30]}...")
                    except Exception as e:
                        logger.error(f"通知送信エラー: {str(e)}")
            
            self.updated_count += 1
            return True
            
        except Exception as e:
            logger.error(f"処理エラー: {product.name[:30]}... - {str(e)}")
            self.error_count += 1
            return False
    
    def run(self) -> Dict[str, Any]:
        """バッチ処理を実行"""
        logger.info("=" * 50)
        logger.info("価格更新バッチ処理を開始")
        logger.info("=" * 50)
        
        start_time = datetime.now()
        
        # ウォッチリスト商品を取得
        products = self.get_watchlist_products()
        
        if not products:
            return {
                "status": "completed",
                "message": "処理対象の商品がありません",
                "total": 0,
                "updated": 0,
                "errors": 0
            }
        
        # 各商品を処理
        for i, product in enumerate(products, 1):
            logger.info(f"[{i}/{len(products)}] {product.name[:40]}...")
            self.process_product(product)
        
        # 変更をコミット
        try:
            self.db.commit()
            logger.info("データベースにコミットしました")
        except Exception as e:
            logger.error(f"コミットエラー: {str(e)}")
            self.db.rollback()
            raise
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 結果サマリー
        result = {
            "status": "completed",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "total": len(products),
            "updated": self.updated_count,
            "errors": self.error_count,
            "price_drops": len([c for c in self.price_changes if c["is_price_drop"]]),
            "price_increases": len([c for c in self.price_changes if not c["is_price_drop"] and c["price_diff"] != 0]),
            "price_changes": self.price_changes
        }
        
        logger.info("=" * 50)
        logger.info(f"バッチ処理完了")
        logger.info(f"  処理件数: {result['total']}")
        logger.info(f"  更新成功: {result['updated']}")
        logger.info(f"  エラー: {result['errors']}")
        logger.info(f"  値下げ: {result['price_drops']}件")
        logger.info(f"  値上げ: {result['price_increases']}件")
        logger.info(f"  処理時間: {duration:.2f}秒")
        logger.info("=" * 50)
        
        return result


def run_price_update_batch() -> Dict[str, Any]:
    """バッチ処理を実行するエントリーポイント"""
    db = SessionLocal()
    try:
        processor = PriceBatchProcessor(db)
        return processor.run()
    finally:
        db.close()