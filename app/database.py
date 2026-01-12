from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import QueuePool
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# mysql-connector-pythonを使用する場合の設定
# Azure MySQLの場合、SSL接続のパラメータを追加
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,            # 同時接続
    max_overflow=10,        # プールがいっぱいの時の追加接続
    pool_recycle=3600,      # 1時間で接続をリサイクル
    pool_pre_ping=True,     # 接続の有効性を事前確認
    echo=True,              # 開発時はSQL分をログ出力

    # mysql-connector-python用の接続オプション
    connect_args={
        "use_pure": True,           # pure Python実装を使用
        "ssl_disabled": False,      # SSLを有効化
    }
)

# セッションファクトリー
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base Class for ORM models
class Base(DeclarativeBase):
    pass

# 依存性注入用のジェネレータ
def get_db():
    """
    FastAPIの依存性注入で使用するDBセッション

    使用例:
        from sqlalchemy.orm import Session
        from database import get_db

        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
