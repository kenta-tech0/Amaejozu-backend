"""
Watchlist API エンドポイント
"""

import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.watchlist import Watchlist
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.schemas.watchlist import (
    WatchlistCreateRequest,
    WatchlistResponse,
    WatchlistItemResponse,
    ProductInWatchlist,
    PriceHistoryResponse,
    PriceHistoryItem,
    MessageResponse,
)

router = APIRouter(prefix="/api/watchlist", tags=["Watchlist"])

# 仮のユーザーID（認証実装後に置き換え）
TEMP_USER_ID = "test-user-001"


@router.post(
    "", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED
)
def add_to_watchlist(request: WatchlistCreateRequest, db: Session = Depends(get_db)):
    """
    ウォッチリストに商品を追加
    """
    # 商品の存在確認
    product = db.query(Product).filter(Product.id == request.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="商品が見つかりません"
        )

    # 重複チェック
    existing = (
        db.query(Watchlist)
        .filter(
            Watchlist.user_id == TEMP_USER_ID,
            Watchlist.product_id == request.product_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="この商品は既にウォッチリストに追加されています",
        )

    # ウォッチリストに追加
    watchlist_item = Watchlist(
        id=str(uuid.uuid4()),
        user_id=TEMP_USER_ID,
        product_id=request.product_id,
        target_price=request.target_price,
        notify_any_drop=True,
    )

    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)

    return WatchlistItemResponse(
        id=watchlist_item.id,
        product=ProductInWatchlist(
            id=product.id,
            name=product.name,
            current_price=product.current_price,
            image_url=product.image_url,
        ),
        target_price=watchlist_item.target_price,
        added_at=watchlist_item.created_at,
    )


@router.get("", response_model=WatchlistResponse)
def get_watchlist(db: Session = Depends(get_db)):
    """
    ウォッチリスト一覧を取得
    """
    watchlist_items = (
        db.query(Watchlist).filter(Watchlist.user_id == TEMP_USER_ID).all()
    )

    result = []
    for item in watchlist_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            result.append(
                WatchlistItemResponse(
                    id=item.id,
                    product=ProductInWatchlist(
                        id=product.id,
                        name=product.name,
                        current_price=product.current_price,
                        image_url=product.image_url,
                    ),
                    target_price=item.target_price,
                    added_at=item.created_at,
                )
            )

    return WatchlistResponse(watchlist=result)


@router.delete("/{watchlist_id}", response_model=MessageResponse)
def remove_from_watchlist(watchlist_id: str, db: Session = Depends(get_db)):
    """ウォッチリストアイテムの価格履歴を取得"""
    watchlist_item = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == TEMP_USER_ID)
        .first()
    )

    if not watchlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ウォッチリストアイテムが見つかりません",
        )

    price_histories = (
        db.query(PriceHistory)
        .filter(PriceHistory.product_id == watchlist_item.product_id)
        .order_by(PriceHistory.observed_at.desc())
        .all()
    )

    result = [
        PriceHistoryItem(
            price=ph.price,
            recorded_at=ph.observed_at,
        )
        for ph in price_histories
    ]

    return PriceHistoryResponse(price_history=result)
