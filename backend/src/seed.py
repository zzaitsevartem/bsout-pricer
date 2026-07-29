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
            Store(name="ТГСМ", slug="tgssm", website_url="https://taggsm.ru", logo_url="/logos/taggsm.webp"),
            Store(name="Профи", slug="profi", website_url="https://siriust.ru", logo_url="/logos/profi.webp"),
            Store(name="Либерти", slug="liberty", website_url="https://liberty-part.ru", logo_url="/logos/liberty.webp"),
            Store(name="ГринСпарк", slug="greenspark", website_url="https://greenspark.ru", logo_url="/logos/greenspark.webp"),
            Store(name="Дивизион", slug="divizion", website_url="https://divizion126.ru", logo_url="/logos/divizion.webp"),
        ]
        db.add_all(stores)
        await db.flush()
        store_ids = {s.slug: s.id for s in stores}

        # --- Categories ---
        categories = [
            Category(name="Дисплеи", slug="displays"),
            Category(name="Аккумуляторы", slug="batteries"),
            Category(name="Стекло и корпуса", slug="glass-cases"),
            Category(name="Шлейфы и разъёмы", slug="cables-connectors"),
            Category(name="Инструмент", slug="tools"),
        ]
        db.add_all(categories)
        await db.flush()
        cat_ids = {c.slug: c.id for c in categories}

        # --- Products ---
        products_data = [
            # Displays
            Product(store_id=store_ids["tgssm"], category_id=cat_ids["displays"], external_id="disp-iphone13-tgssm",
                    name='Дисплей iPhone 13 (оригинал)', normalized_name='дисплей iphone 13 оригинал',
                    price=4500.00, old_price=5200.00, currency="RUB", in_stock=True,
                    image_url="https://taggsm.ru/img/disp-iphone13.jpg",
                    product_url="https://taggsm.ru/product/disp-iphone13/"),
            Product(store_id=store_ids["profi"], category_id=cat_ids["displays"], external_id="disp-iphone13-profi",
                    name='Дисплей iPhone 13 (оригинал)', normalized_name='дисплей iphone 13 оригинал',
                    price=4800.00, currency="RUB", in_stock=True,
                    image_url="https://siriust.ru/img/disp-iphone13.jpg",
                    product_url="https://siriust.ru/product/disp-iphone13/"),
            Product(store_id=store_ids["liberty"], category_id=cat_ids["displays"], external_id="disp-iphone13-liberty",
                    name='Дисплей iPhone 13 (оригинал)', normalized_name='дисплей iphone 13 оригинал',
                    price=5100.00, currency="RUB", in_stock=True,
                    image_url="https://liberty-part.ru/img/disp-iphone13.jpg",
                    product_url="https://liberty-part.ru/product/disp-iphone13/"),
            Product(store_id=store_ids["tgssm"], category_id=cat_ids["displays"], external_id="disp-samsung-s23-tgssm",
                    name='Дисплей Samsung Galaxy S23', normalized_name='дисплей samsung galaxy s23',
                    price=6200.00, old_price=6900.00, currency="RUB", in_stock=True,
                    image_url="https://taggsm.ru/img/disp-s23.jpg",
                    product_url="https://taggsm.ru/product/disp-s23/"),
            # Batteries
            Product(store_id=store_ids["profi"], category_id=cat_ids["batteries"], external_id="bat-iphone13-profi",
                    name='Аккумулятор iPhone 13 (1715 mAh)', normalized_name='аккумулятор iphone 13 1715 mah',
                    price=1200.00, currency="RUB", in_stock=True,
                    image_url="https://siriust.ru/img/bat-iphone13.jpg",
                    product_url="https://siriust.ru/product/bat-iphone13/"),
            Product(store_id=store_ids["greenspark"], category_id=cat_ids["batteries"], external_id="bat-iphone13-greenspark",
                    name='Аккумулятор iPhone 13 (1715 mAh)', normalized_name='аккумулятор iphone 13 1715 mah',
                    price=1350.00, currency="RUB", in_stock=False,
                    image_url="https://greenspark.ru/img/bat-iphone13.jpg",
                    product_url="https://greenspark.ru/product/bat-iphone13/"),
            Product(store_id=store_ids["divizion"], category_id=cat_ids["batteries"], external_id="bat-iphone11-divizion",
                    name='Аккумулятор iPhone 11 (3110 mAh)', normalized_name='аккумулятор iphone 11 3110 mah',
                    price=1500.00, currency="RUB", in_stock=True,
                    image_url="https://divizion126.ru/img/bat-iphone11.jpg",
                    product_url="https://divizion126.ru/product/bat-iphone11/"),
            # Glass & cases
            Product(store_id=store_ids["tgssm"], category_id=cat_ids["glass-cases"], external_id="glass-iphone13-tgssm",
                    name='Защитное стекло iPhone 13', normalized_name='защитное стекло iphone 13',
                    price=350.00, currency="RUB", in_stock=True,
                    image_url="https://taggsm.ru/img/glass-iphone13.jpg",
                    product_url="https://taggsm.ru/product/glass-iphone13/"),
            Product(store_id=store_ids["liberty"], category_id=cat_ids["glass-cases"], external_id="case-iphone15-liberty",
                    name='Чехол iPhone 15 силиконовый', normalized_name='чехол iphone 15 силиконовый',
                    price=890.00, old_price=1200.00, currency="RUB", in_stock=True,
                    image_url="https://liberty-part.ru/img/case-iphone15.jpg",
                    product_url="https://liberty-part.ru/product/case-iphone15/"),
            # Cables & connectors
            Product(store_id=store_ids["profi"], category_id=cat_ids["cables-connectors"], external_id="flex-charge-type-c-profi",
                    name='Шлейф зарядки Type-C универсальный', normalized_name='шлейф зарядки type c универсальный',
                    price=450.00, currency="RUB", in_stock=True,
                    image_url="https://siriust.ru/img/flex-type-c.jpg",
                    product_url="https://siriust.ru/product/flex-type-c/"),
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
