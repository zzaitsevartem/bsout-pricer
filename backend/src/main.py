from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import cors_origins, settings
from src.logging_config import configure_logging
from src.middleware.rate_limit import RateLimitMiddleware
from src.middleware.request_id import RequestIdMiddleware
from src.modules.admin.controller import admin_router
from src.modules.auth.controller import auth_router
from src.modules.auth.service.security import validate_security_settings
from src.modules.cache.service.redis_cache import close_redis
from src.modules.categories.controller import categories_router
from src.modules.health.controller import health_router
from src.modules.parser.controller import parser_router
from src.modules.parser.service.parsers import register_default_parsers
from src.modules.payment.controller import payment_router
from src.modules.products.controller import products_router
from src.modules.search.controller import search_router
from src.modules.stores.controller import stores_router
from src.modules.tracking.controller import notifications_router, tracking_router
from src.modules.users.controller import users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


validate_security_settings(settings)
configure_logging(getattr(settings, "log_level", "INFO"))
register_default_parsers()

_docs_enabled = settings.debug

app = FastAPI(
    title="BScout API",
    lifespan=lifespan,
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
)

app.add_middleware(RequestIdMiddleware)

app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.rate_limit_max_requests,
    window=settings.rate_limit_window,
    trust_forwarded_for=settings.rate_limit_trust_forwarded_for,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(stores_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(search_router)
app.include_router(payment_router)
app.include_router(admin_router)
app.include_router(parser_router)
app.include_router(tracking_router)
app.include_router(notifications_router)
