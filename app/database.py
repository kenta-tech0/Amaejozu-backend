from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

connect_args = {}

# Azure MySQL っぽいホストなら SSL を有効化
if "mysql.database.azure.com" in DATABASE_URL:
    ssl_ca_path = os.getenv("SSL_CA_PATH")
    if not ssl_ca_path:
        # デフォルトのCA証明書パス（DigiCert Global Root CA）
        default_cert_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "DigiCertGlobalRootCA.crt.pem"
        )
        if os.path.exists(default_cert_path):
            ssl_ca_path = default_cert_path

    if ssl_ca_path and os.path.exists(ssl_ca_path):
        connect_args = {
            "ssl_ca": ssl_ca_path,
            "ssl_verify_cert": True,
        }
    else:
        # Azure MySQLはSSL必須のため、システムのCA証明書を使用
        import certifi
        connect_args = {
            "ssl_ca": certifi.where(),
            "ssl_verify_cert": True,
        }

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=True,
    connect_args=connect_args,
)

# セッションファクトリー
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
