import argparse
import asyncio
import getpass
import json
import os
import pathlib
import sys
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_factory
from src.modules.auth.service.auth import create_user, get_user_by_email
from src.modules.auth.service.security import WeakCredentialsError, validate_admin_credentials
from src.modules.catalog.service.seed import seed_all
from src.modules.products.service.matching_service import MatchingService

ADMIN_PASSWORD_ENV = "BSCOUT_ADMIN_PASSWORD"

ADMIN_MESSAGES = {
    "created": "create-admin: created administrator {email}",
    "promoted": "create-admin: promoted {email} to administrator",
    "exists_admin": "create-admin: {email} is already an administrator, nothing to do",
    "exists": "create-admin: {email} already exists but is not an administrator; "
    "rerun with --promote to grant admin rights",
}


class AdminBootstrapError(RuntimeError):
    pass


async def _run_seed() -> None:
    async with async_session_factory() as session:
        async with session.begin():
            await seed_all(session)


async def _run_match(only_unmatched: bool) -> dict:
    async with async_session_factory() as session:
        async with session.begin():
            return await MatchingService.match_all(session, only_unmatched=only_unmatched)


async def _run_gaps(limit: int) -> list[tuple[str, int]]:
    async with async_session_factory() as session:
        return await MatchingService.device_gap_report(session, limit=limit)


async def _run_import(path: str) -> dict:
    from src.modules.admin.service.offer_import_service import OfferImportService

    rows = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    async with async_session_factory() as session:
        result = await OfferImportService.import_offers(session, rows)
        await session.commit()
        return {
            "created": result.created,
            "updated": result.updated,
            "errors": len(result.errors),
        }


async def _run_precision(limit: int) -> tuple[dict, list[dict]]:
    async with async_session_factory() as session:
        stats = await MatchingService.precision_stats(session)
        rows = await MatchingService.precision_report(session, limit=limit)
        return stats, rows


async def create_admin(
    db: AsyncSession,
    email: str,
    full_name: str,
    promote: bool,
    password_provider: Callable[[], str],
) -> str:
    existing = await get_user_by_email(db, email)
    if existing is not None:
        if existing.is_admin:
            return "exists_admin"
        if not promote:
            return "exists"
        existing.is_admin = True
        await db.flush()
        return "promoted"

    credentials = validate_admin_credentials(
        email=email, password=password_provider(), full_name=full_name
    )
    user = await create_user(
        db=db,
        email=credentials.email,
        password=credentials.password,
        full_name=credentials.full_name,
        phone=None,
        company=None,
    )
    user.is_admin = True
    await db.flush()
    return "created"


async def _run_create_admin(
    email: str, full_name: str, promote: bool, password_provider: Callable[[], str]
) -> str:
    async with async_session_factory() as session:
        async with session.begin():
            return await create_admin(session, email, full_name, promote, password_provider)


def read_admin_password() -> str:
    from_env = os.environ.get(ADMIN_PASSWORD_ENV)
    if from_env:
        return from_env
    if not sys.stdin.isatty():
        raise AdminBootstrapError(
            f"no tty for an interactive prompt; set {ADMIN_PASSWORD_ENV} instead"
        )
    password = getpass.getpass("Admin password: ")
    if password != getpass.getpass("Repeat password: "):
        raise AdminBootstrapError("passwords do not match")
    return password


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m src.cli")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("seed", help="idempotently seed catalog, stores and categories")
    match_parser = subparsers.add_parser("match", help="match store offers to canonical products")
    match_parser.add_argument("--all", action="store_true", help="rematch already linked offers")
    gaps_parser = subparsers.add_parser(
        "gaps", help="report top unrecognized devices from review-status offers"
    )
    gaps_parser.add_argument("--limit", type=int, default=30)
    import_parser = subparsers.add_parser("import", help="import store offers from a json file")
    import_parser.add_argument(
        "--path", default="data/fixtures/demo_offers.json", help="path to the offers json"
    )
    precision_parser = subparsers.add_parser(
        "precision",
        help="report auto-matched offers whose title carries a model suffix the device lacks",
    )
    precision_parser.add_argument("--limit", type=int, default=30)
    precision_parser.add_argument(
        "--max-share",
        type=float,
        default=None,
        help="exit with code 1 if the suspicious share exceeds this percentage",
    )
    admin_parser = subparsers.add_parser(
        "create-admin",
        help=f"create an administrator; password comes from {ADMIN_PASSWORD_ENV} or a prompt",
    )
    admin_parser.add_argument("--email", required=True)
    admin_parser.add_argument("--full-name", default="Administrator")
    admin_parser.add_argument(
        "--promote", action="store_true", help="grant admin rights to an existing user"
    )
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
    if args.command == "gaps":
        rows = asyncio.run(_run_gaps(args.limit))
        if not rows:
            print("gaps: no review-status offers")
            return 0
        for phrase, count in rows:
            print(f"{count:4d}  {phrase}")
        return 0

    if args.command == "import":
        stats = asyncio.run(_run_import(args.path))
        print(
            f"import: created={stats['created']} updated={stats['updated']} "
            f"errors={stats['errors']}"
        )
        return 1 if stats["errors"] else 0

    if args.command == "precision":
        stats, rows = asyncio.run(_run_precision(args.limit))
        print(
            f"precision: auto={stats['auto']} suspicious={stats['suspicious']} "
            f"({stats['share_pct']}%)"
        )
        for row in rows:
            print(f"  [{','.join(row['missing'])}] -> {row['device']} | {row['title']}")
        if args.max_share is not None and stats["share_pct"] > args.max_share:
            print(
                f"precision: share {stats['share_pct']}% exceeds limit {args.max_share}%",
                file=sys.stderr,
            )
            return 1
        return 0
    if args.command == "create-admin":
        try:
            outcome = asyncio.run(
                _run_create_admin(
                    email=args.email,
                    full_name=args.full_name,
                    promote=args.promote,
                    password_provider=read_admin_password,
                )
            )
        except (AdminBootstrapError, WeakCredentialsError) as exc:
            print(f"create-admin: {exc}", file=sys.stderr)
            return 1
        print(ADMIN_MESSAGES[outcome].format(email=args.email))
        return 0 if outcome != "exists" else 1
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
