# Amaejozu-backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS設定 (重要!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # ブラウザから
        "http://frontend:3000",       # コンテナ間通信
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
        "status": "running"
    }

# ヘルスチェックエンドポイント
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "Amaejozu Backend",
        "message": "Connected via Docker network!",
        "network": "amaejozu-network"
    }

# FastAPI自動ドキュメントは /docs で確認可能