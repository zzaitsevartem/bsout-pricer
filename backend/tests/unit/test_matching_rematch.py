from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.modules.catalog.service.extractor import ExtractedAttrs
from src.modules.products.service.matching_service import MatchingService

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("status,expected_id", [("auto", None), ("manual", 99), ("rejected", 99)])
async def test_rematch_removes_invalid_auto_link_but_preserves_moderation(
    monkeypatch, status, expected_id
):
    attrs = ExtractedAttrs(None, None, None, None, None, 0.0, {})
    monkeypatch.setattr("src.modules.products.service.matching_service.extract", lambda *_: attrs)
    offer = SimpleNamespace(
        id=1, title="Unknown part", product_id=99, match_status=status, match_confidence=0.85
    )

    await MatchingService.match_offer(AsyncMock(), offer, None)

    assert offer.product_id == expected_id
    assert offer.match_status == ("unmatched" if status == "auto" else status)
