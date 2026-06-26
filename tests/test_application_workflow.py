from app.db.models import Application, Job
from app.db.session import create_db_engine, init_db, make_session_factory
from app.workflows.applications import mark_application_status


def test_mark_application_submitted_updates_job_and_timestamp(tmp_path) -> None:
    engine = create_db_engine(tmp_path / "application_status.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        job = Job(
            title="Software Engineer",
            company_name="Example",
            source="test",
            source_url="https://example.com/software",
            status="discovered",
        )
        session.add(job)
        session.commit()
        application = Application(job_id=job.id, status="manual_apply_in_progress")
        session.add(application)
        session.commit()

        updated = mark_application_status(session, application.id, "submitted", note="Submitted manually.")

        assert updated is not None
        assert updated.status == "submitted"
        assert updated.submitted_at is not None
        assert updated.submission_confirmed_by_user is True
        assert updated.job.status == "applied"
        assert "Submitted manually." in updated.notes

    engine.dispose()


def test_mark_application_returns_none_for_missing_application(tmp_path) -> None:
    engine = create_db_engine(tmp_path / "missing_application.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        assert mark_application_status(session, 999, "submitted") is None

    engine.dispose()
