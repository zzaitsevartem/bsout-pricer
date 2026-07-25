import weakref
from dataclasses import dataclass

from src.modules.catalog.service.dictionaries import Dictionaries
from src.modules.catalog.service.normalizer import edit_distance, token_variants, tokenize

UNKNOWN_QUALITY_CODE = "unknown"

_WEIGHT_DEVICE = 0.5
_WEIGHT_PART_TYPE = 0.3
_WEIGHT_QUALITY = 0.15
_WEIGHT_COLOR = 0.05
_INCOMPLETE_CORE_FACTOR = 0.5
_FUZZY_FACTOR = 0.9
_FUZZY_MIN_LEN = 6
_FUZZY_MAX_DISTANCE = 1


@dataclass(frozen=True)
class ExtractedAttrs:
    brand_id: int | None
    device_id: int | None
    part_type_id: int | None
    quality_tier_id: int | None
    color_id: int | None
    confidence: float
    matched: dict[str, str]


@dataclass(frozen=True)
class _Entry:
    entity_id: int
    surface: str
    tokens: tuple[frozenset[str], ...]


@dataclass(frozen=True)
class _Index:
    devices: tuple[_Entry, ...]
    part_types: tuple[_Entry, ...]
    qualities: tuple[_Entry, ...]
    colors: tuple[_Entry, ...]
    unknown_quality_id: int | None


@dataclass(frozen=True)
class _Match:
    entity_id: int
    surface: str
    size: int
    contiguous: bool
    start: int


_index_cache: dict[int, _Index] = {}


def _build_entries(source: dict[str, int]) -> tuple[_Entry, ...]:
    entries: list[_Entry] = []
    for surface, entity_id in source.items():
        parts = surface.split()
        if not parts:
            continue
        entries.append(
            _Entry(
                entity_id=entity_id,
                surface=surface,
                tokens=tuple(token_variants(part) for part in parts),
            )
        )
    return tuple(entries)


def _build_index(dicts: Dictionaries) -> _Index:
    unknown_quality_id = None
    for tier_id, code in dicts.quality_code.items():
        if code == UNKNOWN_QUALITY_CODE:
            unknown_quality_id = tier_id
            break
    return _Index(
        devices=_build_entries(dicts.device_by_alias),
        part_types=_build_entries(dicts.part_type_by_synonym),
        qualities=_build_entries(dicts.quality_by_synonym),
        colors=_build_entries(dicts.color_by_synonym),
        unknown_quality_id=unknown_quality_id,
    )


def _get_index(dicts: Dictionaries) -> _Index:
    key = id(dicts)
    cached = _index_cache.get(key)
    if cached is not None:
        return cached
    index = _build_index(dicts)
    _index_cache[key] = index
    weakref.finalize(dicts, _index_cache.pop, key, None)
    return index


def _assign_positions(
    entry: _Entry, variants: list[frozenset[str]], union: frozenset[str]
) -> list[int] | None:
    options: list[list[int]] = []
    for token in entry.tokens:
        if not token & union:
            return None
        positions = [index for index, variant in enumerate(variants) if variant & token]
        if not positions:
            return None
        options.append(positions)

    assigned: dict[int, int] = {}

    def _try(slot: int, seen: set[int]) -> bool:
        for position in options[slot]:
            if position in seen:
                continue
            seen.add(position)
            if position not in assigned or _try(assigned[position], seen):
                assigned[position] = slot
                return True
        return False

    for slot in range(len(options)):
        if not _try(slot, set()):
            return None
    return sorted(assigned)


def _best_match(
    entries: tuple[_Entry, ...], variants: list[frozenset[str]], union: frozenset[str]
) -> _Match | None:
    best: _Match | None = None
    best_key: tuple[int, int, int, int] | None = None
    for entry in entries:
        positions = _assign_positions(entry, variants, union)
        if positions is None:
            continue
        size = len(positions)
        contiguous = positions[-1] - positions[0] == size - 1
        candidate_key = (size, int(contiguous), -positions[0], len(entry.surface))
        if best_key is None or candidate_key > best_key:
            best_key = candidate_key
            best = _Match(
                entity_id=entry.entity_id,
                surface=entry.surface,
                size=size,
                contiguous=contiguous,
                start=positions[0],
            )
    return best


def _fuzzy_match(entries: tuple[_Entry, ...], tokens: list[str]) -> _Match | None:
    best: _Match | None = None
    best_key: tuple[int, int, int] | None = None
    for entry in entries:
        if len(entry.tokens) != 1 or len(entry.surface) < _FUZZY_MIN_LEN:
            continue
        for position, token in enumerate(tokens):
            if len(token) < _FUZZY_MIN_LEN:
                continue
            distance = edit_distance(token, entry.surface, _FUZZY_MAX_DISTANCE)
            if distance > _FUZZY_MAX_DISTANCE or distance == 0:
                continue
            candidate_key = (-distance, -position, len(entry.surface))
            if best_key is None or candidate_key > best_key:
                best_key = candidate_key
                best = _Match(
                    entity_id=entry.entity_id,
                    surface=entry.surface,
                    size=1,
                    contiguous=True,
                    start=position,
                )
    return best


def extract(title: str, dicts: Dictionaries) -> ExtractedAttrs:
    tokens = tokenize(title)
    if not tokens:
        return ExtractedAttrs(
            brand_id=None,
            device_id=None,
            part_type_id=None,
            quality_tier_id=None,
            color_id=None,
            confidence=0.0,
            matched={},
        )

    index = _get_index(dicts)
    variants = [token_variants(token) for token in tokens]
    union = frozenset().union(*variants)

    device = _best_match(index.devices, variants, union)
    part_type = _best_match(index.part_types, variants, union)
    quality = _best_match(index.qualities, variants, union)
    color = _best_match(index.colors, variants, union)

    fuzzy_fields: list[str] = []
    if device is None:
        device = _fuzzy_match(index.devices, tokens)
        if device is not None:
            fuzzy_fields.append("device")
    if part_type is None:
        part_type = _fuzzy_match(index.part_types, tokens)
        if part_type is not None:
            fuzzy_fields.append("part_type")

    device_id = device.entity_id if device else None
    part_type_id = part_type.entity_id if part_type else None
    color_id = color.entity_id if color else None
    brand_id = dicts.device_brand.get(device_id) if device_id is not None else None

    if quality is not None:
        quality_tier_id = quality.entity_id
    else:
        quality_tier_id = index.unknown_quality_id

    matched: dict[str, str] = {}
    if device is not None:
        matched["device"] = device.surface
        model_key = dicts.device_model_key.get(device.entity_id)
        if model_key:
            matched["device_model_key"] = model_key
    if part_type is not None:
        matched["part_type"] = part_type.surface
        code = dicts.part_type_code.get(part_type.entity_id)
        if code:
            matched["part_type_code"] = code
    if quality is not None:
        matched["quality_tier"] = quality.surface
        code = dicts.quality_code.get(quality.entity_id)
        if code:
            matched["quality_tier_code"] = code
    if color is not None:
        matched["color"] = color.surface
        code = dicts.color_code.get(color.entity_id)
        if code:
            matched["color_code"] = code

    score = 0.0
    if device_id is not None:
        score += _WEIGHT_DEVICE
    if part_type_id is not None:
        score += _WEIGHT_PART_TYPE
    if quality is not None:
        score += _WEIGHT_QUALITY
    if color_id is not None:
        score += _WEIGHT_COLOR
    if device_id is None or part_type_id is None:
        score *= _INCOMPLETE_CORE_FACTOR
    if fuzzy_fields:
        score *= _FUZZY_FACTOR
        matched["fuzzy"] = ",".join(fuzzy_fields)

    return ExtractedAttrs(
        brand_id=brand_id,
        device_id=device_id,
        part_type_id=part_type_id,
        quality_tier_id=quality_tier_id,
        color_id=color_id,
        confidence=round(score, 3),
        matched=matched,
    )
