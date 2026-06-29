from pathlib import Path

from sqlalchemy import select

from app.config.loader import load_project_config
from app.db.job_repository import upsert_job_from_raw
from app.db.models import Job
from app.db.session import create_db_engine, init_db, make_session_factory
from app.sources.seek_email import parse_seek_email_file, parse_seek_email_folder


FIXTURE = Path(__file__).parent / "fixtures" / "seek_recommendation_email.html"
EML_FIXTURE = Path(__file__).parent / "fixtures" / "seek_recommendation_email.eml"


def test_parse_seek_email_file_extracts_recommended_jobs() -> None:
    result = parse_seek_email_file(FIXTURE)

    assert result.path == FIXTURE
    assert [job.title for job in result.jobs] == ["Software Developer", "Business Analyst"]
    assert result.jobs[0].company_name == "KPMG"
    assert result.jobs[0].location == "Auckland CBD, Auckland (Hybrid)"
    assert result.jobs[0].source == "seek_email"
    assert result.jobs[0].external_id == "123456"
    assert "clean, reliable code" in result.jobs[0].description
    assert result.jobs[1].company_name == "Deloitte New Zealand"


def test_parse_seek_email_folder_reads_html_files(tmp_path) -> None:
    email_path = tmp_path / "seek_email.html"
    email_path.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    results = parse_seek_email_folder(tmp_path)

    assert len(results) == 1
    assert len(results[0].jobs) == 2


def test_parse_seek_email_file_reads_eml_html_body() -> None:
    result = parse_seek_email_file(EML_FIXTURE)

    assert [job.title for job in result.jobs] == ["Data Analyst"]
    assert result.jobs[0].company_name == "Example Analytics"
    assert result.jobs[0].external_id == "246810"


def test_parse_seek_email_folder_reads_eml_files(tmp_path) -> None:
    email_path = tmp_path / "seek_email.eml"
    email_path.write_text(EML_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    results = parse_seek_email_folder(tmp_path)

    assert len(results) == 1
    assert results[0].jobs[0].title == "Data Analyst"


def test_import_seek_email_jobs_are_scored_and_deduplicated(tmp_path) -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    engine = create_db_engine(tmp_path / "seek.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)
    raw_jobs = parse_seek_email_file(FIXTURE).jobs

    with session_factory() as session:
        first_job, first_created = upsert_job_from_raw(raw_jobs[0], session, config=config)
        duplicate_job, duplicate_created = upsert_job_from_raw(raw_jobs[0], session, config=config)
        second_job, second_created = upsert_job_from_raw(raw_jobs[1], session, config=config)

        stored_jobs = session.scalars(select(Job).order_by(Job.id)).all()

        assert first_created is True
        assert duplicate_created is False
        assert second_created is True
        assert first_job.id == duplicate_job.id
        assert len(stored_jobs) == 2
        assert first_job.role_group == "software"
        assert second_job.role_group == "business_analyst"
        assert first_job.match_score is not None

    engine.dispose()
