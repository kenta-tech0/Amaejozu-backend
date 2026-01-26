"""
バッチスケジューラーサービス

APSchedulerを使用して定期バッチ処理を実行する
- キャッシュウォームアップ: 6時間ごと
- 価格更新: 6時間ごと

楽天APIレート制限: 1リクエスト/秒
- キャッシュウォームアップ: 約18キーワード × 1秒 = 約18秒
- 価格更新: 商品数 × 1秒（リトライ含む）

同時実行防止のため、ジョブはロックで排他制御する
"""

import logging
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

logger = logging.getLogger(__name__)

# スケジューラーインスタンス（グローバル）
scheduler = BackgroundScheduler()

# 楽天API呼び出しの排他制御用ロック
# 同時に1つのジョブのみAPIを呼び出せるようにする
api_lock = threading.Lock()


def run_cache_warmup_job():
    """
    キャッシュウォームアップジョブ

    楽天APIレート制限（1リクエスト/秒）を遵守
    - run_cache_warmup内で各リクエスト間に1秒のウェイトあり
    """
    # ロックを取得（他のジョブとの同時実行を防止）
    acquired = api_lock.acquire(blocking=False)
    if not acquired:
        logger.warning("⏳ キャッシュウォームアップ: 他のジョブが実行中のためスキップ")
        return

    try:
        from app.scripts.run_cache_warmup import run_cache_warmup

        logger.info(f"🔥 キャッシュウォームアップ開始: {datetime.now().isoformat()}")
        logger.info("   ※ 楽天APIレート制限: 1リクエスト/秒")

        result = run_cache_warmup()

        logger.info(
            f"✅ キャッシュウォームアップ完了: "
            f"成功={result['success']}, スキップ={result['skipped']}, "
            f"エラー={result['errors']}, 処理時間={result['duration_seconds']:.2f}秒"
        )
    except Exception as e:
        logger.error(f"❌ キャッシュウォームアップエラー: {str(e)}")
    finally:
        api_lock.release()


def run_price_update_job():
    """
    価格更新ジョブ

    楽天APIレート制限（1リクエスト/秒）を遵守
    - 各商品の価格取得間に1秒のウェイトを入れる
    """
    import time

    # ロックを取得（他のジョブとの同時実行を防止）
    acquired = api_lock.acquire(blocking=False)
    if not acquired:
        logger.warning("⏳ 価格更新: 他のジョブが実行中のためスキップ")
        return

    try:
        from app.services.price_batch import PriceBatchProcessor
        from app.database import SessionLocal

        logger.info(f"💰 価格更新バッチ開始: {datetime.now().isoformat()}")
        logger.info("   ※ 楽天APIレート制限: 1リクエスト/秒")

        db = SessionLocal()
        try:
            processor = PriceBatchProcessor(db)

            # ウォッチリスト商品を取得
            products = processor.get_watchlist_products()

            if not products:
                logger.info("✅ 価格更新完了: 処理対象の商品なし")
                return

            # 各商品を処理（レート制限を守る）
            for i, product in enumerate(products):
                logger.info(f"  [{i+1}/{len(products)}] {product.name[:40]}...")
                processor.process_product(product)

                # 最後の商品以外は1秒待機（楽天APIレート制限）
                if i < len(products) - 1:
                    time.sleep(1.0)

            # コミット
            db.commit()

            logger.info(
                f"✅ 価格更新完了: "
                f"処理={len(products)}, 更新={processor.updated_count}, "
                f"エラー={processor.error_count}"
            )
        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ 価格更新バッチエラー: {str(e)}")
    finally:
        api_lock.release()


def run_weekly_ranking_job():
    """
    週間TOP10ランキング生成ジョブ

    毎週日曜日 0:00 に実行
    """
    # ロックを取得（他のジョブとの同時実行を防止）
    acquired = api_lock.acquire(blocking=False)
    if not acquired:
        logger.warning("⏳ 週間ランキング: 他のジョブが実行中のためスキップ")
        return

    try:
        from app.services.weekly_ranking_batch import run_weekly_ranking_batch

        logger.info(f"📊 週間TOP10ランキング生成開始: {datetime.now().isoformat()}")

        result = run_weekly_ranking_batch()

        logger.info(
            f"✅ 週間ランキング生成完了: "
            f"週={result.get('week_label', 'N/A')}, "
            f"成功={result.get('success', 0)}, "
            f"エラー={result.get('errors', 0)}, "
            f"処理時間={result.get('duration_seconds', 0):.2f}秒"
        )
    except Exception as e:
        logger.error(f"❌ 週間ランキング生成エラー: {str(e)}")
    finally:
        api_lock.release()


def start_scheduler():
    """スケジューラーを開始"""
    if scheduler.running:
        logger.warning("スケジューラーは既に実行中です")
        return

    # キャッシュウォームアップ: 6時間ごと（0:00, 6:00, 12:00, 18:00）
    scheduler.add_job(
        run_cache_warmup_job,
        trigger=IntervalTrigger(hours=6),
        id="cache_warmup",
        name="キャッシュウォームアップ",
        replace_existing=True,
        max_instances=1,  # 同時に1インスタンスのみ
    )

    # 価格更新: 6時間ごと、キャッシュウォームアップから3時間後
    # （3:00, 9:00, 15:00, 21:00）
    # 同時実行を避けるため十分な間隔を確保
    scheduler.add_job(
        run_price_update_job,
        trigger=IntervalTrigger(hours=6, start_date="2024-01-01 03:00:00"),
        id="price_update",
        name="価格更新バッチ",
        replace_existing=True,
        max_instances=1,  # 同時に1インスタンスのみ
    )

    # 週間TOP10ランキング生成: 毎週日曜日 0:00
    scheduler.add_job(
        run_weekly_ranking_job,
        trigger=CronTrigger(day_of_week="sun", hour=0, minute=0),
        id="weekly_ranking",
        name="週間TOP10ランキング生成",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info("📅 スケジューラー開始")
    logger.info("   - キャッシュウォームアップ: 6時間ごと")
    logger.info("   - 価格更新バッチ: 6時間ごと（3時間オフセット）")
    logger.info("   - 週間TOP10ランキング: 毎週日曜日 0:00")
    logger.info("   ※ 楽天APIレート制限（1req/sec）を遵守")
    logger.info("   ※ ジョブは排他制御により同時実行されません")


def stop_scheduler():
    """スケジューラーを停止"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("📅 スケジューラー停止")


def get_scheduler_status() -> dict:
    """スケジューラーの状態を取得"""
    jobs = []
    if scheduler.running:
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            })

    return {
        "running": scheduler.running,
        "jobs": jobs,
        "note": "楽天APIレート制限: 1リクエスト/秒",
    }
