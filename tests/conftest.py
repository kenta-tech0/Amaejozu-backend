"""
テスト用の共通設定・フィクスチャ
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# テスト用の環境変数を設定（app.mainをインポートする前に設定）
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("RESEND_API_KEY", "test-resend-api-key")

from app.main import app
from app.database import get_db, Base


# テスト用のインメモリSQLiteデータベース
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """テスト用のDBセッションを提供"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """各テスト用のDBセッション"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """テスト用のAPIクライアント"""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(client):
    """テスト用ユーザーを作成"""
    response = client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    return response.json()


@pytest.fixture
def auth_headers(test_user):
    """認証ヘッダーを取得"""
    return {"Authorization": f"Bearer {test_user['token']}"}