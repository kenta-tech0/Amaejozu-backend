"""Base model for SQLAlchemy models"""
from app.database import Base

# 他のモデルはこのBaseを継承して作成します
__all__ = ["Base"]