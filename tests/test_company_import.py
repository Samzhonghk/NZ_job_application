from pathlib import Path

from sqlalchemy import select

from app.config.loader import load_project_config
from app.db.importers import import_companies
from app.db.models import Company
from app.db.session import create_db_engine, init_db, make_session_factory


def test_import_companies_is_idempotent(tmp_path) -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_project_config(root)
    engine = create_db_engine(tmp_path / "test.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        created, updated = import_companies(config, session)
        assert created == len(config.companies)
        assert updated == 0

        created_again, updated_again = import_companies(config, session)
        assert created_again == 0
        assert updated_again == len(config.companies)

        companies = session.scalars(select(Company)).all()
        assert len(companies) == len(config.companies)
        assert any(company.company_name == "Xero" for company in companies)

    engine.dispose()
