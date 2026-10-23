from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.modules.parser.service.exceptions import ParserAuthError, ParserConnectionError
from src.modules.parser.service.parsers.profi_browser import ProfiBrowserSession

pytestmark = pytest.mark.unit


async def test_bootstrap_retries_transient_network_error(monkeypatch):
    session = ProfiBrowserSession("https://siriust.ru", "Ставрополь")
    bootstrap = AsyncMock(side_effect=[RuntimeError("net::ERR_CERT_VERIFIER_CHANGED"), None])
    monkeypatch.setattr(session, "_bootstrap_once", bootstrap)

    await session._bootstrap()

    assert bootstrap.await_count == 2
    assert session._blocked_error is None


def response(status, markup):
    return SimpleNamespace(status=status, ok=status == 200, text=AsyncMock(return_value=markup))


@pytest.mark.parametrize("status,exception", [(403, ParserAuthError), (404, ParserConnectionError)])
async def test_browser_does_not_retry_denied_or_missing_pages(status, exception):
    session = ProfiBrowserSession("https://siriust.ru", "Ставрополь")
    get = AsyncMock(return_value=response(status, "unavailable"))
    session._context = SimpleNamespace(request=SimpleNamespace(get=get))

    with pytest.raises(exception):
        await session.fetch("https://siriust.ru/product/")

    assert get.await_count == 1
    if status == 403:
        with pytest.raises(ParserAuthError):
            await session.fetch("https://siriust.ru/another/")
        assert get.await_count == 1


async def test_browser_refreshes_verification_once_and_keeps_xml(monkeypatch):
    session = ProfiBrowserSession("https://siriust.ru", "Ставрополь")
    get = AsyncMock(
        side_effect=[
            response(503, "<title>Проверка безопасности...</title>"),
            response(200, "<urlset><url><loc>https://siriust.ru/product/</loc></url></urlset>"),
        ]
    )
    session._context = SimpleNamespace(request=SimpleNamespace(get=get))

    async def bootstrap():
        session._generation += 1

    refresh = AsyncMock(side_effect=bootstrap)
    monkeypatch.setattr(session, "_bootstrap", refresh)

    markup = await session.fetch("https://siriust.ru/sitemap.xml")

    assert markup.startswith("<urlset>")
    refresh.assert_awaited_once()
    assert get.await_count == 2
