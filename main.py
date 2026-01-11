from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv

load_dotenv()

from database import get_db, engine, Base

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Amaejozu Backend starting...")
    logger.info(f"Database engine: {engine.url}")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection test successful")
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
    yield
    logger.info("👋 Amaejozu Backend shutting down...")
    engine.dispose()


app = FastAPI(
    title="Amaejozu API",
    description="メンズコスメ価格下落通知アプリ",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定 (重要!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # ブラウザから
        "http://frontend:3000",  # コンテナ間通信
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ルートエンドポイント
@app.get("/")
async def root():
    return {
        "message": "Amaejozu Backend API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


# ヘルスチェックエンドポイント
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "Amaejozu Backend",
        "message": "Connected via Docker network!",
        "network": "amaejozu-network",
    }


@app.get("/api/db/health")
async def db_health_check(db: Session = Depends(get_db)):
    """データベース接続のエンドポイント

    Returns:
        - status: データベース接続状態
        - database: データベース名
        - server_version: MySQLバージョン
    """
    try:
        result = db.execute(text("SELECT VERSION() as version, DATABASE() as db_name"))
        row = result.fetchone()

        return {
            "status": "connected",
            "database": row.db_name if row else "unknown",
            "server_version": row.version if row else "unknown",
            "message": "Azure MySQL connection successful!",
        }
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/db/tables")
async def list_tables(db: Session = Depends(get_db)):
    """
    データベース内のテーブル一覧を取得

    Returns:
        - tables: テーブル名のリスト
    """
    try:
        result = db.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]

        return {"status": "ok", "count": len(tables), "tables": tables}
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        return {"status": "error", "message": str(e)}


# (startup/shutdown は lifespan に移行済み)
