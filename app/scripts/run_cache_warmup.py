"""
キャッシュウォームアップバッチ実行スクリプト

人気キーワードで事前にキャッシュを作成し、
最初のユーザーからも高速なレスポンスを実現する

使い方:
    python -m app.scripts.run_cache_warmup

cronで定期実行する場合（6時間ごと - キャッシュTTLに合わせる）:
    0 */6 * * * cd /path/to/project && python -m app.scripts.run_cache_warmup >> /var/log/cache_warmup.log 2>&1
"""
import sys
import os
import time
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from app.services.rakuten_api import search_products as rakuten_search, format_product_for_db, APIError
from app.services.cache_service import product_cache

# 人気キーワードリスト（メンズコスメ関連）
POPULAR_KEYWORDS = [
    # 基本スキンケア
    "メンズ 化粧水",
    "メンズ 洗顔",
    "メンズ 乳液",
    "メンズ スキンケア",
    "メンズ 美容液",
    "メンズ クレンジング",
    "メンズ オールインワン",
    # UV・リップケア
    "メンズ 日焼け止め",
    "メンズ リップ",
    # 人気ブランド
    "バルクオム",
    "オルビス メンズ",
    "ニベアメン",
    "uno スキンケア",
    "ギャツビー スキンケア",
    "ルシード",
    "NULL メンズ",
    "BOTCHAN",
]

# 楽天APIレート制限: 1リクエスト/秒
RATE_LIMIT_SECONDS = 1.0


def warmup_keyword(keyword: str, page: int = 1, limit: int = 20) -> dict:
    """
    1つのキーワードでキャッシュをウォームアップ

    Returns:
        結果情報（成功/失敗、件数など）
    """
    cache_key = f"{keyword}:p{page}:l{limit}"

    # 既にキャッシュがあればスキップ
    if product_cache.get(cache_key) is not None:
        return {
            "keyword": keyword,
            "status": "skipped",
            "reason": "already_cached",
            "count": 0,
        }

    try:
        # 楽天APIから検索
        result = rakuten_search(keyword, hits=limit, page=page)

        if not result or "Items" not in result:
            return {
                "keyword": keyword,
                "status": "empty",
                "reason": "no_results",
                "count": 0,
            }

        # データを整形
        products = []
        for item in result["Items"]:
            try:
                formatted = format_product_for_db(item)
                products.append(formatted)
            except Exception:
                continue

        total = result.get("count", len(products))

        # キャッシュに保存
        product_cache.set(cache_key, {"products": products, "total": total})

        return {
            "keyword": keyword,
            "status": "success",
            "count": len(products),
            "total": total,
        }

    except APIError as e:
        return {
            "keyword": keyword,
            "status": "error",
            "reason": str(e),
            "count": 0,
        }
    except Exception as e:
        return {
            "keyword": keyword,
            "status": "error",
            "reason": str(e),
            "count": 0,
        }


def run_cache_warmup(keywords: list = None) -> dict:
    """
    キャッシュウォームアップを実行

    Args:
        keywords: ウォームアップするキーワードリスト（Noneの場合はデフォルト）

    Returns:
        実行結果サマリー
    """
    if keywords is None:
        keywords = POPULAR_KEYWORDS

    start_time = time.time()
    results = []
    success_count = 0
    error_count = 0
    skipped_count = 0
    total_products = 0

    for i, keyword in enumerate(keywords):
        print(f"  [{i+1}/{len(keywords)}] '{keyword}' ...", end=" ", flush=True)

        result = warmup_keyword(keyword)
        results.append(result)

        if result["status"] == "success":
            success_count += 1
            total_products += result["count"]
            print(f"✅ {result['count']}件")
        elif result["status"] == "skipped":
            skipped_count += 1
            print("⏭️ スキップ（キャッシュ済み）")
        elif result["status"] == "empty":
            print("⚠️ 結果なし")
        else:
            error_count += 1
            print(f"❌ エラー: {result.get('reason', 'unknown')}")

        # レート制限を遵守（最後のキーワード以外）
        if i < len(keywords) - 1:
            time.sleep(RATE_LIMIT_SECONDS)

    duration = time.time() - start_time

    return {
        "status": "completed",
        "total_keywords": len(keywords),
        "success": success_count,
        "skipped": skipped_count,
        "errors": error_count,
        "total_products_cached": total_products,
        "duration_seconds": duration,
        "cache_stats": product_cache.get_stats(),
        "details": results,
    }


def main():
    """メイン処理"""
    print("=" * 60)
    print(f"🔥 キャッシュウォームアップバッチ")
    print(f"   実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   対象キーワード数: {len(POPULAR_KEYWORDS)}")
    print("=" * 60)
    print()

    try:
        # ウォームアップを実行
        result = run_cache_warmup()

        # 結果を表示
        print()
        print("=" * 60)
        print("📊 実行結果サマリー:")
        print(f"   ステータス: {result['status']}")
        print(f"   処理キーワード数: {result['total_keywords']}")
        print(f"   成功: {result['success']}")
        print(f"   スキップ: {result['skipped']}")
        print(f"   エラー: {result['errors']}")
        print(f"   キャッシュ済み商品数: {result['total_products_cached']}")
        print(f"   処理時間: {result['duration_seconds']:.2f}秒")
        print()
        print("📈 キャッシュ統計:")
        stats = result['cache_stats']
        print(f"   キャッシュサイズ: {stats['current_size']}/{stats['max_size']}")
        print(f"   ヒット数: {stats['hits']}")
        print(f"   ミス数: {stats['misses']}")
        print(f"   ヒット率: {stats['hit_rate']}%")
        print("=" * 60)
        print("\n✅ ウォームアップが完了しました")
        return 0

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
