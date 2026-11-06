import asyncio
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select, func
from src.database import async_session_factory
from src.modules.auth.model.user import Subscription, User
from src.modules.auth.service.auth import create_access_token


async def active_user():
    async with async_session_factory() as db:
        return await db.scalar(
            select(User.id)
            .join(Subscription, Subscription.user_id == User.id)
            .where(User.is_active.is_(True), Subscription.is_active.is_(True),
                   Subscription.end_date > func.now())
            .order_by(User.id).limit(1)
        )


def fetch(path, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    with urlopen(Request("http://127.0.0.1:8000" + path, headers=headers), timeout=20) as r:
        return json.load(r)


assert fetch("/api/health")
openapi = fetch("/openapi.json")
assert "/api/products/catalog/suggestions" in openapi["paths"]
user = asyncio.run(active_user())
if user is None:
    raise SystemExit("No active subscribed user for authenticated read-only check")
token = create_access_token(user)
base = "/api/products/catalog?"
queries = ("защитная плёнка apple iphone 15", "защитная plenka apple iphone 15")
results = []
for query in queries:
    data = fetch(base + urlencode({"q": query, "per_page": 100}), token)
    results.append({row["id"] for row in data["results"]})
if not results[0] or not results[0] <= results[1]:
    raise SystemExit(f"Real catalog equivalence failed: literal={len(results[0])}, expanded={len(results[1])}, overlap={len(results[0] & results[1])}")
suggestions = fetch("/api/products/catalog/suggestions?" + urlencode({"q": queries[1]}), token)
if not suggestions:
    raise SystemExit("No real suggestions for expanded query")
print(f"RUNTIME_PASS literal={len(results[0])} expanded={len(results[1])} suggestions={len(suggestions)}")
