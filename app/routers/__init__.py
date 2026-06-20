from app.routers.account import router as account_router
from app.routers.admin import router as admin_router
from app.routers.chat import router as chat_router
from app.routers.orders import router as orders_router
from app.routers.pages import router as pages_router
from app.routers.products import router as products_router
from app.routers.quiz import router as quiz_router

__all__ = ["account_router", "admin_router", "chat_router", "orders_router", "pages_router", "products_router", "quiz_router"]
