from src.modules.parser.service.base import BaseParser, ParserManager, parser_manager
from src.modules.parser.service.parsers.divizion import DivizionParser
from src.modules.parser.service.parsers.liberti import LibertiParser
from src.modules.parser.service.parsers.profi import ProfiParser
from src.modules.parser.service.parsers.tgsm import TgsmParser

AVAILABLE_PARSERS: tuple[type[BaseParser], ...] = (
    TgsmParser,
    ProfiParser,
    LibertiParser,
    DivizionParser,
)

__all__ = [
    "AVAILABLE_PARSERS",
    "DivizionParser",
    "LibertiParser",
    "ProfiParser",
    "TgsmParser",
    "register_default_parsers",
]


def register_default_parsers(manager: ParserManager | None = None) -> list[BaseParser]:
    target = manager if manager is not None else parser_manager
    parsers = [parser_cls() for parser_cls in AVAILABLE_PARSERS]
    for parser in parsers:
        target.register(parser)
    return parsers
