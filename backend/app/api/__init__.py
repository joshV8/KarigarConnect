from app.api.health import router as health_router
from app.api.products import router as products_router
from app.api.catalogs import router as catalogs_router
from app.api.buyers import router as buyers_router
from app.api.users import router as users_router

__all__ = [
    "health_router",
    "products_router",
    "catalogs_router",
    "buyers_router",
    "users_router",
]
