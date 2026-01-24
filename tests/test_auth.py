"""
認証エンドポイントのテスト
"""

import pytest


class TestSignup:
    """ユーザー登録テスト"""

    def test_signup_success(self, client):
        """正常な新規登録"""
        response = client.post(
            "/auth/signup",
            json={
                "email": "newuser@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["token"] is not None
        assert data["user"]["email"] == "newuser@example.com"

    def test_signup_duplicate_email(self, client):
        """重複メールアドレスでの登録失敗"""
        # 1回目の登録
        client.post(
            "/auth/signup",
            json={
                "email": "duplicate@example.com",
                "password": "password123"
            }
        )
        # 2回目の登録（同じメール）
        response = client.post(
            "/auth/signup",
            json={
                "email": "duplicate@example.com",
                "password": "password456"
            }
        )
        assert response.status_code == 400


class TestLogin:
    """ログインテスト"""

    def test_login_success(self, client, test_user):
        """正常なログイン"""
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["token"] is not None

    def test_login_wrong_password(self, client, test_user):
        """パスワード間違い"""
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """存在しないユーザー"""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 401


class TestMe:
    """現在のユーザー情報取得テスト"""

    def test_get_me_success(self, client, auth_headers):
        """認証済みでユーザー情報取得"""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_get_me_unauthorized(self, client):
        """未認証でのアクセス"""
        response = client.get("/auth/me")
        assert response.status_code == 401