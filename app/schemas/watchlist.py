"""
Watchlist API スキーマ定義
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================
# リクエストスキーマ
# ============================================
class WatchlistCreateRequest(BaseModel):
    """ウォッチリスト追加リクエスト"""
    product_id: str = Field(..., description="商品ID")
    target_price: Optional[int] = Field(None, description="目標価格", ge=0)


# ============================================
# レスポンススキーマ
# ============================================
class ProductInWatchlist(BaseModel):
    """ウォッチリスト内の商品情報"""
    id: str
    name: str
    current_price: int
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class WatchlistItemResponse(BaseModel):
    """ウォッチリストアイテムレスポンス"""
    id: str
    product: ProductInWatchlist
    target_price: Optional[int] = None
    added_at: datetime

    class Config:
        from_attributes = True


class WatchlistResponse(BaseModel):
    """ウォッチリスト一覧レスポンス"""
    watchlist: List[WatchlistItemResponse]


class PriceHistoryItem(BaseModel):
    """価格履歴アイテム"""
    price: int
    recorded_at: datetime

    class Config:
        from_attributes = True


class PriceHistoryResponse(BaseModel):
    """価格履歴レスポンス"""
    price_history: List[PriceHistoryItem]


class MessageResponse(BaseModel):
    """メッセージレスポンス"""
    message: str
