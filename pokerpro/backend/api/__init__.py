from .auth import router as auth_router, get_current_user
from .onboarding import router as onboarding_router
from .academy import router as academy_router
from .gto_engine import router as gto_router
from .hand_analyzer import router as hand_analyzer_router

# Export routers
router = auth_router

__all__ = [
    "auth",
    "onboarding",
    "academy",
    "gto_engine",
    "hand_analyzer",
    "get_current_user"
]
