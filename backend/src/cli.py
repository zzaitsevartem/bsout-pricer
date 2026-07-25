import argparse
import asyncio
import sys

from src.database import async_session_factory
from src.modules.catalog.service.seed import seed_all


async def _run_seed() -> None:
    async with async_session_factory() as session:
        async with session.begin():
            await seed_all(session)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m src.cli")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("seed", help="idempotently seed catalog, stores and categories")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "seed":
        asyncio.run(_run_seed())
        print("seed: ok")
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
