"""
週間TOP10ランキング生成サービス

機能:
- ウォッチリスト集計によるTOP10抽出
- Azure OpenAI による推薦文生成
- 前週ランキングとの比較
- DBへのランキング保存
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.models.product import Product
from app.models.watchlist import Watchlist
from app.models.weekly_ranking import WeeklyRanking
from app.services.openai_service import (
    _create_openai_client,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    validate_env_variables,
)

logger = logging.getLogger(__name__)


class WeeklyRankingService:
    """週間TOP10ランキング生成サービス"""

    def __init__(self, db: Session):
        self.db = db
        self.success_count = 0
        self.error_count = 0
        self.skipped_count = 0

    @staticmethod
    def get_current_week() -> Tuple[int, int]:
        """現在のISO週を取得 (year, week_number)"""
        now = datetime.now()
        iso_calendar = now.isocalendar()
        return iso_calendar.year, iso_calendar.week

    @staticmethod
    def get_previous_week(year: int, week: int) -> Tuple[int, int]:
        """前週のISO週を取得"""
        # 現在週の月曜日を計算
        jan_4 = datetime(year, 1, 4)
        week_one_monday = jan_4 - timedelta(days=jan_4.weekday())
        current_monday = week_one_monday + timedelta(weeks=week - 1)

        # 1週前の月曜日
        previous_monday = current_monday - timedelta(weeks=1)
        prev_iso = previous_monday.isocalendar()

        return prev_iso.year, prev_iso.week

    def get_top10_products(self) -> List[Dict]:
        """
        ウォッチリスト登録数でTOP10商品を取得

        Returns:
            List[Dict]: product_id, watchlist_count を含む辞書のリスト
        """
        try:
            # ウォッチリスト集計クエリ（distinct user_id でカウント）
            results = (
                self.db.query(
                    Watchlist.product_id,
                    func.count(func.distinct(Watchlist.user_id)).label("watchlist_count"),
                )
                .group_by(Watchlist.product_id)
                .order_by(desc("watchlist_count"))
                .limit(10)
                .all()
            )

            if not results:
                logger.warning("ウォッチリストに商品が登録されていません")
                return []

            top10 = [
                {"product_id": r.product_id, "watchlist_count": r.watchlist_count}
                for r in results
            ]

            logger.info(f"TOP10商品を抽出: {len(top10)}件")
            return top10

        except Exception as e:
            logger.error(f"TOP10抽出エラー: {str(e)}")
            raise

    def get_previous_rank(
        self, product_id: str, prev_year: int, prev_week: int
    ) -> Optional[int]:
        """前週のランキング順位を取得"""
        try:
            prev_ranking = (
                self.db.query(WeeklyRanking.rank_position)
                .filter(
                    WeeklyRanking.product_id == product_id,
                    WeeklyRanking.year == prev_year,
                    WeeklyRanking.week_number == prev_week,
                )
                .first()
            )

            return prev_ranking.rank_position if prev_ranking else None

        except Exception as e:
            logger.warning(
                f"前週ランキング取得エラー: product_id={product_id}, {str(e)}"
            )
            return None

    def generate_ai_recommendation(
        self,
        product: Product,
        rank: int,
        watchlist_count: int,
        previous_rank: Optional[int] = None,
    ) -> Optional[str]:
        """
        Azure OpenAI でランキング推薦文を生成

        Args:
            product: 商品オブジェクト
            rank: 現在のランキング順位
            watchlist_count: ウォッチリスト登録数
            previous_rank: 前週順位

        Returns:
            推薦文 or None（失敗時）
        """
        try:
            # 環境変数チェック
            if not validate_env_variables():
                logger.warning("Azure OpenAI環境変数が未設定、デフォルト推薦文を使用")
                return self._generate_fallback_recommendation(rank, watchlist_count)

            # トレンド情報
            trend_text = ""
            if previous_rank is None:
                trend_text = "今週新登場"
            elif previous_rank > rank:
                trend_text = f"前週{previous_rank}位から上昇"
            elif previous_rank < rank:
                trend_text = f"前週{previous_rank}位から下降"
            else:
                trend_text = f"前週{previous_rank}位から変動なし"

            # 価格情報
            price_info = f"現在価格: ¥{product.current_price:,}"
            if product.original_price and product.original_price > product.current_price:
                discount = product.original_price - product.current_price
                price_info += f"（定価から¥{discount:,}お得）"

            # レビュー情報
            review_info = ""
            if product.review_score and product.review_count:
                review_info = f"レビュー: {product.review_score}点 ({product.review_count}件)"

            # ブランド・カテゴリ
            brand_name = product.brand.name if product.brand else "不明"
            category_name = product.category.name if product.category else "不明"

            # プロンプト構築
            prompt = f"""あなたはメンズコスメの専門家です。週間人気ランキング{rank}位の商品について、ユーザーに魅力を伝える推薦文を日本語で作成してください。

【商品情報】
商品名: {product.name}
ブランド: {brand_name}
カテゴリ: {category_name}
{price_info}
{review_info}

【ランキング情報】
今週順位: {rank}位
ウォッチリスト登録: {watchlist_count}名
トレンド: {trend_text}

【条件】
- 120〜180文字程度で簡潔に
- ランキング順位と人気の理由を冒頭で触れる
- 男性の肌悩みや美容意識に寄り添った内容
- 価格のお得感や人気の高さを強調
- 自然で親しみやすい表現
- 絵文字は使用しない

推薦文:"""

            # OpenAI API 呼び出し
            client = _create_openai_client()
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは親切で専門的なメンズコスメアドバイザーです。人気ランキングを紹介する際は、その商品の魅力を分かりやすく伝えます。",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
                temperature=0.7,
            )

            recommendation_text = response.choices[0].message.content.strip()
            logger.info(f"AI推薦文生成成功: product_id={product.id}, rank={rank}")

            return recommendation_text

        except Exception as e:
            logger.error(f"AI推薦文生成エラー: product_id={product.id}, {str(e)}")
            # フォールバック推薦文を返す
            return self._generate_fallback_recommendation(rank, watchlist_count)

    def _generate_fallback_recommendation(self, rank: int, watchlist_count: int) -> str:
        """AI生成失敗時のフォールバック推薦文"""
        return (
            f"週間ランキング{rank}位の人気商品です。"
            f"{watchlist_count}名のユーザーがウォッチリストに登録している注目アイテムです。"
        )

    def save_weekly_ranking(
        self,
        product_id: str,
        year: int,
        week_number: int,
        rank: int,
        watchlist_count: int,
        ai_recommendation: str,
        previous_rank: Optional[int],
    ) -> None:
        """週間ランキングをDBに保存"""
        try:
            ranking = WeeklyRanking(
                id=str(uuid.uuid4()),
                product_id=product_id,
                year=year,
                week_number=week_number,
                rank_position=rank,
                watchlist_count=watchlist_count,
                ai_recommendation=ai_recommendation,
                ai_generated_at=datetime.now(),
                previous_rank=previous_rank,
            )

            self.db.add(ranking)
            logger.debug(f"ランキング保存: product_id={product_id}, rank={rank}")

        except Exception as e:
            logger.error(f"ランキング保存エラー: product_id={product_id}, {str(e)}")
            raise

    def delete_existing_rankings(self, year: int, week_number: int) -> None:
        """既存の同一週ランキングを削除（再生成時）"""
        try:
            deleted = (
                self.db.query(WeeklyRanking)
                .filter(
                    WeeklyRanking.year == year,
                    WeeklyRanking.week_number == week_number,
                )
                .delete()
            )

            if deleted > 0:
                logger.info(
                    f"既存ランキング削除: {year}-W{week_number:02d} ({deleted}件)"
                )

        except Exception as e:
            logger.error(f"既存ランキング削除エラー: {str(e)}")
            raise

    def update_product_rankings(
        self, top10_data: List[Dict], year: int, week_number: int
    ) -> None:
        """
        Product テーブルの ranking, ranking_prev フィールドを更新

        Args:
            top10_data: product_id と rank を含む辞書のリスト
            year: 年
            week_number: 週番号
        """
        try:
            # まず全商品の ranking_prev に現在の ranking を保存
            all_products = self.db.query(Product).all()
            for product in all_products:
                product.ranking_prev = product.ranking

            # TOP10 の ranking を更新
            product_ids = [item["product_id"] for item in top10_data]
            products = (
                self.db.query(Product).filter(Product.id.in_(product_ids)).all()
            )

            rank_map = {item["product_id"]: item["rank"] for item in top10_data}

            for product in products:
                product.ranking = rank_map.get(product.id)

            # TOP10 以外の商品は ranking を NULL に
            non_top10 = (
                self.db.query(Product).filter(Product.id.notin_(product_ids)).all()
            )
            for product in non_top10:
                product.ranking = None

            logger.info(f"Product.ranking 更新完了: TOP10={len(products)}件")

        except Exception as e:
            logger.error(f"Product.ranking 更新エラー: {str(e)}")
            raise

    def generate_weekly_rankings(self) -> Dict:
        """
        週間TOP10ランキングを生成（メイン処理）

        Returns:
            実行結果サマリー
        """
        logger.info("=" * 60)
        logger.info("週間TOP10ランキング生成バッチ開始")
        logger.info("=" * 60)

        start_time = datetime.now()
        year, week_number = self.get_current_week()
        prev_year, prev_week = self.get_previous_week(year, week_number)

        logger.info(f"対象週: {year}-W{week_number:02d}")
        logger.info(f"前週: {prev_year}-W{prev_week:02d}")

        try:
            # 1. TOP10商品を抽出
            top10_data = self.get_top10_products()

            if not top10_data:
                return {
                    "status": "skipped",
                    "message": "ウォッチリストに商品が登録されていません",
                    "year": year,
                    "week_number": week_number,
                }

            # 2. 既存ランキングを削除（再生成対応）
            self.delete_existing_rankings(year, week_number)

            # 3. 各商品のランキング情報を生成・保存
            processed_data = []

            for rank, item in enumerate(top10_data, start=1):
                product_id = item["product_id"]
                watchlist_count = item["watchlist_count"]

                try:
                    # 商品情報を取得（リレーション含む）
                    product = (
                        self.db.query(Product)
                        .options(
                            joinedload(Product.brand), joinedload(Product.category)
                        )
                        .filter(Product.id == product_id)
                        .first()
                    )

                    if not product:
                        logger.warning(f"商品が見つかりません: product_id={product_id}")
                        self.skipped_count += 1
                        continue

                    # 前週ランキングを取得
                    previous_rank = self.get_previous_rank(
                        product_id, prev_year, prev_week
                    )

                    # AI推薦文を生成
                    logger.info(
                        f"[{rank}/10] {product.name[:40]}... (登録: {watchlist_count}名)"
                    )
                    ai_recommendation = self.generate_ai_recommendation(
                        product, rank, watchlist_count, previous_rank
                    )

                    # DBに保存
                    self.save_weekly_ranking(
                        product_id,
                        year,
                        week_number,
                        rank,
                        watchlist_count,
                        ai_recommendation,
                        previous_rank,
                    )

                    processed_data.append({"product_id": product_id, "rank": rank})

                    self.success_count += 1

                except Exception as e:
                    logger.error(f"商品処理エラー: product_id={product_id}, {str(e)}")
                    self.error_count += 1
                    continue

            # 4. データベースにコミット
            self.db.commit()
            logger.info("週間ランキングをコミットしました")

            # 5. Product.ranking, Product.ranking_prev を更新
            self.update_product_rankings(processed_data, year, week_number)
            self.db.commit()
            logger.info("Product.ranking 更新をコミットしました")

            # 結果サマリー
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "status": "completed",
                "year": year,
                "week_number": week_number,
                "week_label": f"{year}-W{week_number:02d}",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "total": len(top10_data),
                "success": self.success_count,
                "errors": self.error_count,
                "skipped": self.skipped_count,
            }

            logger.info("=" * 60)
            logger.info("週間TOP10ランキング生成完了")
            logger.info(f"  対象週: {result['week_label']}")
            logger.info(f"  処理件数: {result['total']}")
            logger.info(f"  成功: {result['success']}")
            logger.info(f"  エラー: {result['errors']}")
            logger.info(f"  スキップ: {result['skipped']}")
            logger.info(f"  処理時間: {duration:.2f}秒")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"週間ランキング生成エラー: {str(e)}")
            self.db.rollback()
            raise
