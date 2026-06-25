from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import func, select

from app.config.loader import load_project_config
from app.db.importers import import_companies
from app.db.models import Application, AutofillLog, Company, Job, SourceScan
from app.db.session import create_db_engine, init_db, make_session_factory


def main() -> None:
    parser = argparse.ArgumentParser(description="NZ IT job application automation CLI")
    parser.add_argument(
        "--root",
        default=str(Path.cwd()),
        help="Project root containing YAML and Markdown source files.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-config", help="Validate project source files.")
    subparsers.add_parser("init-db", help="Create local SQLite tables.")
    subparsers.add_parser("import-companies", help="Import company targets into the database.")
    subparsers.add_parser("db-summary", help="Show local database record counts.")

    args = parser.parse_args()
    root = Path(args.root)

    if args.command == "validate-config":
        config = load_project_config(root)
        print(f"Config OK: {len(config.companies)} companies loaded")
        return

    config = load_project_config(root)
    engine = create_db_engine(config.paths.database)
    session_factory = make_session_factory(engine)

    if args.command == "init-db":
        init_db(engine)
        print(f"Database initialised: {config.paths.database}")
        engine.dispose()
        return

    init_db(engine)
    try:
        with session_factory() as session:
            if args.command == "import-companies":
                created, updated = import_companies(config, session)
                print(f"Companies imported: {created} created, {updated} updated")
                return

            if args.command == "db-summary":
                counts = {
                    "companies": _count(session, Company),
                    "jobs": _count(session, Job),
                    "applications": _count(session, Application),
                    "autofill_logs": _count(session, AutofillLog),
                    "source_scans": _count(session, SourceScan),
                }
                for name, count in counts.items():
                    print(f"{name}: {count}")
                return
    finally:
        engine.dispose()


def _count(session, model: type) -> int:
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


if __name__ == "__main__":
    main()
