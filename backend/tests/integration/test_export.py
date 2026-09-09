import csv
import io
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

import src.modules.export.service.pdf as pdf_module
from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.auth.service.auth import create_access_token, hash_password
from src.modules.catalog.model.catalog import Brand, Device, PartType, QualityTier
from src.modules.export.service.csv_writer import BOM, CSV_DELIMITER
from src.modules.export.service.export_service import CATALOG_HEADER, TRACKING_HEADER
from src.modules.products.model.product import Cluster, Product, StoreOffer
from src.modules.stores.model.store import Store
from src.modules.tracking.model.tracking import TrackedProduct

pytestmark = pytest.mark.integration

CATALOG_URL = "/api/export/catalog.csv"
TRACKING_URL = "/api/export/tracking.csv"
CATALOG_PDF_URL = "/api/export/catalog.pdf"

FALLBACK_CYRILLIC_FONT = "/Library/Fonts/Arial Unicode.ttf"


@pytest.fixture(autouse=True)
def register_export_router():
    from src.main import app
    from src.modules.export.controller import export_router

    registered = any(getattr(route, "path", "").startswith("/api/export") for route in app.routes)
    if not registered:
        app.include_router(export_router)
    yield


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _parse_csv(body: bytes) -> list[list[str]]:
    text = body.decode("utf-8")
    assert text.startswith(BOM)
    reader = csv.reader(io.StringIO(text[1:]), delimiter=CSV_DELIMITER)
    return [row for row in reader if row]


async def _make_user(
    db,
    email: str,
    plan: PlanEnum | None = PlanEnum.advanced,
) -> tuple[User, str]:
    user = User(
        email=email,
        password_hash=hash_password("s3cret-pass"),
        full_name="Export User",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    if plan is not None:
        now = datetime.now(timezone.utc)
        db.add(
            Subscription(
                user_id=user.id,
                plan=plan,
                start_date=now,
                end_date=now + timedelta(days=30),
                is_active=True,
            )
        )
        await db.flush()

    return user, create_access_token(user.id)


async def _make_refs(db) -> dict:
    brand = Brand(name="Apple", slug="apple")
    db.add(brand)
    await db.flush()

    device = Device(brand_id=brand.id, name="iPhone 13", model_key="apple-iphone-13")
    other_device = Device(brand_id=brand.id, name="iPhone 14", model_key="apple-iphone-14")
    part_type = PartType(code="display", name_ru="Дисплей")
    db.add_all([device, other_device, part_type])
    await db.flush()

    tier_copy = QualityTier(code="copy", name_ru="Копия", rank=10)
    tier_orig = QualityTier(code="original", name_ru="Оригинал", rank=100)
    db.add_all([tier_copy, tier_orig])
    await db.flush()

    cluster = Cluster(device_id=device.id, part_type_id=part_type.id, offers_count=0)
    other_cluster = Cluster(device_id=other_device.id, part_type_id=part_type.id, offers_count=0)
    db.add_all([cluster, other_cluster])
    await db.flush()

    return {
        "brand": brand,
        "device": device,
        "other_device": other_device,
        "part_type": part_type,
        "tier_copy": tier_copy,
        "tier_orig": tier_orig,
        "cluster": cluster,
        "other_cluster": other_cluster,
    }


async def _make_product(db, refs: dict, tier, suffix: str, name: str, cluster=None) -> Product:
    product = Product(
        cluster_id=(cluster or refs["cluster"]).id,
        quality_tier_id=tier.id,
        brand_id=refs["brand"].id,
        canonical_key=f"key-{suffix}",
        canonical_name=name,
    )
    db.add(product)
    await db.flush()
    return product


async def _make_store(db, slug: str, name: str) -> Store:
    store = Store(name=name, slug=slug, website_url=f"http://{slug}.example.com", is_active=True)
    db.add(store)
    await db.flush()
    return store


async def _make_offer(db, store: Store, product: Product, sku: str, price: str, opt: str | None):
    offer = StoreOffer(
        store_id=store.id,
        product_id=product.id,
        source_sku=sku,
        title=f"Offer {sku}",
        normalized_title=f"offer {sku}",
        price_retail=Decimal(price),
        price_opt=Decimal(opt) if opt else None,
        stock_status="in_stock",
        url=f"http://{store.slug}.example.com/{sku}",
        is_active=True,
        match_status="auto",
    )
    db.add(offer)
    await db.flush()
    return offer


async def _seed_catalog(db) -> dict:
    refs = await _make_refs(db)
    tgsm = await _make_store(db, "tgsm", "ТГСМ")
    divizion = await _make_store(db, "divizion", "Дивизион")

    copy_product = await _make_product(
        db, refs, refs["tier_copy"], "copy", "Дисплей iPhone 13 копия"
    )
    orig_product = await _make_product(
        db, refs, refs["tier_orig"], "orig", "Дисплей iPhone 13 оригинал"
    )
    other_product = await _make_product(
        db,
        refs,
        refs["tier_copy"],
        "other",
        "Дисплей iPhone 14 копия",
        cluster=refs["other_cluster"],
    )

    await _make_offer(db, tgsm, copy_product, "sku-1", "5400.00", "4800.00")
    await _make_offer(db, divizion, copy_product, "sku-2", "5600.00", None)
    await _make_offer(db, tgsm, orig_product, "sku-3", "12000.00", None)
    await _make_offer(db, divizion, other_product, "sku-4", "7000.00", None)

    refs["copy_product"] = copy_product
    refs["orig_product"] = orig_product
    refs["other_product"] = other_product
    return refs


async def test_catalog_export_requires_authentication(client):
    resp = await client.get(CATALOG_URL)

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.parametrize("url", [CATALOG_URL, TRACKING_URL, CATALOG_PDF_URL])
async def test_export_forbidden_without_subscription(client, db_session, url):
    slug = url.rsplit("/", 1)[-1]
    _, token = await _make_user(db_session, f"nosub-{slug}@example.com", plan=None)

    resp = await client.get(url, headers=_auth(token))

    assert resp.status_code == 403, resp.text
    detail = resp.json()["detail"]
    assert detail["code"] == "subscription_required"
    assert detail["message"].strip()


@pytest.mark.parametrize("plan", [PlanEnum.trial, PlanEnum.basic])
@pytest.mark.parametrize("url", [CATALOG_URL, TRACKING_URL, CATALOG_PDF_URL])
async def test_export_forbidden_for_plans_without_the_feature(client, db_session, plan, url):
    slug = url.rsplit("/", 1)[-1]
    _, token = await _make_user(db_session, f"{plan.value}-{slug}@example.com", plan=plan)

    resp = await client.get(url, headers=_auth(token))

    assert resp.status_code == 403, resp.text
    detail = resp.json()["detail"]
    assert detail["code"] == "feature_unavailable"
    assert detail["feature"] == "export_reports"
    assert detail["requiredPlans"] == ["advanced"]
    assert "Продвинутый" in detail["message"]


async def test_catalog_export_returns_excel_friendly_csv(client, db_session):
    await _seed_catalog(db_session)
    _, token = await _make_user(db_session, "adv-catalog@example.com")

    resp = await client.get(CATALOG_URL, headers=_auth(token))

    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/csv")

    body = resp.content
    assert body.startswith(b"\xef\xbb\xbf")

    rows = _parse_csv(body)
    assert rows[0] == CATALOG_HEADER
    assert len(rows) == 4

    by_name = {row[0]: row for row in rows[1:]}
    copy_row = by_name["Дисплей iPhone 13 копия"]
    assert copy_row[1] == "Apple"
    assert copy_row[2] == "iPhone 13"
    assert copy_row[3] == "Дисплей"
    assert copy_row[4] == "Копия"
    assert copy_row[5] == "5400,00"
    assert copy_row[6] == "4800,00"
    assert copy_row[7] == "2"
    assert copy_row[8] == "2"
    assert copy_row[9] == "Дивизион, ТГСМ"


async def test_catalog_export_uses_semicolon_so_excel_splits_columns(client, db_session):
    await _seed_catalog(db_session)
    _, token = await _make_user(db_session, "adv-delimiter@example.com")

    resp = await client.get(CATALOG_URL, headers=_auth(token))
    text = resp.content.decode("utf-8")

    lines = text[1:].split("\r\n")
    assert lines[0] == CSV_DELIMITER.join(CATALOG_HEADER)
    assert all(line.count(CSV_DELIMITER) == len(CATALOG_HEADER) - 1 for line in lines if line)


async def test_catalog_export_escapes_formula_injection(client, db_session):
    refs = await _make_refs(db_session)
    store = await _make_store(db_session, "tgsm", "ТГСМ")
    product = await _make_product(db_session, refs, refs["tier_copy"], "inj", "=cmd|' /C calc'!A0")
    await _make_offer(db_session, store, product, "sku-inj", "100.00", None)
    _, token = await _make_user(db_session, "adv-injection@example.com")

    resp = await client.get(CATALOG_URL, headers=_auth(token))

    assert resp.status_code == 200, resp.text
    rows = _parse_csv(resp.content)
    assert rows[1][0] == "'=cmd|' /C calc'!A0"
    assert not rows[1][0].startswith("=")


async def test_catalog_export_sets_a_meaningful_filename(client, db_session):
    _, token = await _make_user(db_session, "adv-filename@example.com")

    resp = await client.get(CATALOG_URL, headers=_auth(token))

    disposition = resp.headers["content-disposition"]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert disposition == f'attachment; filename="bscout-catalog-{stamp}.csv"'


async def test_tracking_export_sets_a_meaningful_filename(client, db_session):
    _, token = await _make_user(db_session, "adv-trackfilename@example.com")

    resp = await client.get(TRACKING_URL, headers=_auth(token))

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert (
        resp.headers["content-disposition"] == f'attachment; filename="bscout-tracking-{stamp}.csv"'
    )


async def test_catalog_export_honours_the_row_limit(client, db_session):
    await _seed_catalog(db_session)
    _, token = await _make_user(db_session, "adv-limit@example.com")

    too_small = await client.get(CATALOG_URL, params={"limit": 2}, headers=_auth(token))

    assert too_small.status_code == 413, too_small.text
    detail = too_small.json()["detail"]
    assert detail["code"] == "export_limit_exceeded"
    assert detail["limit"] == 2
    assert detail["total"] == 3
    assert "Уточните фильтры" in detail["message"]

    exact = await client.get(CATALOG_URL, params={"limit": 3}, headers=_auth(token))

    assert exact.status_code == 200, exact.text
    assert len(_parse_csv(exact.content)) == 4


async def test_catalog_export_rejects_a_limit_above_the_hard_cap(client, db_session):
    _, token = await _make_user(db_session, "adv-hardcap@example.com")

    resp = await client.get(CATALOG_URL, params={"limit": 10_001}, headers=_auth(token))

    assert resp.status_code == 422, resp.text


async def test_catalog_export_applies_the_same_filters_as_the_catalog(client, db_session):
    refs = await _seed_catalog(db_session)
    _, token = await _make_user(db_session, "adv-filters@example.com")

    by_quality = await client.get(
        CATALOG_URL,
        params={"quality_tier_id": refs["tier_orig"].id},
        headers=_auth(token),
    )
    quality_rows = _parse_csv(by_quality.content)
    assert [row[0] for row in quality_rows[1:]] == ["Дисплей iPhone 13 оригинал"]

    by_device = await client.get(
        CATALOG_URL, params={"device_id": refs["other_device"].id}, headers=_auth(token)
    )
    device_rows = _parse_csv(by_device.content)
    assert [row[0] for row in device_rows[1:]] == ["Дисплей iPhone 14 копия"]

    by_query = await client.get(CATALOG_URL, params={"q": "оригинал"}, headers=_auth(token))
    query_rows = _parse_csv(by_query.content)
    assert [row[0] for row in query_rows[1:]] == ["Дисплей iPhone 13 оригинал"]

    by_part_type = await client.get(
        CATALOG_URL, params={"part_type_id": refs["part_type"].id}, headers=_auth(token)
    )
    assert len(_parse_csv(by_part_type.content)) == 4


async def test_catalog_export_streams_in_chunks(client, db_session):
    await _seed_catalog(db_session)
    _, token = await _make_user(db_session, "adv-stream@example.com")

    async with client.stream("GET", CATALOG_URL, headers=_auth(token)) as resp:
        assert resp.status_code == 200
        assert "content-length" not in resp.headers
        chunks = [chunk async for chunk in resp.aiter_bytes()]

    assert chunks
    assert b"".join(chunks).startswith(b"\xef\xbb\xbf")


async def test_tracking_export_reports_prices_target_and_delta(client, db_session):
    refs = await _seed_catalog(db_session)
    user, token = await _make_user(db_session, "adv-tracking@example.com")

    db_session.add(
        TrackedProduct(
            user_id=user.id,
            product_id=refs["copy_product"].id,
            target_price=Decimal("5000.00"),
            initial_price=Decimal("6000.00"),
            last_seen_price=Decimal("6000.00"),
            notify_on_any_drop=True,
            is_active=True,
        )
    )
    await db_session.flush()

    resp = await client.get(TRACKING_URL, headers=_auth(token))

    assert resp.status_code == 200, resp.text
    rows = _parse_csv(resp.content)
    assert rows[0] == TRACKING_HEADER
    assert len(rows) == 2

    row = rows[1]
    assert row[0] == "Дисплей iPhone 13 копия"
    assert row[1] == "5400,00"
    assert row[2] == "5000,00"
    assert row[3] == "-600,00"
    assert row[5] == "2"
    assert row[6] == "нет"
    assert row[7] == "да"


async def test_tracking_export_only_returns_rows_of_the_current_user(client, db_session):
    refs = await _seed_catalog(db_session)
    owner, _ = await _make_user(db_session, "adv-owner@example.com")
    _, other_token = await _make_user(db_session, "adv-other@example.com")

    db_session.add(
        TrackedProduct(
            user_id=owner.id,
            product_id=refs["copy_product"].id,
            initial_price=Decimal("6000.00"),
            last_seen_price=Decimal("6000.00"),
            is_active=True,
        )
    )
    await db_session.flush()

    resp = await client.get(TRACKING_URL, headers=_auth(other_token))

    assert resp.status_code == 200, resp.text
    assert len(_parse_csv(resp.content)) == 1


async def test_tracking_export_honours_the_row_limit(client, db_session):
    refs = await _seed_catalog(db_session)
    user, token = await _make_user(db_session, "adv-tracklimit@example.com")

    for product in (refs["copy_product"], refs["orig_product"]):
        db_session.add(
            TrackedProduct(
                user_id=user.id,
                product_id=product.id,
                initial_price=Decimal("6000.00"),
                last_seen_price=Decimal("6000.00"),
                is_active=True,
            )
        )
    await db_session.flush()

    resp = await client.get(TRACKING_URL, params={"limit": 1}, headers=_auth(token))

    assert resp.status_code == 413, resp.text
    assert resp.json()["detail"]["code"] == "export_limit_exceeded"
    assert resp.json()["detail"]["total"] == 2


async def test_pdf_export_returns_503_when_reportlab_is_missing(client, db_session, monkeypatch):
    _, token = await _make_user(db_session, "adv-pdf-missing@example.com")
    monkeypatch.setattr(pdf_module, "is_reportlab_available", lambda: False)

    resp = await client.get(CATALOG_PDF_URL, headers=_auth(token))

    assert resp.status_code == 503, resp.text
    detail = resp.json()["detail"]
    assert detail["code"] == "export_pdf_unavailable"
    assert "reportlab" in detail["message"]
    assert "CSV" in detail["message"]


async def test_pdf_export_returns_503_when_the_cyrillic_font_is_missing(
    client, db_session, monkeypatch
):
    _, token = await _make_user(db_session, "adv-pdf-font@example.com")
    monkeypatch.setattr(pdf_module, "is_reportlab_available", lambda: True)
    monkeypatch.setattr(pdf_module, "find_cyrillic_font", lambda: None)

    resp = await client.get(CATALOG_PDF_URL, headers=_auth(token))

    assert resp.status_code == 503, resp.text
    assert resp.json()["detail"]["code"] == "export_pdf_unavailable"
    assert "DejaVuSans" in resp.json()["detail"]["message"]


async def test_pdf_export_renders_when_the_toolchain_is_present(client, db_session, monkeypatch):
    pytest.importorskip("reportlab")

    font = pdf_module.find_cyrillic_font() or FALLBACK_CYRILLIC_FONT
    if not Path(font).is_file():
        pytest.skip("no Cyrillic TTF available on this host")

    await _seed_catalog(db_session)
    _, token = await _make_user(db_session, "adv-pdf-ok@example.com")
    monkeypatch.setattr(pdf_module, "find_cyrillic_font", lambda: font)

    resp = await client.get(CATALOG_PDF_URL, headers=_auth(token))

    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert (
        resp.headers["content-disposition"] == f'attachment; filename="bscout-catalog-{stamp}.pdf"'
    )
