"""
Product Model - プロダクトテーブル
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .brand import Brand
    from .category import Category
    from .price_history import PriceHistory
    from .watchlist import Watchlist


class Product(Base):
    """プロダクトテーブル"""
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    brand_id: Mapped[str] = mapped_column(String(36), ForeignKey("brands.id"), nullable=False, index=True)
    category_id: Mapped[str] = mapped_column(String(36), ForeignKey("categories.id"), nullable=False, index=True)
    rakuten_item_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    product_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    affiliate_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    current_price: Mapped[int] = mapped_column(Integer, nullable=False)
    original_price: Mapped[int] = mapped_column(Integer, nullable=False)
    lowest_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    discount_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_on_sale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    review_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    review_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ranking: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ranking_prev: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", back_populates="products")
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    price_histories: Mapped[list["PriceHistory"]] = relationship(
        "PriceHistory",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    watchlists: Mapped[list["Watchlist"]] = relationship(
        "Watchlist",
        back_populates="product",
        cascade="all, delete-orphan"
    )
