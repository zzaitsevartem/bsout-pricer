from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.config import settings
from src.database import Base
from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.auth.service.auth import create_user, hash_password
from src.modules.categories.model.category import Category
from src.modules.plans.model.plan import Plan
from src.modules.products.model.product import PriceHistory, Product
from src.modules.stores.model.store import Store


async def seed():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as db:
        existing = await db.execute(select(User).where(User.email == "admin@bscout.ru"))
        if existing.scalar_one_or_none():
            print("Seed data already exists, skipping.")
            return

        # --- Users ---
        admin = await create_user(db, "admin@bscout.ru", "admin123", "Admin User", None, "BScout")
        admin.is_admin = True

        test_user = await create_user(db, "user@bscout.ru", "user123", "Test User", "+79991234567", "Test Corp")

        await db.flush()

        # --- Subscriptions ---
        now = datetime.now(timezone.utc)
        sub_admin = Subscription(
            user_id=admin.id,
            plan=PlanEnum.advanced,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=335),
            is_active=True,
            auto_renew=True,
        )
        sub_user = Subscription(
            user_id=test_user.id,
            plan=PlanEnum.basic,
            start_date=now,
            end_date=now + timedelta(days=30),
            is_active=True,
            auto_renew=True,
        )
        db.add_all([sub_admin, sub_user])

        # --- Stores ---
        stores = [
            Store(name="Ozon", slug="ozon", website_url="https://www.ozon.ru", logo_url="https://cdn.ozon.ru/seller/logo.png"),
            Store(name="Wildberries", slug="wildberries", website_url="https://www.wildberries.ru", logo_url="https://static.wbstatic.net/seller/logo.png"),
            Store(name="Яндекс Маркет", slug="yandex-market", website_url="https://market.yandex.ru", logo_url="https://market-static.yandex.ru/logo.png"),
            Store(name="DNS", slug="dns", website_url="https://www.dns-shop.ru", logo_url="https://static.dns-shop.ru/logo.png"),
            Store(name="М.Видео", slug="mvideo", website_url="https://www.mvideo.ru", logo_url="https://cdn.mvideo.ru/logo.png"),
        ]
        db.add_all(stores)
        await db.flush()
        store_ids = {s.slug: s.id for s in stores}

        # --- Categories ---
        categories = [
            Category(name="Смартфоны", slug="smartphones"),
            Category(name="Ноутбуки", slug="laptops"),
            Category(name="Наушники", slug="headphones"),
            Category(name="Игровые консоли", slug="gaming-consoles"),
            Category(name="Умные часы", slug="smartwatches"),
        ]
        db.add_all(categories)
        await db.flush()
        cat_ids = {c.slug: c.id for c in categories}

        # --- Products ---
        products_data = [
            # Smartphones
            Product(store_id=store_ids["ozon"], category_id=cat_ids["smartphones"], external_id="iphone15-pro-ozon",
                    name='iPhone 15 Pro 256GB Natural Titanium', normalized_name='iphone 15 pro 256gb natural titanium',
                    price=129999.00, old_price=139999.00, currency="RUB", in_stock=True,
                    image_url="https://cdn.ozon.ru/iphone15pro.jpg",
                    product_url="https://www.ozon.ru/product/iphone15pro/"),
            Product(store_id=store_ids["wildberries"], category_id=cat_ids["smartphones"], external_id="samsung-s24-ultra-wb",
                    name='Samsung Galaxy S24 Ultra 512GB', normalized_name='samsung galaxy s24 ultra 512gb',
                    price=119999.00, old_price=134999.00, currency="RUB", in_stock=True,
                    image_url="https://static.wbstatic.net/s24ultra.jpg",
                    product_url="https://www.wildberries.ru/product/s24ultra/"),
            Product(store_id=store_ids["dns"], category_id=cat_ids["smartphones"], external_id="xiaomi-14-pro-dns",
                    name='Xiaomi 14 Pro 256GB', normalized_name='xiaomi 14 pro 256gb',
                    price=79999.00, currency="RUB", in_stock=True,
                    image_url="https://static.dns-shop.ru/xiaomi14pro.jpg",
                    product_url="https://www.dns-shop.ru/product/xiaomi14pro/"),
            # Laptops
            Product(store_id=store_ids["mvideo"], category_id=cat_ids["laptops"], external_id="macbook-pro-m3-mvideo",
                    name='MacBook Pro 14" M3 Pro 18GB/512GB', normalized_name='macbook pro 14 m3 pro 18gb 512gb',
                    price=249999.00, old_price=279999.00, currency="RUB", in_stock=True,
                    image_url="https://cdn.mvideo.ru/macbookpro14.jpg",
                    product_url="https://www.mvideo.ru/product/macbookpro14/"),
            Product(store_id=store_ids["yandex-market"], category_id=cat_ids["laptops"], external_id="thinkpad-x1-ym",
                    name='Lenovo ThinkPad X1 Carbon Gen 11', normalized_name='lenovo thinkpad x1 carbon gen 11',
                    price=189999.00, currency="RUB", in_stock=True,
                    image_url="https://market-static.yandex.ru/thinkpadx1.jpg",
                    product_url="https://market.yandex.ru/product/thinkpadx1/"),
            # Headphones
            Product(store_id=store_ids["ozon"], category_id=cat_ids["headphones"], external_id="airpods-pro-2-ozon",
                    name='Apple AirPods Pro 2nd Gen USB-C', normalized_name='apple airpods pro 2nd gen usb c',
                    price=21999.00, old_price=24999.00, currency="RUB", in_stock=True,
                    image_url="https://cdn.ozon.ru/airpodspro2.jpg",
                    product_url="https://www.ozon.ru/product/airpodspro2/"),
            Product(store_id=store_ids["wildberries"], category_id=cat_ids["headphones"], external_id="sony-wh1000xm5-wb",
                    name='Sony WH-1000XM5 Black', normalized_name='sony wh 1000xm5 black',
                    price=32999.00, currency="RUB", in_stock=True,
                    image_url="https://static.wbstatic.net/wh1000xm5.jpg",
                    product_url="https://www.wildberries.ru/product/wh1000xm5/"),
            # Gaming consoles
            Product(store_id=store_ids["dns"], category_id=cat_ids["gaming-consoles"], external_id="ps5-slim-dns",
                    name='Sony PlayStation 5 Slim Digital Edition', normalized_name='sony playstation 5 slim digital edition',
                    price=59999.00, currency="RUB", in_stock=True,
                    image_url="https://static.dns-shop.ru/ps5slim.jpg",
                    product_url="https://www.dns-shop.ru/product/ps5slim/"),
            Product(store_id=store_ids["mvideo"], category_id=cat_ids["gaming-consoles"], external_id="xbox-series-x-mvideo",
                    name='Microsoft Xbox Series X 1TB', normalized_name='microsoft xbox series x 1tb',
                    price=55999.00, old_price=61999.00, currency="RUB", in_stock=True,
                    image_url="https://cdn.mvideo.ru/xboxseriesx.jpg",
                    product_url="https://www.mvideo.ru/product/xboxseriesx/"),
            # Smartwatches
            Product(store_id=store_ids["yandex-market"], category_id=cat_ids["smartwatches"], external_id="apple-watch-ultra2-ym",
                    name='Apple Watch Ultra 2 49mm', normalized_name='apple watch ultra 2 49mm',
                    price=79999.00, currency="RUB", in_stock=True,
                    image_url="https://market-static.yandex.ru/watchultra2.jpg",
                    product_url="https://market.yandex.ru/product/watchultra2/"),
        ]
        db.add_all(products_data)
        await db.flush()

        # --- Price History ---
        now_ts = datetime.now(timezone.utc)
        price_history = []
        for i, p in enumerate(products_data):
            base_price = float(p.price)
            for days_ago in [30, 14, 7, 3, 1, 0]:
                ts = now_ts - timedelta(days=days_ago)
                # Simulate price fluctuations
                variation = 1.0 + (days_ago * 0.005 * (-1 if i % 2 == 0 else 1))
                hist_price = round(base_price * variation, 2)
                price_history.append(
                    PriceHistory(product_id=p.id, price=hist_price, recorded_at=ts)
                )
        db.add_all(price_history)

        await db.commit()
        print(f"Seed complete:")
        print(f"  Users: 2 (admin@bscout.ru, user@bscout.ru)")
        print(f"  Subscriptions: 2")
        print(f"  Stores: {len(stores)}")
        print(f"  Categories: {len(categories)}")
        print(f"  Products: {len(products_data)}")
        print(f"  Price history entries: {len(price_history)}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(seed())
