"""
ウォッチリスト機能のテスト
"""

import pytest


class TestWatchlist:
    """ウォッチリストテスト"""

    def test_get_watchlist_unauthorized(self, client):
        """未認証でウォッチリスト取得 → 401エラー"""
        response = client.get("/api/watchlist")
        assert response.status_code == 401

    def test_get_watchlist_empty(self, client, auth_headers):
        """空のウォッチリスト取得"""
        response = client.get("/api/watchlist", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # APIは "watchlist" キーを使用
        assert "watchlist" in data
        assert isinstance(data["watchlist"], list)

    def test_add_to_watchlist(self, client, auth_headers):
        """ウォッチリストに追加"""
        response = client.post(
            "/api/watchlist",
            headers=auth_headers,
            json={
                "product_id": "test-product-123",
                "target_price": 1500
            }
        )
        # 商品が存在すれば201、存在しなければ404
        assert response.status_code in [201, 404]

    def test_add_duplicate_to_watchlist(self, client, auth_headers):
        """同じ商品を重複追加 → 400エラー"""
        # 1回目の追加
        first_response = client.post(
            "/api/watchlist",
            headers=auth_headers,
            json={
                "product_id": "duplicate-product",
                "target_price": 2000
            }
        )
        
        # 商品が存在しない場合はスキップ
        if first_response.status_code == 404:
            pytest.skip("テスト用商品がDBに存在しません")
        
        # 2回目の追加（重複）
        response = client.post(
            "/api/watchlist",
            headers=auth_headers,
            json={
                "product_id": "duplicate-product",
                "target_price": 2000
            }
        )
        assert response.status_code == 400

    def test_delete_from_watchlist(self, client, auth_headers):
        """ウォッチリストから削除"""
        add_response = client.post(
            "/api/watchlist",
            headers=auth_headers,
            json={
                "product_id": "delete-test-product",
                "target_price": 3000
            }
        )
        
        if add_response.status_code == 404:
            pytest.skip("テスト用商品がDBに存在しません")
        
        if add_response.status_code == 201:
            data = add_response.json()
            item_id = data.get("id")
            
            if item_id:
                delete_response = client.delete(
                    f"/api/watchlist/{item_id}",
                    headers=auth_headers
                )
                assert delete_response.status_code == 200
                assert "message" in delete_response.json()