from fastapi import APIRouter

from src.modules.auth.controller.auth import router as _auth_router
from src.modules.auth.controller.password import password_router

auth_router = APIRouter()
auth_router.include_router(_auth_router)
auth_router.include_router(password_router)

__all__ = ["auth_router", "password_router"]
