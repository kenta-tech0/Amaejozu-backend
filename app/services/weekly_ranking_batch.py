"""
週間ランキングバッチ処理
APScheduler から呼び出されるエントリーポイント
"""
import logging
from typing import Dict

from app.database import SessionLocal
from app.services.weekly_ranking_service import WeeklyRankingService

logger = logging.getLogger(__name__)


def run_weekly_ranking_batch() -> Dict:
    """
    週間TOP10ランキング生成バッチを実行

    Returns:
        実行結果サマリー
    """
    db = SessionLocal()
    try:
        service = WeeklyRankingService(db)
        return service.generate_weekly_rankings()
    except Exception as e:
        logger.error(f"週間ランキングバッチエラー: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # テスト実行用
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    result = run_weekly_ranking_batch()
    print("\n=== バッチ実行結果 ===")
    for key, value in result.items():
        print(f"{key}: {value}")
