import json
from pathlib import Path

from app.applications.materials import build_material_draft, prepare_application
from app.config.loader import load_project_config
from app.db.models import Job
from app.db.session import create_db_engine, init_db, make_session_factory


def test_build_material_draft_selects_data_summary() -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    job = Job(
        id=1,
        title="Data Engineer",
        company_name="Xero",
        location="Auckland",
        role_group="data",
        source="test",
        source_url="https://example.com/jobs/data",
    )

    draft = build_material_draft(job, config)

    assert "data engineering professional" in draft.summary
    assert "good data foundations" in draft.motivation
    assert "Dear Xero hiring team" in draft.cover_letter
    assert "Permanent Resident" in draft.screening_answers["work_rights"]


def test_prepare_application_is_idempotent(tmp_path) -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    engine = create_db_engine(tmp_path / "applications.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        job = Job(
            title="Software Engineer",
            company_name="Xero",
            location="Auckland",
            role_group="software",
            source="test",
            source_url="https://example.com/jobs/software",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        application, created = prepare_application(job, config, session)
        application_again, created_again = prepare_application(job, config, session)

        assert created is True
        assert created_again is False
        assert application_again.id == application.id
        assert application_again.status == "prepared"
        answers = json.loads(application_again.generated_screening_answers)
        assert "salary_expectations" in answers
        assert "Software Engineer" in application_again.generated_cover_letter

    engine.dispose()
