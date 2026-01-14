"""
Watchlist Model - アイテムウォッチテーブル (ウォッチリスト)
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .product import Product
    from .alert import Alert


class Watchlist(Base):
    """アイテムウォッチテーブル (ウォッチリスト)"""
    __tablename__ = "watchlists"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_user_product"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    target_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notify_any_drop: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="watchlists")
    product: Mapped["Product"] = relationship("Product", back_populates="watchlists")
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="watchlist",
        cascade="all, delete-orphan"
    )
