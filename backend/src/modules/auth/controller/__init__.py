from fastapi import APIRouter

from src.modules.auth.controller.auth import router as _auth_router
from src.modules.auth.controller.oauth import router as oauth_router
from src.modules.auth.controller.password import password_router
from src.modules.auth.controller.verification import router as verification_router

auth_router = APIRouter()
auth_router.include_router(_auth_router)
auth_router.include_router(password_router)
auth_router.include_router(verification_router)
auth_router.include_router(oauth_router)

__all__ = ["auth_router", "oauth_router", "password_router", "verification_router"]
