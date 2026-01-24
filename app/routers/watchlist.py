"""
Watchlist API エンドポイント
"""

import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.watchlist import Watchlist
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.models.user import User
from app.auth import get_current_user
from app.schemas.watchlist import (
    WatchlistCreateRequest,
    WatchlistCreateWithProductRequest,
    WatchlistResponse,
    WatchlistItemResponse,
    ProductInWatchlist,
    PriceHistoryResponse,
    PriceHistoryItem,
    MessageResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/watchlist", tags=["Watchlist"])


@router.post(
    "", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED
)
def add_to_watchlist(
    request: WatchlistCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
            Watchlist.user_id == current_user.id,
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
        user_id=current_user.id,
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
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ウォッチリスト一覧を取得
    """
    watchlist_items = (
        db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
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
def remove_from_watchlist(
    watchlist_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ウォッチリストからアイテムを削除
    """
    watchlist_item = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .first()
    )

    if not watchlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ウォッチリストアイテムが見つかりません",
        )

    # 削除処理
    db.delete(watchlist_item)
    db.commit()

    return MessageResponse(message="ウォッチリストから削除しました")


@router.get("/{watchlist_id}/price-history", response_model=PriceHistoryResponse)
def get_price_history(
    watchlist_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ウォッチリストアイテムの価格履歴を取得
    """
    # ウォッチリストアイテムの存在確認（所有権チェック含む）
    watchlist_item = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .first()
    )

    if not watchlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ウォッチリストアイテムが見つかりません",
        )

    # 価格履歴を取得
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


@router.post(
    "/with-product",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_to_watchlist_with_product(
    request: WatchlistCreateWithProductRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    商品データ付きでウォッチリストに追加

    楽天API検索結果から直接ウォッチリストに追加する場合に使用。
    商品がDBに存在しなければ自動で保存（UPSERT）する。
    """
    product_data = request.product

    # 楽天商品IDで既存商品を検索
    existing_product = (
        db.query(Product)
        .filter(Product.rakuten_product_id == product_data.rakuten_product_id)
        .first()
    )

    if existing_product:
        # 既存商品を更新（価格等の最新情報を反映）
        existing_product.name = product_data.name
        existing_product.current_price = product_data.price
        existing_product.image_url = product_data.image_url
        existing_product.product_url = product_data.product_url
        existing_product.affiliate_url = product_data.affiliate_url
        existing_product.review_score = product_data.review_average
        existing_product.review_count = product_data.review_count
        existing_product.updated_at = datetime.utcnow()
        product = existing_product
        logger.info(f"商品を更新: {product.id} - {product.name}")
    else:
        # 新規商品を作成
        product = Product(
            id=str(uuid.uuid4()),
            rakuten_product_id=product_data.rakuten_product_id,
            name=product_data.name,
            current_price=product_data.price,
            original_price=product_data.price,
            lowest_price=product_data.price,
            image_url=product_data.image_url,
            product_url=product_data.product_url,
            affiliate_url=product_data.affiliate_url,
            review_score=product_data.review_average,
            review_count=product_data.review_count,
        )
        db.add(product)
        logger.info(f"商品を新規作成: {product.id} - {product.name}")

    db.flush()  # product.idを確定

    # 重複チェック（同一ユーザー＆商品の組み合わせ）
    existing_watchlist = (
        db.query(Watchlist)
        .filter(
            Watchlist.user_id == current_user.id,
            Watchlist.product_id == product.id,
        )
        .first()
    )

    if existing_watchlist:
        db.commit()  # 商品更新は保存
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="この商品は既にウォッチリストに追加されています",
        )

    # ウォッチリストに追加
    watchlist_item = Watchlist(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        product_id=product.id,
        target_price=request.target_price,
        notify_any_drop=True,
    )

    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)

    logger.info(f"ウォッチリストに追加: {watchlist_item.id}")

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
