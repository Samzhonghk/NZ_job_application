from pathlib import Path

from app.config.loader import load_project_config
from app.db.models import Application, Job
from app.db.session import create_db_engine, init_db, make_session_factory
from app.workflows import mode_b
from app.workflows.mode_b import mark_job_status, prepare_jobs_batch, recommended_queue, run_daily_scan


def test_recommended_queue_orders_by_score(tmp_path) -> None:
    engine = create_db_engine(tmp_path / "queue.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        session.add_all(
            [
                Job(
                    title="Low Match",
                    company_name="Example",
                    is_it_related=True,
                    role_group="software",
                    match_score=60,
                    status="discovered",
                    source="test",
                    source_url="https://example.com/low",
                ),
                Job(
                    title="High Match",
                    company_name="Example",
                    is_it_related=True,
                    role_group="data",
                    match_score=90,
                    status="discovered",
                    source="test",
                    source_url="https://example.com/high",
                ),
                Job(
                    title="Ignored Match",
                    company_name="Example",
                    is_it_related=True,
                    role_group="data",
                    match_score=95,
                    status="ignored",
                    source="test",
                    source_url="https://example.com/ignored",
                ),
                Job(
                    title="Analyst Match",
                    company_name="Example",
                    is_it_related=True,
                    role_group="analyst",
                    match_score=99,
                    status="discovered",
                    source="test",
                    source_url="https://example.com/analyst",
                ),
                Job(
                    title="Business Analyst Match",
                    company_name="Example",
                    is_it_related=True,
                    role_group="business_analyst",
                    match_score=80,
                    status="discovered",
                    source="test",
                    source_url="https://example.com/business-analyst",
                ),
            ]
        )
        session.commit()

        queue = recommended_queue(session, minimum_score=55)
        data_queue = recommended_queue(session, minimum_score=55, role_groups=["data"])
        analyst_queue = recommended_queue(session, minimum_score=55, role_groups=["analyst"])

        assert [item.title for item in queue] == ["High Match", "Business Analyst Match", "Low Match"]
        assert queue[0].open_url == "https://example.com/high"
        assert [item.title for item in data_queue] == ["High Match"]
        assert [item.title for item in analyst_queue] == ["Analyst Match"]

    engine.dispose()


def test_batch_prepare_and_mark_status(tmp_path) -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    engine = create_db_engine(tmp_path / "batch.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        job = Job(
            title="Data Engineer",
            company_name="Xero",
            is_it_related=True,
            role_group="data",
            match_score=88,
            status="discovered",
            source="test",
            source_url="https://example.com/data",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        results = prepare_jobs_batch(session, config, [job.id])
        marked = mark_job_status(session, job.id, "shortlisted")

        assert len(results) == 1
        assert session.query(Application).count() == 1
        assert results[0].created is True
        assert marked is not None
        assert marked.status == "shortlisted"

    engine.dispose()


def test_run_daily_scan_refreshes_outputs(tmp_path, monkeypatch) -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    engine = create_db_engine(tmp_path / "daily.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    def fake_scan(session, config, max_priority=2, limit=60):
        job = Job(
            title="Software Engineer",
            company_name="Example",
            location="Auckland, NZ",
            description="Build Python and SQL services.",
            is_it_related=True,
            role_group="software",
            match_score=70,
            status="discovered",
            source="test",
            source_url="https://example.com/software",
        )
        session.add(job)
        session.commit()
        return (1, 1, 1)

    monkeypatch.setattr(mode_b, "scan_companies_by_priority", fake_scan)

    with session_factory() as session:
        result = run_daily_scan(
            session,
            config,
            max_priority=2,
            limit=60,
            minimum_score=55,
            dashboard_output=tmp_path / "dashboard.html",
        )

        assert result.companies_updated >= 0
        assert result.companies_scanned == 1
        assert result.jobs_found == 1
        assert result.new_jobs == 1
        assert result.jobs_scored == 1
        assert result.recommended_count == 1
        assert result.dashboard_path.exists()
        assert "Software Engineer" in result.digest

    engine.dispose()
