from .start import router as start_router
from .sticker_add import router as sticker_add_router
from .sticker_delete import router as sticker_delete_router
from .admin import router as admin_router
from .register import router as register_router

__all__ = [
    "start_router",
    "sticker_add_router",
    "sticker_delete_router",
    "admin_router",
    "register_router",
]
