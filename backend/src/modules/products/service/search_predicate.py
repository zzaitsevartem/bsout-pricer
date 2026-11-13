import re

from sqlalchemy import and_, func, or_, true

from src.modules.catalog.service.normalizer import edit_distance, token_variants

_ALIASES = (
    ("дисплей", "экран", "display", "lcd"),
    ("iphone", "айфон"),
    ("samsung", "самсунг"),
    ("galaxy", "галакси"),
    ("nokia", "нокиа"),
    ("аккумулятор", "батарея", "battery"),
)
_LAYOUT = str.maketrans(
    "qwertyuiop[]asdfghjkl;'zxcvbnm,.",
    "йцукенгшщзхъфывапролджэячсмитьбю",
)
_REVERSE_LAYOUT = {value: key for key, value in _LAYOUT.items()}
_SCRIPT_SPELLINGS = (
    ("пленка", "plenka"),
    ("шлейф", "shleyf", "shleif"),
    ("стекло", "steklo"),
    ("iphone", "айфон"),
    ("samsung", "самсунг"),
    ("galaxy", "галакси"),
    ("nokia", "нокиа"),
)
_MODEL_TOKENS = frozenset({"se", "xr", "gt", "pro"})
_MAX_TOKEN_CANDIDATES = 12
_MAX_QUERY_EXPANSIONS = 64
_MODEL_LETTERS = str.maketrans({"а": "a", "с": "s", "А": "a", "С": "s"})


def _query_tokens(query: str) -> list[tuple[str, bool]]:
    text = query.lower()
    tokens = []
    for match in re.finditer(r"[\w]+", text, flags=re.UNICODE):
        token = match.group()
        adjacent_hyphen = (match.start() > 0 and text[match.start() - 1] == "-") or (
            match.end() < len(text) and text[match.end()] == "-"
        )
        protected = token in _MODEL_TOKENS or "_" in token or adjacent_hyphen
        tokens.append((token, protected))
    return tokens


def _alphabetic(token: str) -> bool:
    return bool(re.fullmatch(r"[a-z]+|[а-яё]+", token))


def _script_variants(token: str) -> tuple[str, ...]:
    folded = token.replace("ё", "е")
    if len(folded) < 4:
        return ()
    for spellings in _SCRIPT_SPELLINGS:
        if folded in spellings:
            keys = token_variants(folded)
            return tuple(value for value in spellings if keys & token_variants(value))
    return ()


def search_terms(query: str, fuzzy: bool) -> list[list[str]]:
    terms = []
    remaining = _MAX_QUERY_EXPANSIONS
    for token, protected in _query_tokens(query):
        variants = [token]
        if not protected:
            if _alphabetic(token) and len(token) >= 2:
                translated = token.translate(_LAYOUT if token.isascii() else _REVERSE_LAYOUT)
                variants.append(translated)
                for value in tuple(variants):
                    variants.extend(_script_variants(value))
            if fuzzy:
                if any(char.isdigit() for char in token):
                    variants.append(token.translate(_MODEL_LETTERS))
                for aliases in _ALIASES:
                    if any(
                        value in aliases
                        or (
                            len(value) >= 5
                            and value.isalpha()
                            and any(
                                len(alias) >= 5 and edit_distance(value, alias, limit=1) <= 1
                                for alias in aliases
                            )
                        )
                        for value in variants
                    ):
                        variants.extend(aliases)
        unique = list(dict.fromkeys(variants))
        extras = unique[1 : min(_MAX_TOKEN_CANDIDATES, remaining + 1)]
        remaining -= len(extras)
        terms.append([token, *extras])
    return terms


def search_predicate(column, query: str, fuzzy: bool = False):
    terms = []
    for (_, protected), variants in zip(_query_tokens(query), search_terms(query, fuzzy)):
        matches = []
        for term in variants:
            escaped = re.escape(term)
            if term.isdecimal():
                matches.append(column.op("~*")(rf"(^|[^0-9]){escaped}([^0-9]|$)"))
            elif any(char.isdigit() for char in term):
                model = re.sub(r"(?<=[^0-9])(?=[0-9])", "[[:space:]-]*", escaped)
                matches.append(column.op("~*")(rf"(^|[^[:alnum:]]){model}([^[:alnum:]]|$)"))
            elif protected:
                matches.append(column.op("~*")(rf"(^|[^[:alnum:]]){escaped}([^[:alnum:]]|$)"))
            else:
                if _alphabetic(term) and any(char in "её" for char in term):
                    pattern = re.sub("[её]", "[её]", escaped)
                    matches.append(column.op("~*")(pattern))
                else:
                    matches.append(column.ilike(f"%{term}%", escape="\\"))
                if fuzzy and len(term) >= 4 and term.isalpha():
                    matches.append(func.strict_word_similarity(term, func.lower(column)) >= 0.4)
        terms.append(or_(*matches))
    return and_(*terms) if terms else true()
