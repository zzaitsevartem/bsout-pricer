import re

from sqlalchemy import and_, func, or_, true

from src.modules.catalog.service.normalizer import edit_distance

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
_MODEL_LETTERS = str.maketrans({"а": "a", "с": "s", "А": "a", "С": "s"})


def search_terms(query: str, fuzzy: bool) -> list[list[str]]:
    tokens = re.findall(r"[\w]+", query.lower(), flags=re.UNICODE)
    terms = []
    for token in tokens:
        variants = [token]
        if fuzzy:
            variants.extend((token.translate(_LAYOUT), token.translate(_REVERSE_LAYOUT)))
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
        terms.append(list(dict.fromkeys(variants)))
    return terms


def search_predicate(column, query: str, fuzzy: bool = False):
    terms = []
    for variants in search_terms(query, fuzzy):
        matches = []
        for term in variants:
            if term.isdecimal():
                matches.append(column.op("~*")(rf"(^|[^0-9]){term}([^0-9]|$)"))
            elif any(char.isdigit() for char in term):
                model = re.sub(r"(?<=[^0-9])(?=[0-9])", "[[:space:]-]*", term)
                matches.append(column.op("~*")(rf"(^|[^[:alnum:]]){model}([^[:alnum:]]|$)"))
            else:
                matches.append(column.ilike(f"%{term}%"))
                if fuzzy and len(term) >= 4 and term.isalpha():
                    matches.append(func.strict_word_similarity(term, func.lower(column)) >= 0.4)
        terms.append(or_(*matches))
    return and_(*terms) if terms else true()
