from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.middleware.rate_limit import RateLimitMiddleware
from src.modules.admin.controller import admin_router
from src.modules.auth.controller import auth_router
from src.modules.categories.controller import categories_router
from src.modules.health.controller import health_router
from src.modules.parser.controller import parser_router
from src.modules.payment.controller import payment_router
from src.modules.products.controller import products_router
from src.modules.search.controller import search_router
from src.modules.stores.controller import stores_router
from src.modules.users.controller import users_router

app = FastAPI(title="BScout API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, max_requests=120, window=60)

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
