import argparse
import asyncio
import sys

from src.database import async_session_factory
from src.modules.catalog.service.seed import seed_all
from src.modules.products.service.matching_service import MatchingService


async def _run_seed() -> None:
    async with async_session_factory() as session:
        async with session.begin():
            await seed_all(session)


async def _run_match(only_unmatched: bool) -> dict:
    async with async_session_factory() as session:
        async with session.begin():
            return await MatchingService.match_all(session, only_unmatched=only_unmatched)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m src.cli")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("seed", help="idempotently seed catalog, stores and categories")
    match_parser = subparsers.add_parser("match", help="match store offers to canonical products")
    match_parser.add_argument("--all", action="store_true", help="rematch already linked offers")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "seed":
        asyncio.run(_run_seed())
        print("seed: ok")
        return 0
    if args.command == "match":
        stats = asyncio.run(_run_match(only_unmatched=not args.all))
        print("match: " + " ".join(f"{key}={value}" for key, value in stats.items()))
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
