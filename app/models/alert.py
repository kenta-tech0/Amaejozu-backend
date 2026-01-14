"""
Alert Model - アラートテーブル
"""
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .watchlist import Watchlist
    from .notification_history import Notification


class Alert(Base):
    """アラートテーブル"""
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    watch_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("watchlists.id"), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "price_drop", "stock_return", etc.
    old_price: Mapped[int] = mapped_column(Integer, nullable=False)
    new_price: Mapped[int] = mapped_column(Integer, nullable=False)
    drop_rate: Mapped[float] = mapped_column(Float, nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    watchlist: Mapped["Watchlist"] = relationship("Watchlist", back_populates="alerts")
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="alert",
        cascade="all, delete-orphan"
    )
