"""
商品検索キャッシュサービス
TTL付きメモリキャッシュで楽天API検索結果を保存
"""

import threading
from datetime import datetime
from typing import Optional, List, Dict, Any
from cachetools import TTLCache


class ProductCacheService:
    """商品検索結果のメモリキャッシュ"""

    # デフォルトTTL: 6時間
    DEFAULT_TTL = 6 * 60 * 60
    # 最大キャッシュ数: 1000キーワード
    DEFAULT_MAX_SIZE = 1000

    def __init__(self, ttl: int = DEFAULT_TTL, max_size: int = DEFAULT_MAX_SIZE):
        """
        Args:
            ttl: キャッシュ有効期限（秒）
            max_size: 最大キャッシュ数
        """
        self._cache: TTLCache = TTLCache(maxsize=max_size, ttl=ttl)
        self._lock = threading.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
        }

    def _normalize_key(self, keyword: str) -> str:
        """キーワードを正規化（小文字化、トリム）"""
        return keyword.strip().lower()

    def get(self, keyword: str) -> Optional[List[Dict[str, Any]]]:
        """
        キャッシュから商品リストを取得

        Args:
            keyword: 検索キーワード

        Returns:
            商品リスト or None（キャッシュミス）
        """
        key = self._normalize_key(keyword)
        with self._lock:
            result = self._cache.get(key)
            if result is not None:
                self._stats["hits"] += 1
                return result
            else:
                self._stats["misses"] += 1
                return None

    def set(self, keyword: str, products: List[Dict[str, Any]]) -> None:
        """
        商品リストをキャッシュに保存

        Args:
            keyword: 検索キーワード
            products: 商品リスト
        """
        key = self._normalize_key(keyword)
        with self._lock:
            self._cache[key] = products
            self._stats["sets"] += 1

    def delete(self, keyword: str) -> bool:
        """
        特定のキーワードのキャッシュを削除

        Args:
            keyword: 検索キーワード

        Returns:
            削除成功かどうか
        """
        key = self._normalize_key(keyword)
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> int:
        """
        全キャッシュをクリア

        Returns:
            クリアしたキャッシュ数
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def has(self, keyword: str) -> bool:
        """
        キーワードがキャッシュに存在するか

        Args:
            keyword: 検索キーワード

        Returns:
            存在するかどうか
        """
        key = self._normalize_key(keyword)
        with self._lock:
            return key in self._cache

    def get_stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計を取得

        Returns:
            統計情報
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                self._stats["hits"] / total_requests * 100
                if total_requests > 0 else 0
            )
            return {
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "sets": self._stats["sets"],
                "hit_rate": round(hit_rate, 2),
                "current_size": len(self._cache),
                "max_size": self._cache.maxsize,
                "ttl_seconds": self._cache.ttl,
            }

    def get_cached_keywords(self) -> List[str]:
        """
        キャッシュされているキーワード一覧を取得

        Returns:
            キーワードリスト
        """
        with self._lock:
            return list(self._cache.keys())


# シングルトンインスタンス
product_cache = ProductCacheService()
