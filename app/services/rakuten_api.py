"""
楽天API連携サービス
メンズコスメ値下げ通知アプリ用

機能:
- 商品検索API
- ランキングAPI
- データ整形（DB保存用）
"""

import os
import requests
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from datetime import datetime
from pydantic import BaseModel, Field, validator
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# .envファイルから環境変数を読み込み
load_dotenv()

# ============================================
# ログ設定
# ============================================
logger = logging.getLogger(__name__)

# ============================================
# 設定
# ============================================
RAKUTEN_APP_ID = os.getenv("RAKUTEN_APP_ID")
RAKUTEN_AFFILIATE_ID = os.getenv("RAKUTEN_AFFILIATE_ID")

# APIエンドポイント
ITEM_SEARCH_API = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"
RANKING_API = "https://app.rakuten.co.jp/services/api/IchibaItem/Ranking/20220601"

# リトライ設定
MAX_RETRIES = 3
BACKOFF_FACTOR = 1  # 1秒, 2秒, 4秒...
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]


# ============================================
# カスタム例外
# ============================================
class APIError(Exception):
    """API関連のエラー"""
    pass


# ============================================
# Pydanticモデル
# ============================================
class Product(BaseModel):
    """商品モデル"""
    rakuten_product_id: str = Field(..., alias="itemCode")
    name: str = Field(..., alias="itemName")
    brand: Optional[str] = None
    price: int = Field(..., alias="itemPrice")
    image_url: Optional[str] = None
    shop_url: str = Field(..., alias="itemUrl")
    affiliate_url: Optional[str] = Field(None, alias="affiliateUrl")
    category: Optional[str] = None
    review_score: Optional[float] = Field(None, alias="reviewAverage")
    review_count: Optional[int] = Field(None, alias="reviewCount")
    shop_name: Optional[str] = Field(None, alias="shopName")
    shop_code: Optional[str] = Field(None, alias="shopCode")
    
    class Config:
        populate_by_name = True
    
    @validator('image_url', pre=True, always=True)
    def extract_image_url(cls, v, values):
        """画像URLを抽出"""
        if isinstance(v, list) and len(v) > 0:
            return v[0].get('imageUrl') if isinstance(v[0], dict) else v[0]
        return v
    
    @validator('brand', pre=True, always=True)
    def extract_brand(cls, v, values):
        """ブランド名を抽出（商品名から推測）"""
        if v:
            return v
        # 商品名からブランドを推測（簡易版）
        item_name = values.get('name', '')
        for brand in ['BULK HOMME', 'SK-II', 'ORBIS', 'FANCL', 'UNO', 'LUCIDO']:
            if brand in item_name.upper():
                return brand
        return None
    
    @validator('category', pre=True, always=True)
    def set_default_category(cls, v):
        """デフォルトカテゴリを設定"""
        return v or "化粧水"


class SearchResponse(BaseModel):
    """検索レスポンスモデル"""
    products: List[Product]
    total: int
    page: int
    limit: int


# ============================================
# ユーティリティ関数
# ============================================
def validate_env_variables() -> None:
    """
    環境変数の検証
    
    Raises:
        ValueError: 必須の環境変数が設定されていない場合
    """
    if not RAKUTEN_APP_ID:
        raise ValueError("RAKUTEN_APP_ID が設定されていません。.envファイルを確認してください。")
    logger.info(f"環境変数の検証完了: APP_ID={RAKUTEN_APP_ID[:8]}...")


def _create_session_with_retry() -> requests.Session:
    """リトライ機能付きのセッションを作成"""
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=RETRY_STATUS_CODES,
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# ============================================
# 商品検索API
# ============================================
def search_products(keyword: str, hits: int = 10, page: int = 1) -> Optional[Dict[str, Any]]:
    """
    楽天市場商品検索API
    
    Parameters:
        keyword: 検索キーワード
        hits: 取得件数（1-30）
        page: ページ番号
    
    Returns:
        商品リストのJSON
    
    Raises:
        APIError: API呼び出しに失敗した場合
    """
    params = {
        "applicationId": RAKUTEN_APP_ID,
        "affiliateId": RAKUTEN_AFFILIATE_ID,
        "keyword": keyword,
        "hits": hits,
        "page": page,
        "genreId": "100939",  # 美容・コスメ・香水
        "formatVersion": 2,
    }
    
    session = _create_session_with_retry()
    
    try:
        logger.info(f"API呼び出し開始: keyword={keyword}, hits={hits}, page={page}")
        response = session.get(ITEM_SEARCH_API, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"API呼び出し成功: {len(data.get('Items', []))}件取得")
        return data
        
    except requests.exceptions.Timeout:
        logger.error("タイムアウトエラー: APIリクエストがタイムアウトしました")
        raise APIError("APIリクエストがタイムアウトしました")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPエラー: {e.response.status_code} - {e.response.text}")
        raise APIError(f"HTTPエラー: {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"リクエストエラー: {str(e)}")
        raise APIError(f"リクエストエラー: {str(e)}")
    except ValueError as e:
        logger.error(f"JSONパースエラー: {str(e)}")
        raise APIError(f"レスポンスのパースに失敗しました: {str(e)}")
    finally:
        session.close()


# ============================================
# ランキングAPI
# ============================================
def get_ranking(genre_id: str = "100939") -> Optional[Dict[str, Any]]:
    """
    楽天市場ランキングAPI
    
    Parameters:
        genre_id: ジャンルID（100939=美容・コスメ・香水）
    
    Returns:
        ランキングデータ
    
    Raises:
        APIError: API呼び出しに失敗した場合
    """
    params = {
        "applicationId": RAKUTEN_APP_ID,
        "affiliateId": RAKUTEN_AFFILIATE_ID,
        "genreId": genre_id,
        "formatVersion": 2,
    }
    
    session = _create_session_with_retry()
    
    try:
        logger.info(f"ランキングAPI呼び出し: genre_id={genre_id}")
        response = session.get(RANKING_API, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"ランキングAPI成功: {len(data.get('Items', []))}件取得")
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"ランキングAPIエラー: {str(e)}")
        raise APIError(f"ランキングAPIエラー: {str(e)}")
    finally:
        session.close()


# ============================================
# データ整形（DB保存用）
# ============================================
def format_product_for_db(item: dict) -> dict:
    """
    APIレスポンスをDB保存用に整形
    
    Parameters:
        item: 楽天APIからの商品データ
    
    Returns:
        DB保存用に整形された辞書
    
    Raises:
        ValueError: データの整形に失敗した場合
    """
    try:
        # mediumImageUrlsを正しく処理
        if 'mediumImageUrls' in item and item['mediumImageUrls']:
            item['image_url'] = item['mediumImageUrls']
        
        # Pydanticモデルでバリデーション
        product = Product(**item)
        
        return {
            "rakuten_product_id": product.rakuten_product_id,
            "name": product.name,
            "brand": product.brand,
            "image_url": product.image_url,
            "shop_url": product.shop_url,
            "affiliate_url": product.affiliate_url,
            "current_price": product.price,
            "original_price": None,  # APIからは取得できない場合がある
            "review_score": product.review_score,
            "review_count": product.review_count,
            "shop_name": product.shop_name,
            "shop_code": product.shop_code,
            "category": product.category,
            "checked_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"商品データの整形に失敗: {str(e)}")
        raise ValueError(f"商品データの整形に失敗: {str(e)}")
