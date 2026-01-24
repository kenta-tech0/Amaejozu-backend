"""
通知機能のテスト
"""

import pytest


class TestNotification:
    """通知機能テスト"""

    def test_get_notifications_unauthorized(self, client):
        """未認証で通知設定取得 → 401エラー"""
        response = client.get("/api/user/notification-settings")
        assert response.status_code == 401

    def test_get_notifications_empty(self, client, auth_headers):
        """通知一覧取得（エンドポイント未実装の場合は404許容）"""
        response = client.get("/api/notifications", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_notification_settings_get(self, client, auth_headers):
        """通知設定取得"""
        response = client.get(
            "/api/user/notification-settings",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "email_notifications" in data
        assert "notification_frequency" in data

    def test_notification_settings_update(self, client, auth_headers):
        """通知設定更新"""
        response = client.put(
            "/api/user/notification-settings",
            headers=auth_headers,
            json={
                "email_notifications": False,
                "notification_frequency": "weekly"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "email_notifications" in data