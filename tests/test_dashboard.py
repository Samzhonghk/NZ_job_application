from pathlib import Path

from app.dashboard.render import render_daily_digest, render_dashboard
from app.db.models import Application, Job
from app.db.session import create_db_engine, init_db, make_session_factory


def test_render_daily_digest(tmp_path) -> None:
    engine = create_db_engine(tmp_path / "digest.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        job = Job(
            title="Data Engineer",
            company_name="Xero",
            role_group="data",
            status="prepared",
            is_it_related=True,
            match_score=87,
            source="test",
            source_url="https://example.com/data",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        session.add(Application(job_id=job.id, status="prepared"))
        session.commit()

        digest = render_daily_digest(session)

        assert "NZ IT Job Application Daily Digest" in digest
        assert "Data Engineer" in digest
        assert "#1 | prepared" in digest

    engine.dispose()


def test_render_dashboard(tmp_path) -> None:
    engine = create_db_engine(tmp_path / "dashboard.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)
    output = tmp_path / "dashboard.html"

    with session_factory() as session:
        job = Job(
            title="Software Engineer",
            company_name="Xero",
            role_group="software",
            status="prepared",
            is_it_related=True,
            match_score=79,
            source="test",
            source_url="https://example.com/software",
        )
        business_analyst_job = Job(
            title="Business Analyst",
            company_name="Xero",
            role_group="business_analyst",
            status="discovered",
            is_it_related=True,
            match_score=95,
            source="test",
            source_url="https://example.com/business-analyst",
        )
        broad_analyst_job = Job(
            title="Analyst",
            company_name="Xero",
            role_group="analyst",
            status="discovered",
            is_it_related=True,
            match_score=96,
            source="test",
            source_url="https://example.com/analyst",
        )
        non_it_job = Job(
            title="Personal Assistant",
            company_name="Xero",
            role_group="non_it",
            status="discovered",
            is_it_related=False,
            match_score=99,
            source="test",
            source_url="https://example.com/pa",
        )
        session.add(job)
        session.add(business_analyst_job)
        session.add(broad_analyst_job)
        session.add(non_it_job)
        session.commit()
        session.refresh(job)
        session.add(Application(job_id=job.id, status="prepared"))
        session.add(Application(job_id=job.id, status="paused_for_review"))
        session.add(Application(job_id=job.id, status="submitted"))
        session.add(Application(job_id=job.id, status="sample_archived"))
        session.add(Application(job_id=job.id, status="superseded_duplicate"))
        session.commit()

        render_dashboard(session, output)

        html = output.read_text(encoding="utf-8")
        assert "NZ IT Job Application Dashboard" in html
        assert "Software Engineer" in html
        assert "Business Analyst" in html
        assert ">Analyst<" not in html
        assert "Personal Assistant" not in html
        assert "Paused for review" in html
        assert "Submitted" in html
        assert "manual-assist --url" in html
        assert "Next Action" in html
        assert "mark-application" in html
        assert ">Open<" in html
        assert "sample_archived" not in html
        assert "superseded_duplicate" not in html

    engine.dispose()
