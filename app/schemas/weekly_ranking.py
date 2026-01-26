"""
Weekly Ranking API スキーマ定義
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ProductInRanking(BaseModel):
    """ランキング内の商品情報"""

    id: str
    name: str
    current_price: int
    original_price: int
    discount_rate: float
    image_url: Optional[str] = None
    product_url: str
    brand_name: Optional[str] = None
    category_name: Optional[str] = None
    review_score: Optional[int] = None
    review_count: Optional[int] = None

    model_config = {"from_attributes": True}


class WeeklyRankingItem(BaseModel):
    """週間ランキングアイテム"""

    rank_position: int = Field(..., description="ランキング順位（1-10）")
    watchlist_count: int = Field(..., description="ウォッチリスト登録数")
    ai_recommendation: Optional[str] = Field(None, description="AI生成おすすめ文")
    previous_rank: Optional[int] = Field(None, description="前週順位（新規の場合はNULL）")
    rank_change: Optional[str] = Field(
        None, description="順位変動（UP/DOWN/NEW/STAY）"
    )
    product: ProductInRanking

    model_config = {"from_attributes": True}


class WeeklyRankingResponse(BaseModel):
    """週間TOP10ランキングレスポンス"""

    year: int = Field(..., description="年")
    week_number: int = Field(..., description="週番号")
    week_label: str = Field(..., description="週ラベル（例: 2026-W04）")
    generated_at: Optional[datetime] = Field(None, description="生成日時")
    rankings: List[WeeklyRankingItem] = Field(..., description="TOP10ランキング")

    model_config = {"from_attributes": True}


class WeeklyRankingListResponse(BaseModel):
    """週間ランキング一覧レスポンス（複数週取得用）"""

    total_weeks: int = Field(..., description="取得可能な週数")
    weeks: List[WeeklyRankingResponse] = Field(..., description="週ごとのランキング")
