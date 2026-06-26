import json
from pathlib import Path

from app.config.loader import load_project_config
from app.db.models import Job
from app.db.session import create_db_engine, init_db, make_session_factory
from app.workflows.manual_assist import find_job_for_url, run_manual_assist


def test_find_job_for_smartrecruiters_oneclick_url(tmp_path) -> None:
    engine = create_db_engine(tmp_path / "manual_assist_find.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    publication_id = "0f23fe6c-0ad7-417b-b7f3-e529185ed3a0"
    with session_factory() as session:
        job = Job(
            title="Senior Software Engineer | Typescript",
            company_name="Partly",
            source="smartrecruiters",
            source_url="https://jobs.smartrecruiters.com/Partly/743999880344528-senior-software-engineer-typescript",
            raw_data=json.dumps({"job": {"uuid": publication_id, "id": "743999880344528"}}),
            status="archived",
        )
        active_duplicate = Job(
            title="Senior Software Engineer | Typescript",
            company_name="Partly",
            source="generic_html",
            source_url="https://jobs.smartrecruiters.com/Partly/743999880344528-senior-software-engineer-typescript",
            status="discovered",
        )
        session.add(job)
        session.add(active_duplicate)
        session.commit()

        matched, matched_by = find_job_for_url(
            f"https://jobs.smartrecruiters.com/oneclick-ui/company/Partly/publication/{publication_id}?dcr_ci=Partly",
            session,
        )

        assert matched is not None
        assert matched.id == active_duplicate.id
        assert matched_by == "url_token"

    engine.dispose()


def test_run_manual_assist_generates_copy_file(tmp_path) -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    engine = create_db_engine(tmp_path / "manual_assist.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        job = Job(
            title="Data Engineer",
            company_name="Xero",
            source="test",
            source_url="https://example.com/jobs/data-engineer",
            role_group="data",
            match_score=87.0,
            is_it_related=True,
        )
        session.add(job)
        session.commit()

        result = run_manual_assist(
            "https://example.com/jobs/data-engineer",
            config,
            session,
            output_dir=tmp_path,
            fetch_if_missing=False,
        )

        text = result.output_path.read_text(encoding="utf-8")
        assert result.application_id > 0
        assert result.status == "manual_apply_in_progress"
        assert result.output_path.exists()
        assert "Cover Letter" in text
        assert "work_rights" in text
        assert "New Zealand Permanent Resident" in text

    engine.dispose()
