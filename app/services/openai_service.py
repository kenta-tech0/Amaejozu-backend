"""
Azure OpenAI連携サービス
商品お勧め文生成機能
"""

import os
import logging
from typing import Optional
from datetime import datetime, timedelta
from openai import AzureOpenAI
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.models.product import Product as ProductModel

# .envファイルから環境変数を読み込み
load_dotenv()

# ============================================
# ログ設定
# ============================================
logger = logging.getLogger(__name__)

# ============================================
# 設定
# ============================================
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = "2025-01-01-preview"

# キャッシュ有効期間（日数）
RECOMMENDATION_CACHE_TTL_DAYS = 7


# ============================================
# カスタム例外
# ============================================
class OpenAIServiceError(Exception):
    """OpenAI API関連のエラー"""

    pass


# ============================================
# レスポンスモデル
# ============================================
class RecommendationResponse(BaseModel):
    """お勧め文レスポンスモデル"""

    product_id: str
    recommendation_text: str
    generated_at: datetime
    is_cached: bool = False


# ============================================
# ユーティリティ関数
# ============================================
def validate_env_variables() -> bool:
    """
    環境変数の検証

    Returns:
        bool: 環境変数が有効な場合True
    """
    if not AZURE_OPENAI_API_KEY:
        logger.warning("AZURE_OPENAI_API_KEY が設定されていません")
        return False
    if not AZURE_OPENAI_ENDPOINT:
        logger.warning("AZURE_OPENAI_ENDPOINT が設定されていません")
        return False
    if not AZURE_OPENAI_DEPLOYMENT_NAME:
        logger.warning("AZURE_OPENAI_DEPLOYMENT_NAME が設定されていません")
        return False
    logger.info("Azure OpenAI環境変数の検証完了")
    return True


def _create_openai_client() -> AzureOpenAI:
    """Azure OpenAIクライアントを作成"""
    return AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
    )


def _build_prompt(product: ProductModel) -> str:
    """
    商品情報からプロンプトを構築

    Parameters:
        product: 商品モデル

    Returns:
        str: プロンプト文字列
    """
    # 価格情報の整形
    price_info = f"現在価格: ¥{product.current_price:,}"
    if product.original_price and product.original_price > product.current_price:
        discount = product.original_price - product.current_price
        price_info += f" (定価¥{product.original_price:,}から¥{discount:,}お得)"

    if product.lowest_price:
        price_info += f"\n過去最安値: ¥{product.lowest_price:,}"

    # レビュー情報
    review_info = ""
    if product.review_score and product.review_count:
        review_info = f"\nレビュー: {product.review_score}点 ({product.review_count}件)"

    # ブランド・カテゴリ情報
    brand_name = product.brand.name if product.brand else "不明"
    category_name = product.category.name if product.category else "不明"

    prompt = f"""あなたはメンズコスメの専門家です。以下の商品について、男性ユーザーに向けた魅力的なお勧め文を日本語で作成してください。

【商品情報】
商品名: {product.name}
ブランド: {brand_name}
カテゴリ: {category_name}
{price_info}
{review_info}

【条件】
- 100〜150文字程度で簡潔に
- 男性の肌悩みや美容意識に寄り添った内容
- 価格のお得感やコスパの良さを強調
- 誇大広告にならない自然な表現
- 絵文字は使用しない

お勧め文:"""

    return prompt


def _is_cache_valid(product: ProductModel) -> bool:
    """
    キャッシュが有効かどうか判定

    Parameters:
        product: 商品モデル

    Returns:
        bool: キャッシュが有効な場合True
    """
    if not product.recommendation_text or not product.recommendation_generated_at:
        return False

    expiry_date = product.recommendation_generated_at + timedelta(
        days=RECOMMENDATION_CACHE_TTL_DAYS
    )
    return datetime.now() < expiry_date


# ============================================
# メイン関数
# ============================================
def generate_recommendation(
    product: ProductModel, db: Session, force_regenerate: bool = False
) -> Optional[RecommendationResponse]:
    """
    商品のお勧め文を生成（キャッシュ対応）

    Parameters:
        product: 商品モデル
        db: データベースセッション
        force_regenerate: 強制再生成フラグ

    Returns:
        RecommendationResponse: お勧め文レスポンス（失敗時はNone）

    Raises:
        OpenAIServiceError: API呼び出しに失敗した場合
    """
    # 環境変数チェック
    if not validate_env_variables():
        logger.warning("Azure OpenAI環境変数が未設定のため、お勧め文生成をスキップ")
        return None

    # キャッシュチェック
    if not force_regenerate and _is_cache_valid(product):
        logger.info(f"キャッシュからお勧め文を返却: product_id={product.id}")
        return RecommendationResponse(
            product_id=product.id,
            recommendation_text=product.recommendation_text,
            generated_at=product.recommendation_generated_at,
            is_cached=True,
        )

    # 新規生成
    try:
        logger.info(f"お勧め文を生成開始: product_id={product.id}")

        client = _create_openai_client()
        prompt = _build_prompt(product)

        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "あなたは親切で専門的なメンズコスメアドバイザーです。",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.7,
        )

        recommendation_text = response.choices[0].message.content.strip()
        generated_at = datetime.now()

        # DBにキャッシュを保存
        product.recommendation_text = recommendation_text
        product.recommendation_generated_at = generated_at
        db.commit()

        logger.info(f"お勧め文を生成完了: product_id={product.id}")

        return RecommendationResponse(
            product_id=product.id,
            recommendation_text=recommendation_text,
            generated_at=generated_at,
            is_cached=False,
        )

    except Exception as e:
        logger.error(f"お勧め文生成エラー: product_id={product.id}, error={str(e)}")
        raise OpenAIServiceError(f"お勧め文の生成に失敗しました: {str(e)}")


def invalidate_recommendation_cache(product: ProductModel, db: Session) -> None:
    """
    お勧め文キャッシュを無効化

    Parameters:
        product: 商品モデル
        db: データベースセッション
    """
    product.recommendation_text = None
    product.recommendation_generated_at = None
    db.commit()
    logger.info(f"お勧め文キャッシュを無効化: product_id={product.id}")


# ============================================
# テストコード
# ============================================
if __name__ == "__main__":
    # 環境変数の検証
    if validate_env_variables():
        print("Azure OpenAI環境変数が正しく設定されています")
    else:
        print("Azure OpenAI環境変数が設定されていません")
