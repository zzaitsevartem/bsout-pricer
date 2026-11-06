import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import select
from src import db_metadata
from src.database import async_session_factory
from src.modules.catalog.model.catalog import Device, DeviceAlias
from src.modules.catalog.service.dictionaries import load_dictionaries
from src.modules.catalog.service.extractor import extract
from src.modules.products.model.product import Cluster, Product, StoreOffer
from src.modules.products.service.matching_service import MatchingService

BACKUP = Path('/tmp/hot30-before.json')
PLAY_IDS = {4726, 20873, 34133, 37918, 58605, 58929, 59511, 59940, 79419,
            84399, 85249, 85250, 86201, 86310, 86311, 86312, 88429, 91898}

async def main():
    async with async_session_factory() as db:
        offers = (await db.execute(select(StoreOffer).where(
            StoreOffer.title.op('~*')('hot[ ]*30')
        ).order_by(StoreOffer.id).with_for_update())).scalars().all()
        snapshot = {str(o.id): {
            'title': o.title, 'store_id': o.store_id, 'source_sku': o.source_sku,
            'price_retail': str(o.price_retail), 'price_opt': str(o.price_opt),
            'url': o.url, 'product_id': o.product_id, 'match_status': o.match_status,
            'match_confidence': str(o.match_confidence), 'is_active': o.is_active,
        } for o in offers}
        if '--verify' in sys.argv:
            before = json.loads(BACKUP.read_text())
            assert set(before) == set(snapshot)
            for key, value in before.items():
                for field in ('title', 'store_id', 'source_sku', 'price_retail', 'price_opt', 'url', 'is_active'):
                    assert snapshot[key][field] == value[field], (key, field)
                if int(key) not in PLAY_IDS:
                    assert snapshot[key] == value, key
            dicts = await load_dictionaries(db)
            play = [o for o in offers if o.id in PLAY_IDS]
            assert {o.id for o in play} == PLAY_IDS
            for offer in play:
                if offer.id == 20873:
                    assert offer.product_id is None and offer.match_status == 'review'
                if offer.product_id is None:
                    assert offer.match_status in ('review', 'candidate'), offer.id
                    attrs = extract(offer.title, dicts)
                    assert dicts.device_model_key[attrs.device_id] == 'infinix-hot-30-play'
                    continue
                product = await db.get(Product, offer.product_id)
                cluster = await db.get(Cluster, product.cluster_id)
                assert dicts.device_model_key[cluster.device_id] == 'infinix-hot-30-play', offer.id
                assert product.canonical_key.startswith('infinix-hot-30-play|')
            for title, key in [('Hot 30', 'infinix-hot-30'), ('Hot 30 Play', 'infinix-hot-30-play'), ('Hot 30i', 'infinix-hot-30i')]:
                attrs = extract('Дисплей Infinix ' + title, dicts)
                assert dicts.device_model_key[attrs.device_id] == key
            print(f'HOT30_LIVE_VERIFIED offers={len(offers)} play={len(play)}')
            return
        dry_run = '--dry-run' in sys.argv
        if not dry_run:
            if BACKUP.exists():
                assert json.loads(BACKUP.read_text()) == snapshot, 'Live data differs from backup'
            else:
                BACKUP.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))
        base = (await db.execute(select(Device).where(Device.model_key == 'infinix-hot-30'))).scalar_one()
        play = (await db.execute(select(Device).where(Device.model_key == 'infinix-hot-30-play'))).scalar_one_or_none()
        if play is None:
            play = Device(brand_id=base.brand_id, name='Hot 30 Play', model_key='infinix-hot-30-play')
            db.add(play)
            await db.flush()
        for alias in ('hot 30 play', 'infinix hot 30 play'):
            existing = (await db.execute(select(DeviceAlias).where(DeviceAlias.alias == alias))).scalar_one_or_none()
            if existing is None:
                db.add(DeviceAlias(device_id=play.id, alias=alias, source='seed'))
            else:
                assert existing.device_id == play.id
        await db.flush()
        dicts = await load_dictionaries(db)
        touched = set()
        changed = []
        assert PLAY_IDS <= {o.id for o in offers}
        for offer in offers:
            if offer.id not in PLAY_IDS:
                continue
            assert 'play' in offer.title.lower(), offer.id
            assert offer.match_status not in ('manual', 'rejected'), offer.id
            if offer.product_id:
                touched.add((await db.get(Product, offer.product_id)).cluster_id)
            outcome = await MatchingService.match_offer(db, offer, dicts)
            if outcome.product_id is not None:
                product = await db.get(Product, outcome.product_id)
                assert product.canonical_key.startswith('infinix-hot-30-play|'), offer.id
                touched.add(product.cluster_id)
            else:
                assert outcome.status in ('review', 'candidate'), outcome
                attrs = extract(offer.title, dicts)
                assert dicts.device_model_key[attrs.device_id] == 'infinix-hot-30-play'
            changed.append((offer.id, outcome.status, outcome.confidence))
        assert changed
        await MatchingService.recalc_cluster_aggregates(db, sorted(touched))
        if dry_run:
            await db.rollback()
            print(f'HOT30_DRY_RUN offers={len(changed)} outcomes={changed}')
        else:
            await db.commit()
            print(f'HOT30_REPAIRED offers={len(changed)} outcomes={changed}')

asyncio.run(main())
