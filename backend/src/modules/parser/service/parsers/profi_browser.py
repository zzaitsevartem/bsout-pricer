import asyncio
import re

from src.modules.parser.service.exceptions import ParserAuthError, ParserConnectionError


class ProfiBrowserSession:
    def __init__(self, base_url: str, city: str):
        self.base_url = base_url
        self.city = city
        self._playwright = None
        self._browser = None
        self._context = None
        self._lock = asyncio.Lock()
        self._generation = 0
        self._blocked_error = None

    async def __aenter__(self):
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        try:
            self._browser = await self._playwright.chromium.launch(
                channel="chromium", headless=True
            )
            self._context = await self._browser.new_context()
            await self._bootstrap()
        except Exception:
            await self.__aexit__(None, None, None)
            raise
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if self._browser is not None:
                await self._browser.close()
        finally:
            if self._playwright is not None:
                await self._playwright.stop()

    async def _bootstrap(self):
        for attempt in range(3):
            try:
                await self._bootstrap_once()
                return
            except Exception as exc:
                if attempt < 2 and "net::ERR_" in str(exc):
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                self._blocked_error = f"Profi browser verification or city selection failed: {exc}"
                raise ParserAuthError(self._blocked_error) from exc

    async def _bootstrap_once(self):
        page = await self._context.new_page()
        try:
            await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
            label = page.locator(".cp-city-selector__city").first
            await label.wait_for(state="attached", timeout=45000)
            if self.city and (await label.inner_text()).strip() != self.city:
                change = page.get_by_text("Выбрать другой", exact=True)
                if await change.is_visible():
                    await change.click()
                else:
                    await page.locator(".cp-city-selector__opener").first.click()
                await page.get_by_role(
                    "link", name=re.compile(rf"^{re.escape(self.city)}(?:\s|$)")
                ).first.click(timeout=30000)
                await page.wait_for_function(
                    "city => document.querySelector('.cp-city-selector__city')"
                    "?.textContent.trim() === city",
                    arg=self.city,
                    timeout=30000,
                )
            self._generation += 1
        finally:
            await page.close()

    async def fetch(self, url: str) -> str:
        if self._blocked_error:
            raise ParserAuthError(self._blocked_error)
        last_error = ""
        for attempt in range(3):
            generation = self._generation
            try:
                response = await self._context.request.get(url, timeout=30000)
                markup = await response.text()
                if response.ok:
                    return markup
                if response.status in (401, 403, 429):
                    self._blocked_error = f"Profi access denied: HTTP {response.status} at {url}"
                    raise ParserAuthError(self._blocked_error)
                if response.status == 503 and "Проверка безопасности" in markup:
                    if attempt == 2:
                        self._blocked_error = f"Profi browser verification persists at {url}"
                        raise ParserAuthError(self._blocked_error)
                    async with self._lock:
                        if generation == self._generation:
                            await self._bootstrap()
                    continue
                last_error = f"HTTP {response.status}"
                if 400 <= response.status < 500:
                    break
            except ParserAuthError:
                raise
            except Exception as exc:
                last_error = str(exc)
            if attempt < 2:
                await asyncio.sleep(0.5 * (2**attempt))
        raise ParserConnectionError(f"Profi request failed: {url} ({last_error})")
