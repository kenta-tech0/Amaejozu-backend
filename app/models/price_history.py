"""
PriceHistory Model - 価格履歴テーブル
"""
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .product import Product


class PriceHistory(Base):
    """価格履歴テーブル"""
    __tablename__ = "price_histories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="price_histories")
