"""
Watchlist API スキーマ定義
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================
# リクエストスキーマ
# ============================================
class WatchlistCreateRequest(BaseModel):
    """ウォッチリスト追加リクエスト（既存商品用）"""
    product_id: str = Field(..., description="商品ID")
    target_price: Optional[int] = Field(None, description="目標価格", ge=0)


class ProductData(BaseModel):
    """楽天API検索結果の商品データ"""
    rakuten_product_id: str = Field(..., description="楽天商品ID")
    name: str = Field(..., description="商品名")
    price: int = Field(..., description="価格", ge=0)
    shop_name: Optional[str] = Field(None, description="ショップ名")
    shop_code: Optional[str] = Field(None, description="ショップコード")
    image_url: Optional[str] = Field(None, description="商品画像URL")
    product_url: Optional[str] = Field(None, description="商品ページURL")
    affiliate_url: Optional[str] = Field(None, description="アフィリエイトURL")
    review_average: Optional[float] = Field(None, description="レビュー平均点")
    review_count: Optional[int] = Field(None, description="レビュー件数")


class WatchlistCreateWithProductRequest(BaseModel):
    """ウォッチリスト追加リクエスト（商品データ含む）"""
    product: ProductData = Field(..., description="商品データ")
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
    product_url: Optional[str] = None  # 追加
    model_config = ConfigDict(from_attributes=True)


class WatchlistItemResponse(BaseModel):
    """ウォッチリストアイテムレスポンス"""
    id: str
    product: ProductInWatchlist
    target_price: Optional[int] = None
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistResponse(BaseModel):
    """ウォッチリスト一覧レスポンス"""
    watchlist: List[WatchlistItemResponse]


class PriceHistoryItem(BaseModel):
    """価格履歴アイテム"""
    price: int
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceHistoryResponse(BaseModel):
    """価格履歴レスポンス"""
    price_history: List[PriceHistoryItem]


class MessageResponse(BaseModel):
    """メッセージレスポンス"""
    message: str
