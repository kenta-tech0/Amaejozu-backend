"""
Pydantic Schemas for Amaejozu Application
Based on app/models
"""

from .base import BaseSchema
from .user import UserBase, UserCreate, UserUpdate, UserResponse
from .category import CategoryBase, CategoryCreate, CategoryUpdate, CategoryResponse
from .brand import BrandBase, BrandCreate, BrandUpdate, BrandResponse
from .product import (
    ProductBase,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductWithBrandCategory,
)
from .price_history import PriceHistoryBase, PriceHistoryCreate, PriceHistoryResponse
from .watchlist import (
    WatchlistCreateRequest,
    WatchlistItemResponse,
    WatchlistResponse,
    ProductInWatchlist,
)
from .alert import AlertBase, AlertCreate, AlertResponse
from .notification import (
    NotificationBase,
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
)
from .brand_follow import (
    BrandFollowBase,
    BrandFollowCreate,
    BrandFollowResponse,
    BrandFollowWithBrand,
)
from .user_interest import (
    UserInterestBase,
    UserInterestCreate,
    UserInterestResponse,
    UserInterestWithCategory,
)

# Rebuild models with forward references
ProductWithBrandCategory.model_rebuild()
BrandFollowWithBrand.model_rebuild()
UserInterestWithCategory.model_rebuild()

__all__ = [
    "BaseSchema",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "BrandBase",
    "BrandCreate",
    "BrandUpdate",
    "BrandResponse",
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductWithBrandCategory",
    "PriceHistoryBase",
    "PriceHistoryCreate",
    "PriceHistoryResponse",
    "WatchlistCreateRequest",
    "WatchlistItemResponse",
    "WatchlistResponse",
    "ProductInWatchlist",
    "AlertBase",
    "AlertCreate",
    "AlertResponse",
    "NotificationBase",
    "NotificationCreate",
    "NotificationUpdate",
    "NotificationResponse",
    "BrandFollowBase",
    "BrandFollowCreate",
    "BrandFollowResponse",
    "BrandFollowWithBrand",
    "UserInterestBase",
    "UserInterestCreate",
    "UserInterestResponse",
    "UserInterestWithCategory",
]
