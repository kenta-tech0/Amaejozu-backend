"""
Pydantic Schemas for Amaejozu Application
Based on app/models
"""

from .base import BaseSchema
from .user import UserBase, UserCreate, UserUpdate, UserResponse
from .category import (
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategorySummary,
    CategoryListResponse,
)
from .brand import (
    BrandBase,
    BrandCreate,
    BrandUpdate,
    BrandResponse,
    BrandSummary,
    BrandListResponse,
)
from .product import (
    ProductBase,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductWithBrandCategory,
    ProductSummary,
    ProductSearchResponse,
    ProductListResponse,
    ProductDetailResponse,
)
from .price_history import PriceHistoryBase, PriceHistoryCreate, PriceHistoryResponse
from .watchlist import (
    WatchlistBase,
    WatchlistCreate,
    WatchlistUpdate,
    WatchlistResponse,
    WatchlistWithProduct,
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
WatchlistWithProduct.model_rebuild()
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
    "CategorySummary",
    "CategoryListResponse",
    "BrandBase",
    "BrandCreate",
    "BrandUpdate",
    "BrandResponse",
    "BrandSummary",
    "BrandListResponse",
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductWithBrandCategory",
    "ProductSummary",
    "ProductSearchResponse",
    "ProductListResponse",
    "ProductDetailResponse",
    "PriceHistoryBase",
    "PriceHistoryCreate",
    "PriceHistoryResponse",
    "WatchlistBase",
    "WatchlistCreate",
    "WatchlistUpdate",
    "WatchlistResponse",
    "WatchlistWithProduct",
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
