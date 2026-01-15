"""
SQLAlchemy Models for Amaejozu Application
Based on 要件定義書20260114.xlsx - データ要件

Usage:
    from models import User, Brand, Category, Product, etc.
    # または
    from models import Base
"""

from .base import Base
from .user import User
from .brand import Brand
from .category import Category
from .product import Product
from .price_history import PriceHistory
from .watchlist import Watchlist
from .alert import Alert
from .notification_history import Notification
from .brand_follow import BrandFollow
from .user_interest import UserInterest

__all__ = [
    "Base",
    "User",
    "Brand",
    "Category",
    "Product",
    "PriceHistory",
    "Watchlist",
    "Alert",
    "Notification",
    "BrandFollow",
    "UserInterest",
]
