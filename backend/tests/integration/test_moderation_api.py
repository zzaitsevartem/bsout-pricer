from decimal import Decimal

import pytest
from sqlalchemy import select

from src.modules.auth.model.user import User
from src.modules.auth.service.auth import create_access_token, hash_password
from src.modules.products.model.product import MatchCandidate, Product, StoreOffer
from src.modules.stores.model.store import Store

pytestmark = pytest.mark.integration

QUEUE_URL = "/api/admin/match-candidates"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _make_store(db, slug: str = "tgsm", name: str = "ТГСМ") -> Store:
    store = Store(name=name, slug=slug, website_url="https://taggsm.ru", is_active=True)
    db.add(store)
    await db.flush()
    return store


async def _make_user(db, email: str, *, is_admin: bool) -> User:
    user = User(
        email=email,
        password_hash=hash_password("s3cret-pass"),
        full_name="Moderation User",
        is_active=True,
        is_admin=is_admin,
    )
    db.add(user)
    await db.flush()
    return user


async def _admin(db, email: str = "moderation-admin@example.com") -> User:
    return await _make_user(db, email, is_admin=True)


async def _admin_headers(db, email: str = "moderation-admin@example.com") -> dict[str, str]:
    admin = await _admin(db, email)
    return _auth(create_access_token(admin.id))


async def _make_offer(
    db,
    store: Store,
    *,
    sku: str = "TG-1",
    title: str = "Дисплей iPhone 13 (оригинал)",
    price: str = "4500.00",
    match_status: str = "unmatched",
    product_id: int | None = None,
) -> StoreOffer:
    offer = StoreOffer(
        store_id=store.id,
        source_sku=sku,
        title=title,
        normalized_title=title.lower(),
        price_retail=Decimal(price),
        price_opt=Decimal("3900.00"),
        currency="RUB",
        stock_status="in_stock",
        url=f"https://taggsm.ru/p/{sku}",
        is_active=True,
        match_status=match_status,
        product_id=product_id,
    )
    db.add(offer)
    await db.flush()
    return offer


async def _make_product(db, key: str, name: str) -> Product:
    product = Product(canonical_key=key, canonical_name=name)
    db.add(product)
    await db.flush()
    return product


async def _make_candidate(
    db,
    offer: StoreOffer,
    product: Product,
    *,
    score: str = "0.7000",
    status: str = "pending",
    features: dict | None = None,
) -> MatchCandidate:
    candidate = MatchCandidate(
        offer_id=offer.id,
        product_id=product.id,
        score=Decimal(score),
        features=features if features is not None else {"device": 1.0, "part_type": 1.0},
        status=status,
    )
    db.add(candidate)
    await db.flush()
    return candidate


async def _candidate_by_id(db, candidate_id: int) -> MatchCandidate:
    return (
        await db.execute(select(MatchCandidate).where(MatchCandidate.id == candidate_id))
    ).scalar_one()


async def test_queue_returns_pending_sorted_by_score_with_full_context(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer = await _make_offer(db_session, store)
    weak = await _make_product(db_session, "iphone13|display|copy|-", "Дисплей iPhone 13 (копия)")
    strong = await _make_product(
        db_session, "iphone13|display|orig|-", "Дисплей iPhone 13 (оригинал)"
    )
    await _make_candidate(db_session, offer, weak, score="0.5500")
    await _make_candidate(
        db_session, offer, strong, score="0.7900", features={"device": 1.0, "tier": 0.6}
    )

    resp = await client.get(QUEUE_URL, headers=headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["per_page"] == 20
    assert [item["score"] for item in body["results"]] == ["0.7900", "0.5500"]

    top = body["results"][0]
    assert top["status"] == "pending"
    assert top["product_id"] == strong.id
    assert top["features"] == {"device": 1.0, "tier": 0.6}
    assert top["decided_by"] is None
    assert top["decided_at"] is None
    assert top["offer"]["id"] == offer.id
    assert top["offer"]["title"] == "Дисплей iPhone 13 (оригинал)"
    assert top["offer"]["price_retail"] == "4500.00"
    assert top["offer"]["price_opt"] == "3900.00"
    assert top["offer"]["match_status"] == "unmatched"
    assert top["offer"]["store"] == {"id": store.id, "name": "ТГСМ", "slug": "tgsm"}
    assert top["product"]["canonical_name"] == "Дисплей iPhone 13 (оригинал)"
    assert top["product"]["canonical_key"] == "iphone13|display|orig|-"


async def test_queue_hides_decided_candidates_by_default(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer = await _make_offer(db_session, store)
    product_a = await _make_product(db_session, "key-a", "Товар A")
    product_b = await _make_product(db_session, "key-b", "Товар B")
    await _make_candidate(db_session, offer, product_a, status="approved")
    pending = await _make_candidate(db_session, offer, product_b, status="pending")

    resp = await client.get(QUEUE_URL, headers=headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert [item["id"] for item in body["results"]] == [pending.id]


async def test_queue_filters_by_status_offer_and_product(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer_one = await _make_offer(db_session, store, sku="TG-1")
    offer_two = await _make_offer(db_session, store, sku="TG-2", title="Аккумулятор iPhone 12")
    product_a = await _make_product(db_session, "key-a", "Товар A")
    product_b = await _make_product(db_session, "key-b", "Товар B")
    first = await _make_candidate(db_session, offer_one, product_a, score="0.6000")
    second = await _make_candidate(db_session, offer_two, product_a, score="0.8000")
    third = await _make_candidate(
        db_session, offer_two, product_b, score="0.9000", status="rejected"
    )

    by_offer = await client.get(QUEUE_URL, params={"offer_id": offer_one.id}, headers=headers)
    by_product = await client.get(QUEUE_URL, params={"product_id": product_a.id}, headers=headers)
    rejected = await client.get(QUEUE_URL, params={"status": "rejected"}, headers=headers)
    everything = await client.get(QUEUE_URL, params={"status": "all"}, headers=headers)

    assert [item["id"] for item in by_offer.json()["results"]] == [first.id]
    assert [item["id"] for item in by_product.json()["results"]] == [second.id, first.id]
    assert [item["id"] for item in rejected.json()["results"]] == [third.id]
    assert everything.json()["total"] == 3


async def test_queue_paginates(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer = await _make_offer(db_session, store)
    candidates = []
    for index, score in enumerate(["0.9000", "0.8000", "0.7000"]):
        product = await _make_product(db_session, f"key-{index}", f"Товар {index}")
        candidates.append(await _make_candidate(db_session, offer, product, score=score))

    page_one = await client.get(QUEUE_URL, params={"per_page": 2}, headers=headers)
    page_two = await client.get(QUEUE_URL, params={"per_page": 2, "page": 2}, headers=headers)

    assert page_one.json()["total"] == 3
    assert [item["id"] for item in page_one.json()["results"]] == [
        candidates[0].id,
        candidates[1].id,
    ]
    assert page_two.json()["page"] == 2
    assert [item["id"] for item in page_two.json()["results"]] == [candidates[2].id]


async def test_queue_rejects_unknown_status_filter(client, db_session):
    headers = await _admin_headers(db_session)

    resp = await client.get(QUEUE_URL, params={"status": "whatever"}, headers=headers)

    assert resp.status_code == 422


async def test_approve_links_offer_and_closes_competitors(client, db_session):
    store = await _make_store(db_session)
    admin = await _admin(db_session)
    headers = _auth(create_access_token(admin.id))
    offer = await _make_offer(db_session, store)
    winner = await _make_product(db_session, "key-win", "Дисплей iPhone 13 (оригинал)")
    loser = await _make_product(db_session, "key-lose", "Дисплей iPhone 13 (копия)")
    other_offer = await _make_offer(db_session, store, sku="TG-9", title="Другой оффер")
    chosen = await _make_candidate(db_session, offer, winner, score="0.7600")
    rival = await _make_candidate(db_session, offer, loser, score="0.5100")
    untouched = await _make_candidate(db_session, other_offer, loser, score="0.6000")

    resp = await client.post(f"{QUEUE_URL}/{chosen.id}/approve", headers=headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["candidate"]["status"] == "approved"
    assert body["candidate"]["decided_by"] == admin.id
    assert body["candidate"]["decided_at"] is not None
    assert body["offer"] == {
        "id": offer.id,
        "product_id": winner.id,
        "match_status": "manual",
        "match_confidence": "0.7600",
    }
    assert body["rejected_candidate_ids"] == [rival.id]

    assert offer.product_id == winner.id
    assert offer.match_status == "manual"
    assert offer.match_confidence == Decimal("0.7600")
    assert (await _candidate_by_id(db_session, chosen.id)).status == "approved"

    closed = await _candidate_by_id(db_session, rival.id)
    assert closed.status == "rejected"
    assert closed.decided_by == admin.id
    assert closed.decided_at is not None

    assert (await _candidate_by_id(db_session, untouched.id)).status == "pending"
    assert other_offer.match_status == "unmatched"


async def test_reject_marks_candidate_and_leaves_offer_untouched(client, db_session):
    store = await _make_store(db_session)
    admin = await _admin(db_session)
    headers = _auth(create_access_token(admin.id))
    offer = await _make_offer(db_session, store)
    product = await _make_product(db_session, "key-a", "Товар A")
    other = await _make_product(db_session, "key-b", "Товар B")
    candidate = await _make_candidate(db_session, offer, product, score="0.6100")
    sibling = await _make_candidate(db_session, offer, other, score="0.5200")

    resp = await client.post(f"{QUEUE_URL}/{candidate.id}/reject", headers=headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["candidate"]["status"] == "rejected"
    assert body["candidate"]["decided_by"] == admin.id
    assert body["rejected_candidate_ids"] == []
    assert body["offer"] == {
        "id": offer.id,
        "product_id": None,
        "match_status": "unmatched",
        "match_confidence": None,
    }

    assert offer.product_id is None
    assert offer.match_status == "unmatched"
    assert (await _candidate_by_id(db_session, sibling.id)).status == "pending"


@pytest.mark.parametrize("decision", ["approve", "reject"])
async def test_second_decision_on_same_candidate_returns_409(client, db_session, decision):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer = await _make_offer(db_session, store)
    product = await _make_product(db_session, "key-a", "Товар A")
    candidate = await _make_candidate(db_session, offer, product)

    first = await client.post(f"{QUEUE_URL}/{candidate.id}/{decision}", headers=headers)
    second = await client.post(f"{QUEUE_URL}/{candidate.id}/approve", headers=headers)
    third = await client.post(f"{QUEUE_URL}/{candidate.id}/reject", headers=headers)

    assert first.status_code == 200, first.text
    assert second.status_code == 409
    assert third.status_code == 409
    assert "already" in second.json()["detail"]


async def test_approve_rejected_competitor_returns_409(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer = await _make_offer(db_session, store)
    winner = await _make_product(db_session, "key-win", "Товар win")
    loser = await _make_product(db_session, "key-lose", "Товар lose")
    chosen = await _make_candidate(db_session, offer, winner, score="0.8100")
    rival = await _make_candidate(db_session, offer, loser, score="0.5300")

    await client.post(f"{QUEUE_URL}/{chosen.id}/approve", headers=headers)
    resp = await client.post(f"{QUEUE_URL}/{rival.id}/approve", headers=headers)

    assert resp.status_code == 409
    assert offer.product_id == winner.id


@pytest.mark.parametrize("decision", ["approve", "reject"])
async def test_unknown_candidate_returns_404(client, db_session, decision):
    headers = await _admin_headers(db_session)

    resp = await client.post(f"{QUEUE_URL}/424242/{decision}", headers=headers)

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Match candidate not found"


async def test_link_offer_to_product_manually(client, db_session):
    store = await _make_store(db_session)
    admin = await _admin(db_session)
    headers = _auth(create_access_token(admin.id))
    offer = await _make_offer(db_session, store)
    product = await _make_product(db_session, "key-a", "Товар A")
    other = await _make_product(db_session, "key-b", "Товар B")
    pending = await _make_candidate(db_session, offer, other, score="0.6000")

    resp = await client.post(
        f"/api/admin/offers/{offer.id}/link", json={"product_id": product.id}, headers=headers
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["offer"] == {
        "id": offer.id,
        "product_id": product.id,
        "match_status": "manual",
        "match_confidence": "1.0000",
    }
    assert body["rejected_candidate_ids"] == [pending.id]

    assert offer.product_id == product.id
    assert offer.match_status == "manual"
    assert (await _candidate_by_id(db_session, pending.id)).status == "rejected"


async def test_unlink_offer_marks_it_rejected(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    product = await _make_product(db_session, "key-a", "Товар A")
    offer = await _make_offer(db_session, store, match_status="auto", product_id=product.id)
    offer.match_confidence = Decimal("0.9100")
    await db_session.flush()

    resp = await client.post(f"/api/admin/offers/{offer.id}/unlink", headers=headers)

    assert resp.status_code == 200, resp.text
    assert resp.json()["offer"] == {
        "id": offer.id,
        "product_id": None,
        "match_status": "rejected",
        "match_confidence": None,
    }

    assert offer.product_id is None
    assert offer.match_status == "rejected"
    assert offer.match_confidence is None


async def test_link_with_unknown_product_returns_404(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer = await _make_offer(db_session, store)

    resp = await client.post(
        f"/api/admin/offers/{offer.id}/link", json={"product_id": 999999}, headers=headers
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Product not found"
    assert offer.product_id is None
    assert offer.match_status == "unmatched"


async def test_link_and_unlink_unknown_offer_return_404(client, db_session):
    headers = await _admin_headers(db_session)
    product = await _make_product(db_session, "key-a", "Товар A")

    link = await client.post(
        "/api/admin/offers/777777/link", json={"product_id": product.id}, headers=headers
    )
    unlink = await client.post("/api/admin/offers/777777/unlink", headers=headers)

    assert link.status_code == 404
    assert link.json()["detail"] == "Offer not found"
    assert unlink.status_code == 404
    assert unlink.json()["detail"] == "Offer not found"


async def test_regular_user_is_forbidden_everywhere(client, db_session):
    store = await _make_store(db_session)
    user = await _make_user(db_session, "plain@example.com", is_admin=False)
    headers = _auth(create_access_token(user.id))
    offer = await _make_offer(db_session, store)
    product = await _make_product(db_session, "key-a", "Товар A")
    candidate = await _make_candidate(db_session, offer, product)

    responses = [
        await client.get(QUEUE_URL, headers=headers),
        await client.post(f"{QUEUE_URL}/{candidate.id}/approve", headers=headers),
        await client.post(f"{QUEUE_URL}/{candidate.id}/reject", headers=headers),
        await client.post(
            f"/api/admin/offers/{offer.id}/link", json={"product_id": product.id}, headers=headers
        ),
        await client.post(f"/api/admin/offers/{offer.id}/unlink", headers=headers),
    ]

    assert [resp.status_code for resp in responses] == [403, 403, 403, 403, 403]
    assert all(resp.json()["detail"] == "Admin access required" for resp in responses)
    assert (await _candidate_by_id(db_session, candidate.id)).status == "pending"
    assert offer.product_id is None
    assert offer.match_status == "unmatched"


async def test_anonymous_requests_are_rejected(client, db_session):
    store = await _make_store(db_session)
    offer = await _make_offer(db_session, store)

    queue = await client.get(QUEUE_URL)
    unlink = await client.post(f"/api/admin/offers/{offer.id}/unlink")

    assert queue.status_code == 403
    assert unlink.status_code == 403
    assert offer.match_status == "unmatched"
