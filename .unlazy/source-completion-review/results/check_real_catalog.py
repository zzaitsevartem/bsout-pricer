import asyncio
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select
from src.database import async_session_factory
from src.modules.auth.model.user import User
from src.modules.auth.service.auth import create_access_token

TARGET = 'Защитная плёнка Apple iPhone 15 (Чёрный)'

async def get_user_id():
    async with async_session_factory() as session:
        return await session.scalar(select(User.id).where(User.is_active.is_(True)).order_by(User.id).limit(1))

user_id = asyncio.run(get_user_id())
if user_id is None:
    raise SystemExit('FAIL: no active principal available')
token = create_access_token(user_id)
headers = {'Authorization': f'Bearer {token}'}
base = 'http://127.0.0.1:8000/api/products/catalog'

def get_json(url):
    with urlopen(Request(url, headers=headers), timeout=20) as response:
        return json.load(response)

query = urlencode({'q': 'Защитная плёнка Apple iPhone 15', 'per_page': 100})
payload = get_json(f'{base}?{query}')
items = [item for item in payload['results'] if item['canonical_name'] == TARGET]
if len(items) != 1:
    raise SystemExit(f'FAIL: expected one target product in results; found {len(items)}')
item = items[0]
source = item.get('source')
if not source or source['store_name'] != 'Профи' or not source['url']:
    raise SystemExit('FAIL: target source missing or store does not match Профи')
detail = get_json(f"{base}/{item['id']}")
offers = detail['offers']
if not offers:
    raise SystemExit('FAIL: product detail has no offers')
first = offers[0]
if (source['offer_id'] != first['id'] or source['store_id'] != first['store_id']
        or source['url'] != first['url'] or item['min_price_retail'] != first['price_retail']):
    raise SystemExit('FAIL: catalog source does not match cheapest detail offer')
print(f"Product: {item['canonical_name']}; retail: {item['min_price_retail']}; store: {source['store_name']} ({source['store_slug']}); URL: {source['url']}; offers: {len(offers)}")
print('PASS: authenticated live catalog source matches cheapest detail offer')
