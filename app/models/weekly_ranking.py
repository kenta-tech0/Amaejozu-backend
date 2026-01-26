"""
WeeklyRanking Model - 週間ランキングテーブル
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .product import Product


class WeeklyRanking(Base):
    """週間TOP10ランキングテーブル"""
    __tablename__ = "weekly_rankings"
    __table_args__ = (
        UniqueConstraint("product_id", "year", "week_number", name="uq_product_year_week"),
        Index("idx_year_week", "year", "week_number"),
        Index("idx_product_year_week", "product_id", "year", "week_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    watchlist_count: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    previous_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="weekly_rankings")
