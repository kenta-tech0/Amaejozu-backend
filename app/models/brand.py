"""
Brand Model - ブランドテーブル
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .product import Product
    from .brand_follow import BrandFollow


class Brand(Base):
    """ブランドテーブル"""
    __tablename__ = "brands"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    shop_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="brand",
        cascade="all, delete-orphan"
    )
    brand_follows: Mapped[list["BrandFollow"]] = relationship(
        "BrandFollow",
        back_populates="brand",
        cascade="all, delete-orphan"
    )
