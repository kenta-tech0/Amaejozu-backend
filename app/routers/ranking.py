"""
Weekly Ranking API - 週間TOP10ランキング
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.database import get_db
from app.models.weekly_ranking import WeeklyRanking
from app.models.product import Product
from app.schemas.weekly_ranking import (
    WeeklyRankingResponse,
    WeeklyRankingItem,
    WeeklyRankingListResponse,
    ProductInRanking,
)
from app.services.weekly_ranking_service import WeeklyRankingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rankings", tags=["rankings"])


@router.get(
    "/weekly",
    response_model=WeeklyRankingResponse,
    summary="今週のTOP10ランキング取得",
    description="""
今週の週間TOP10商品ランキングを取得します。

## 機能
- ウォッチリスト登録数に基づくTOP10
- AI生成の推薦文付き
- 前週との順位変動表示

## パラメータ
- `year`: 年（省略時は今週）
- `week`: 週番号（省略時は今週）
""",
    responses={
        200: {
            "description": "取得成功",
            "content": {
                "application/json": {
                    "example": {
                        "year": 2026,
                        "week_number": 4,
                        "week_label": "2026-W04",
                        "generated_at": "2026-01-25T00:00:00",
                        "rankings": [
                            {
                                "rank_position": 1,
                                "watchlist_count": 150,
                                "ai_recommendation": "週間ランキング1位の超人気商品...",
                                "previous_rank": 2,
                                "rank_change": "UP",
                                "product": {
                                    "id": "prod-001",
                                    "name": "メンズ化粧水",
                                    "current_price": 1980,
                                    "original_price": 2980,
                                    "discount_rate": 33.5,
                                    "image_url": "https://example.com/image.jpg",
                                    "product_url": "https://example.com/product",
                                    "brand_name": "ブランド名",
                                    "category_name": "化粧水",
                                    "review_score": 45,
                                    "review_count": 120,
                                },
                            }
                        ],
                    }
                }
            },
        },
        404: {
            "description": "ランキングが見つからない",
            "content": {
                "application/json": {
                    "example": {"detail": "指定された週のランキングが見つかりません"}
                }
            },
        },
    },
)
def get_weekly_ranking(
    year: Optional[int] = Query(None, description="年（省略時は今週）"),
    week: Optional[int] = Query(
        None, ge=1, le=53, description="週番号（省略時は今週）"
    ),
    db: Session = Depends(get_db),
):
    """週間TOP10ランキングを取得"""
    try:
        # 年・週が指定されていない場合は今週
        if year is None or week is None:
            current_year, current_week = WeeklyRankingService.get_current_week()
            year = year or current_year
            week = week or current_week

        # ランキングデータを取得（リレーション含む）
        rankings = (
            db.query(WeeklyRanking)
            .options(
                joinedload(WeeklyRanking.product).joinedload(Product.brand),
                joinedload(WeeklyRanking.product).joinedload(Product.category),
            )
            .filter(
                WeeklyRanking.year == year,
                WeeklyRanking.week_number == week,
            )
            .order_by(WeeklyRanking.rank_position.asc())
            .all()
        )

        if not rankings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"指定された週のランキングが見つかりません: {year}-W{week:02d}",
            )

        # レスポンス構築
        ranking_items = []
        for ranking in rankings:
            product = ranking.product

            # 順位変動を計算
            rank_change = "STAY"
            if ranking.previous_rank is None:
                rank_change = "NEW"
            elif ranking.previous_rank > ranking.rank_position:
                rank_change = "UP"
            elif ranking.previous_rank < ranking.rank_position:
                rank_change = "DOWN"

            ranking_items.append(
                WeeklyRankingItem(
                    rank_position=ranking.rank_position,
                    watchlist_count=ranking.watchlist_count,
                    ai_recommendation=ranking.ai_recommendation,
                    previous_rank=ranking.previous_rank,
                    rank_change=rank_change,
                    product=ProductInRanking(
                        id=product.id,
                        name=product.name,
                        current_price=product.current_price,
                        original_price=product.original_price,
                        discount_rate=product.discount_rate,
                        image_url=product.image_url,
                        product_url=product.product_url,
                        brand_name=product.brand.name if product.brand else None,
                        category_name=product.category.name if product.category else None,
                        review_score=product.review_score,
                        review_count=product.review_count,
                    ),
                )
            )

        # 生成日時（最初のランキングの作成日時）
        generated_at = rankings[0].created_at if rankings else None

        return WeeklyRankingResponse(
            year=year,
            week_number=week,
            week_label=f"{year}-W{week:02d}",
            generated_at=generated_at,
            rankings=ranking_items,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"週間ランキング取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"サーバーエラー: {str(e)}",
        )


@router.get(
    "/weekly/history",
    response_model=WeeklyRankingListResponse,
    summary="週間ランキング履歴取得",
    description="""
過去の週間ランキング履歴を取得します。

## パラメータ
- `weeks`: 取得する週数（デフォルト: 4週）
""",
    responses={200: {"description": "取得成功"}},
)
def get_ranking_history(
    weeks: int = Query(4, ge=1, le=52, description="取得する週数"),
    db: Session = Depends(get_db),
):
    """週間ランキング履歴を取得"""
    try:
        # 利用可能な週を取得（最新からN週分）
        available_weeks = (
            db.query(WeeklyRanking.year, WeeklyRanking.week_number)
            .distinct()
            .order_by(
                desc(WeeklyRanking.year),
                desc(WeeklyRanking.week_number),
            )
            .limit(weeks)
            .all()
        )

        if not available_weeks:
            return WeeklyRankingListResponse(total_weeks=0, weeks=[])

        # 各週のランキングを取得
        weekly_rankings = []
        for year, week_number in available_weeks:
            # 各週のランキングを取得（再利用）
            ranking_response = get_weekly_ranking(year=year, week=week_number, db=db)
            weekly_rankings.append(ranking_response)

        return WeeklyRankingListResponse(
            total_weeks=len(weekly_rankings),
            weeks=weekly_rankings,
        )

    except Exception as e:
        logger.error(f"ランキング履歴取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"サーバーエラー: {str(e)}",
        )
