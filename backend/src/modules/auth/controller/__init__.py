from src.modules.auth.controller.auth import router as auth_router
from src.modules.auth.controller.oauth import router as oauth_router
from src.modules.auth.controller.verification import router as verification_router

__all__ = ["auth_router", "verification_router", "oauth_router"]
