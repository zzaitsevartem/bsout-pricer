import asyncio
import re
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher

import httpx

from src.modules.parser.service.exceptions import ParserConnectionError, ParserParseError

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_PRICE_KEEP_RE = re.compile(r"[^\d,.\-]")


def normalize_name(text: str | None) -> str:
    if not text:
        return ""
    lowered = text.lower().strip()
    no_punct = _PUNCT_RE.sub(" ", lowered)
    return _WS_RE.sub(" ", no_punct).strip()


def parse_price(text: str | None) -> Decimal:
    if text is None:
        raise ParserParseError("price is None")

    cleaned = _PRICE_KEEP_RE.sub("", str(text).replace("\xa0", " "))
    if not cleaned or cleaned in {"-", ".", ","}:
        raise ParserParseError(f"no digits in price: {text!r}")

    cleaned = cleaned.replace(",", ".")
    if cleaned.count(".") > 1:
        parts = cleaned.split(".")
        cleaned = "".join(parts[:-1]) + "." + parts[-1]

    try:
        value = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ParserParseError(f"cannot parse price: {text!r}") from exc

    if value < 0:
        raise ParserParseError(f"negative price: {text!r}")
    return value


def compare_products(a: str, b: str) -> float:
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


async def safe_request(
    client: httpx.AsyncClient,
    url: str,
    *,
    method: str = "GET",
    retries: int = 3,
    backoff: float = 0.5,
    timeout: float = 15.0,
    **kwargs,
) -> httpx.Response:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            response = await client.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as exc:
            last_exc = exc
            if attempt < retries - 1:
                await asyncio.sleep(backoff * (2**attempt))
    raise ParserConnectionError(f"request failed after {retries} attempts: {url} ({last_exc})")
