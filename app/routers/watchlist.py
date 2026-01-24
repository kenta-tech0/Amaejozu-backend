"""
Watchlist API - ウォッチリスト管理
お気に入り商品の追加・削除・一覧取得
"""
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

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
    "",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ウォッチリストに追加",
    description="""
商品をウォッチリストに追加します。

## 認証
`Authorization: Bearer {token}` ヘッダーが必要です。

## 機能
- 指定した商品をウォッチリストに追加
- 目標価格（target_price）を設定可能
- 同じ商品の重複追加は不可
""",
    responses={
        201: {
            "description": "追加成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "product": {
                            "id": "prod-001",
                            "name": "メンズ化粧水 100ml",
                            "current_price": 1980,
                            "image_url": "https://example.com/image.jpg"
                        },
                        "target_price": 1500,
                        "added_at": "2026-01-24T12:00:00"
                    }
                }
            }
        },
        400: {
            "description": "重複エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "この商品は既にウォッチリストに追加されています"}
                }
            }
        },
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "認証トークンが必要です"}
                }
            }
        },
        404: {
            "description": "商品が見つからない",
            "content": {
                "application/json": {
                    "example": {"detail": "商品が見つかりません"}
                }
            }
        }
    }
)
def add_to_watchlist(
    request: WatchlistCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ウォッチリストに商品を追加"""
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

@router.get(
    "",
    response_model=WatchlistResponse,
    summary="ウォッチリスト一覧取得",
    description="""
ログインユーザーのウォッチリスト一覧を取得します。

## 認証
`Authorization: Bearer {token}` ヘッダーが必要です。

## レスポンス
登録されている商品の一覧と、各商品の現在価格・目標価格を返します。
""",
    responses={
        200: {
            "description": "取得成功",
            "content": {
                "application/json": {
                    "example": {
                        "watchlist": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "product": {
                                    "id": "prod-001",
                                    "name": "メンズ化粧水 100ml",
                                    "current_price": 1980,
                                    "image_url": "https://example.com/image.jpg"
                                },
                                "target_price": 1500,
                                "added_at": "2026-01-24T12:00:00"
                            }
                        ]
                    }
                }
            }
        },
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "認証トークンが必要です"}
                }
            }
        }
    }
)
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ウォッチリスト一覧を取得"""
    # joinedloadでProductを一緒に取得（N+1問題解消）
    watchlist_items = (
        db.query(Watchlist)
        .options(joinedload(Watchlist.product))
        .filter(Watchlist.user_id == current_user.id)
        .all()
    )

    result = []
    for item in watchlist_items:
        if item.product:
            result.append(
                WatchlistItemResponse(
                    id=item.id,
                    product=ProductInWatchlist(
                        id=item.product.id,
                        name=item.product.name,
                        current_price=item.product.current_price,
                        image_url=item.product.image_url,
                    ),
                    target_price=item.target_price,
                    added_at=item.created_at,
                )
            )

    return WatchlistResponse(watchlist=result)

@router.delete(
    "/{watchlist_id}",
    response_model=MessageResponse,
    summary="ウォッチリストから削除",
    description="""
指定したアイテムをウォッチリストから削除します。

## 認証
`Authorization: Bearer {token}` ヘッダーが必要です。

## パラメータ
- `watchlist_id`: 削除するウォッチリストアイテムのID
""",
    responses={
        200: {
            "description": "削除成功",
            "content": {
                "application/json": {
                    "example": {"message": "ウォッチリストから削除しました"}
                }
            }
        },
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "認証トークンが必要です"}
                }
            }
        },
        404: {
            "description": "アイテムが見つからない",
            "content": {
                "application/json": {
                    "example": {"detail": "ウォッチリストアイテムが見つかりません"}
                }
            }
        }
    }
)
def remove_from_watchlist(
    watchlist_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ウォッチリストからアイテムを削除"""
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
