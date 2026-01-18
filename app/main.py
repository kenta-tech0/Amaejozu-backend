"""
FastAPI メインアプリケーション
Amaejozu - メンズコスメ価格下落通知アプリ
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import List, Optional
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from app.database import get_db, engine, Base
from app.auth import router as auth_router  # 追加
from app.routers.notification import router as notification_router # 追加
from app.routers.watchlist import router as watchlist_router  # ウォッチリスト

# 楽天API連携
from app.services.rakuten_api import (
    search_products as rakuten_search,
    format_product_for_db,
    APIError,
    validate_env_variables,
    SearchResponse,
    Product,
)

# DBモデル
from app.models.product import Product as ProductModel
from app.models.brand import Brand
from app.models.category import Category

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================
# ライフサイクル管理
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションの起動・終了処理"""
    logger.info("🚀 Amaejozu Backend starting...")
    logger.info(f"Database engine: {engine.url}")

    # 環境変数の検証
    try:
        validate_env_variables()
        logger.info("✅ 楽天API環境変数の検証成功")
    except ValueError as e:
        logger.warning(f"⚠️ 楽天API環境変数: {e}")

    # DB接続テスト
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection test successful")
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")

    yield

    logger.info("👋 Amaejozu Backend shutting down...")
    engine.dispose()


# ============================================
# FastAPI アプリケーション
# ============================================
app = FastAPI(
    title="Amaejozu API",
    description="メンズコスメ価格下落通知アプリ - 楽天市場連携",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # ブラウザから
        "http://frontend:3000",  # コンテナ間通信
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 追加：authルータ登録
app.include_router(auth_router)  
app.include_router(notification_router) # 追加：notificationルータ登録
app.include_router(auth_router)
# ウォッチリストルータ登録
app.include_router(watchlist_router)

# ============================================
# 基本エンドポイント
# ============================================
@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Amaejozu Backend API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "health": "/app/api/health",
            "db_health": "/app/api/db/health",
            "product_search": "/app/api/products/search",
        },
    }


@app.get("/app/api/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "ok",
        "service": "Amaejozu Backend",
        "message": "Connected via Docker network!",
        "network": "amaejozu-network",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================
# データベース関連エンドポイント
# ============================================
@app.get("/app/api/db/health")
async def db_health_check(db: Session = Depends(get_db)):
    """データベース接続確認エンドポイント"""
    try:
        result = db.execute(text("SELECT VERSION() as version, DATABASE() as db_name"))
        row = result.fetchone()

        return {
            "status": "connected",
            "database": row.db_name if row else "unknown",
            "server_version": row.version if row else "unknown",
            "message": "Azure MySQL connection successful!",
        }
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/app/api/db/tables")
async def list_tables(db: Session = Depends(get_db)):
    """データベース内のテーブル一覧を取得"""
    try:
        result = db.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]

        return {"status": "ok", "count": len(tables), "tables": tables}
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        return {"status": "error", "message": str(e)}


# ============================================
# 楽天API 商品検索エンドポイント
# ============================================
@app.get("/app/api/products/search")
async def search_products(
    keyword: str = Query(..., description="検索キーワード"),
    page: int = Query(1, ge=1, le=100, description="ページ番号"),
    limit: int = Query(20, ge=1, le=30, description="1ページあたりの取得件数"),
    db: Session = Depends(get_db),
):
    """
    商品検索エンドポイント

    楽天APIから商品を検索し、結果を返す

    Parameters:
        keyword: 検索キーワード
        page: ページ番号（1-100）
        limit: 取得件数（1-30）

    Returns:
        商品リスト、総数、ページ情報
    """
    try:
        logger.info(f"検索リクエスト: keyword={keyword}, page={page}, limit={limit}")

        # 楽天APIから検索
        result = rakuten_search(keyword, hits=limit, page=page)

        if not result or "Items" not in result:
            raise HTTPException(status_code=404, detail="商品が見つかりませんでした")

        # データを整形
        products = []
        for item in result["Items"]:
            try:
                formatted = format_product_for_db(item)
                products.append(formatted)
            except Exception as e:
                logger.error(f"商品データ処理エラー: {str(e)}")
                continue

        logger.info(f"検索成功: {len(products)}件取得")

        return {
            "status": "ok",
            "products": products,
            "total": result.get("count", len(products)),
            "page": page,
            "limit": limit,
        }

    except APIError as e:
        logger.error(f"楽天APIエラー: {str(e)}")
        raise HTTPException(status_code=503, detail=f"楽天APIエラー: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"予期しないエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"サーバーエラー: {str(e)}")


@app.get("/app/api/products/{product_id}")
async def get_product(product_id: str, db: Session = Depends(get_db)):
    """
    商品詳細取得エンドポイント

    Parameters:
        product_id: 楽天商品ID

    Returns:
        商品詳細情報
    """
    try:
        # TODO: DBから商品を取得する処理を実装
        # product = db.query(Product).filter(Product.rakuten_product_id == product_id).first()

        return {
            "status": "ok",
            "message": "この機能は実装予定です",
            "product_id": product_id,
        }
    except Exception as e:
        logger.error(f"商品取得エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"サーバーエラー: {str(e)}")


@app.get("/app/api/products")
async def list_products(
    skip: int = Query(0, ge=0, description="スキップ件数"),
    limit: int = Query(20, ge=1, le=100, description="取得件数"),
    db: Session = Depends(get_db),
):
    """
    商品一覧取得エンドポイント

    Parameters:
        skip: スキップ件数
        limit: 取得件数

    Returns:
        商品一覧
    """
    try:
        # TODO: DBから商品一覧を取得する処理を実装
        # products = db.query(Product).offset(skip).limit(limit).all()

        return {
            "status": "ok",
            "message": "この機能は実装予定です",
            "skip": skip,
            "limit": limit,
            "products": [],
        }
    except Exception as e:
        logger.error(f"商品一覧取得エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"サーバーエラー: {str(e)}")


# ============================================
# DB商品検索エンドポイント（Issue #4）
# ============================================
@app.get("/api/products/search")
async def search_products_in_db(
    keyword: Optional[str] = Query(None, description="検索キーワード（商品名）"),
    category_id: Optional[str] = Query(None, description="カテゴリID"),
    brand_id: Optional[str] = Query(None, description="ブランドID"),
    min_price: Optional[int] = Query(None, ge=0, description="最低価格"),
    max_price: Optional[int] = Query(None, ge=0, description="最高価格"),
    sort: Optional[str] = Query(
        None, description="ソート順（price_asc, price_desc, popular）"
    ),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(20, ge=1, le=100, description="1ページあたりの取得件数"),
    db: Session = Depends(get_db),
):
    """
    DB内の商品検索エンドポイント（Issue #4）
    """
    try:
        logger.info(
            f"DB検索リクエスト: keyword={keyword}, category_id={category_id}, brand_id={brand_id}"
        )

        # ベースクエリ
        query = db.query(ProductModel)

        # キーワード検索（商品名の部分一致）
        if keyword:
            query = query.filter(ProductModel.name.ilike(f"%{keyword}%"))

        # カテゴリフィルタ
        if category_id:
            query = query.filter(ProductModel.category_id == category_id)

        # ブランドフィルタ
        if brand_id:
            query = query.filter(ProductModel.brand_id == brand_id)

        # 価格範囲フィルタ
        if min_price is not None:
            query = query.filter(ProductModel.current_price >= min_price)
        if max_price is not None:
            query = query.filter(ProductModel.current_price <= max_price)

        # ソート
        if sort == "price_asc":
            query = query.order_by(ProductModel.current_price.asc())
        elif sort == "price_desc":
            query = query.order_by(ProductModel.current_price.desc())
        elif sort == "popular":
            query = query.order_by(ProductModel.review_count.desc().nullslast())
        else:
            query = query.order_by(ProductModel.updated_at.desc())

        # 総件数を取得
        total = query.count()

        # ページネーション
        offset = (page - 1) * limit
        products = query.offset(offset).limit(limit).all()

        # レスポンス用にデータを整形
        product_list = []
        for product in products:
            product_list.append(
                {
                    "id": product.id,
                    "name": product.name,
                    "brand_id": product.brand_id,
                    "category_id": product.category_id,
                    "current_price": product.current_price,
                    "original_price": product.original_price,
                    "discount_rate": product.discount_rate,
                    "is_on_sale": product.is_on_sale,
                    "image_url": product.image_url,
                    "product_url": product.product_url,
                    "review_score": product.review_score,
                    "review_count": product.review_count,
                }
            )

        logger.info(f"DB検索成功: {len(product_list)}件取得（総数: {total}件）")

        return {
            "status": "ok",
            "products": product_list,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
        }

    except Exception as e:
        logger.error(f"DB検索エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"サーバーエラー: {str(e)}")


@app.get("/api/categories")
async def list_categories(db: Session = Depends(get_db)):
    """カテゴリ一覧を取得"""
    try:
        categories = db.query(Category).order_by(Category.sort_order).all()
        return {
            "status": "ok",
            "categories": [
                {"id": c.id, "name": c.name, "slug": c.slug} for c in categories
            ],
            "count": len(categories),
        }
    except Exception as e:
        logger.error(f"カテゴリ取得エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/brands")
async def list_brands(db: Session = Depends(get_db)):
    """ブランド一覧を取得"""
    try:
        brands = db.query(Brand).order_by(Brand.name).all()
        return {
            "status": "ok",
            "brands": [
                {"id": b.id, "name": b.name, "shop_code": b.shop_code} for b in brands
            ],
            "count": len(brands),
        }
    except Exception as e:
        logger.error(f"ブランド取得エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 開発サーバー起動
# ============================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
