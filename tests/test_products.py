"""
商品検索エンドポイントのテスト
"""

import pytest


class TestProductSearch:
    """商品検索テスト"""

    def test_search_products_success(self, client):
        """正常な商品検索"""
        response = client.get(
            "/api/products/search",
            params={"keyword": "化粧水"}
        )
        # 楽天APIの応答に依存するため、ステータスコードのみ確認
        assert response.status_code in [200, 404, 503]

    def test_search_products_without_keyword(self, client):
        """キーワードなしで検索（空の結果を返す）"""
        response = client.get("/api/products/search")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data

    def test_search_products_with_pagination(self, client):
        """ページネーション付き検索"""
        response = client.get(
            "/api/products/search",
            params={
                "keyword": "メンズ",
                "page": 1,
                "limit": 10
            }
        )
        assert response.status_code in [200, 404, 503]


class TestProductList:
    """商品一覧テスト"""

    def test_list_products(self, client):
        """商品一覧取得"""
        response = client.get("/api/products")
        assert response.status_code == 200

    def test_list_products_with_pagination(self, client):
        """ページネーション付き商品一覧"""
        response = client.get(
            "/api/products",
            params={"skip": 0, "limit": 10}
        )
        assert response.status_code == 200


class TestCategories:
    """カテゴリテスト"""

    def test_list_categories(self, client):
        """カテゴリ一覧取得"""
        response = client.get("/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data


class TestBrands:
    """ブランドテスト"""

    def test_list_brands(self, client):
        """ブランド一覧取得"""
        response = client.get("/api/brands")
        assert response.status_code == 200
        data = response.json()
        assert "brands" in data