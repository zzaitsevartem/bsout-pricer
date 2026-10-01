import re

_PUNCT_RE = re.compile(r"[^0-9a-zа-я]+")
_RUN_RE = re.compile(r"[a-zа-я]+|[0-9]+")

_HOMOGLYPHS = {
    "а": "a",
    "в": "b",
    "е": "e",
    "к": "k",
    "м": "m",
    "н": "h",
    "о": "o",
    "р": "p",
    "с": "c",
    "т": "t",
    "у": "y",
    "х": "x",
}

_CYRILLIC = set("абвгдежзийклмнопрстуфхцчшщъыьэюя")
_LATIN = set("abcdefghijklmnopqrstuvwxyz")
_DIGITS = set("0123456789")

_TRANSLIT = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "i",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "c",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "u",
    "я": "a",
}

_LATIN_FOLD = {"x": "ks", "y": "i", "j": "i", "w": "v", "q": "k", "c": "k"}

_DIGRAPH_FOLD = (
    ("ph", "f"),
    ("ai", "i"),
    ("ei", "i"),
    ("ou", "u"),
    ("oo", "u"),
    ("ee", "i"),
    ("ia", "a"),
)

_ENDINGS = (
    "ыми",
    "ими",
    "ого",
    "его",
    "ому",
    "ему",
    "ами",
    "ями",
    "ая",
    "яя",
    "ое",
    "ее",
    "ые",
    "ие",
    "ый",
    "ий",
    "ой",
    "ей",
    "ам",
    "ям",
    "ах",
    "ях",
    "ом",
    "ем",
    "ым",
    "им",
    "ых",
    "их",
    "ую",
    "юю",
    "ов",
    "ев",
    "а",
    "я",
    "о",
    "е",
    "ы",
    "и",
    "у",
    "ю",
    "ь",
    "й",
)

_STEM_TRAILING = set("аеиоуыэюяй")

_MIN_STEM_LEN = 3
_MIN_GLUE_ALPHA = 3
_MIN_LATIN_KEY_LEN = 3


def _fold_homoglyphs(token: str) -> str:
    has_anchor = any(ch in _LATIN or ch in _DIGITS for ch in token)
    if not has_anchor:
        return token
    cyrillic = [ch for ch in token if ch in _CYRILLIC]
    if not cyrillic or any(ch not in _HOMOGLYPHS for ch in cyrillic):
        return token
    return "".join(_HOMOGLYPHS.get(ch, ch) for ch in token)


def _split_glued(token: str) -> list[str]:
    runs = _RUN_RE.findall(token)
    if len(runs) < 2:
        return [token] if token else []
    parts: list[str] = [runs[0]]
    for run in runs[1:]:
        previous = parts[-1]
        prev_run = _RUN_RE.findall(previous)[-1]
        prev_is_alpha = prev_run[0] not in _DIGITS
        cur_is_alpha = run[0] not in _DIGITS
        boundary_alpha = prev_run if prev_is_alpha else (run if cur_is_alpha else "")
        if prev_is_alpha != cur_is_alpha and len(boundary_alpha) >= _MIN_GLUE_ALPHA:
            parts.append(run)
        else:
            parts[-1] = previous + run
    return parts


def normalize(title: str) -> str:
    if not title:
        return ""
    text = title.lower().replace("ё", "е")
    text = _PUNCT_RE.sub(" ", text)
    tokens: list[str] = []
    for raw in text.split():
        tokens.extend(_split_glued(_fold_homoglyphs(raw)))
    return " ".join(token for token in tokens if token)


def tokenize(title: str) -> list[str]:
    normalized = normalize(title)
    return normalized.split() if normalized else []


def _trim_trailing_vowels(token: str) -> str:
    result = token
    while len(result) > _MIN_STEM_LEN and result[-1] in _STEM_TRAILING:
        result = result[:-1]
    return result


def stem(token: str) -> str:
    if len(token) <= 4 or not any(ch in _CYRILLIC for ch in token):
        return token
    for ending in _ENDINGS:
        if token.endswith(ending) and len(token) - len(ending) >= _MIN_STEM_LEN:
            return _trim_trailing_vowels(token[: -len(ending)])
    return _trim_trailing_vowels(token)


def latin_key(token: str) -> str:
    if len(token) < _MIN_LATIN_KEY_LEN:
        return token
    converted = "".join(_TRANSLIT.get(ch, ch) for ch in token)
    converted = "".join(_LATIN_FOLD.get(ch, ch) for ch in converted)
    for source, target in _DIGRAPH_FOLD:
        converted = converted.replace(source, target)
    collapsed: list[str] = []
    for ch in converted:
        if collapsed and collapsed[-1] == ch and ch not in _DIGITS:
            continue
        collapsed.append(ch)
    result = "".join(collapsed)
    if len(result) > _MIN_STEM_LEN and result.endswith("e"):
        result = result[:-1]
    return result or token


def token_variants(token: str) -> frozenset[str]:
    stemmed = stem(token)
    return frozenset({token, stemmed, latin_key(token), latin_key(stemmed)})


def edit_distance(left: str, right: str, limit: int = 1) -> int:
    if left == right:
        return 0
    if abs(len(left) - len(right)) > limit:
        return limit + 1
    previous_previous: list[int] = []
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            cost = 0 if left_char == right_char else 1
            value = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
            if (
                i > 1
                and j > 1
                and left_char == right[j - 2]
                and left[i - 2] == right_char
                and previous_previous
            ):
                value = min(value, previous_previous[j - 2] + 1)
            current.append(value)
        if min(current) > limit:
            return limit + 1
        previous_previous = previous
        previous = current
    return previous[-1]


def strip_stopwords(tokens: list[str], stopwords: frozenset[str]) -> list[str]:
    if not stopwords:
        return list(tokens)
    return [token for token in tokens if token not in stopwords and stem(token) not in stopwords]
