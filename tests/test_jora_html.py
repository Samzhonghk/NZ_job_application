from pathlib import Path

from sqlalchemy import select

from app.config.loader import load_project_config
from app.db.job_repository import upsert_job_from_raw
from app.db.models import Job
from app.db.session import create_db_engine, init_db, make_session_factory
from app.sources.jora_html import parse_jora_html_file, parse_jora_html_folder


FIXTURE = Path(__file__).parent / "fixtures" / "jora_search_results.html"


def test_parse_jora_html_file_extracts_jobs() -> None:
    result = parse_jora_html_file(FIXTURE)

    assert result.path == FIXTURE
    assert [job.title for job in result.jobs] == [
        "Data and AI Specialist",
        "Remote Social Media AI Trainer (Freelance Annotator)",
    ]
    assert result.jobs[0].company_name == "Voyager Internet Services"
    assert result.jobs[0].location == "North Shore, North Island"
    assert result.jobs[0].source == "jora_html"
    assert result.jobs[0].source_url == "https://nz.jora.com/job/data-ai-specialist-abc123"
    assert "meaningful insights" in result.jobs[0].description
    assert result.jobs[1].company_name == "Invisible Agency"
    assert result.jobs[1].location == "New Zealand"


def test_parse_jora_html_folder_reads_html_files(tmp_path) -> None:
    html_path = tmp_path / "jora.html"
    html_path.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    results = parse_jora_html_folder(tmp_path)

    assert len(results) == 1
    assert len(results[0].jobs) == 2


def test_import_jora_html_jobs_are_scored_and_deduplicated(tmp_path) -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    engine = create_db_engine(tmp_path / "jora.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)
    raw_jobs = parse_jora_html_file(FIXTURE).jobs

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
        assert first_job.role_group in {"ai", "data", "data_analyst"}
        assert second_job.role_group in {"ai", "unknown"}
        assert first_job.match_score is not None

    engine.dispose()
