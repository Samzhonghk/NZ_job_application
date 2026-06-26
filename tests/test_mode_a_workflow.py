from pathlib import Path

from app.config.loader import load_project_config
from app.db.models import Application, AutofillLog, Job
from app.db.session import create_db_engine, init_db, make_session_factory
from app.workflows.mode_a import run_mode_a


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_run_mode_a_creates_job_and_application(tmp_path) -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    engine = create_db_engine(tmp_path / "mode_a.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        result = run_mode_a(
            (FIXTURES / "sample_job.html").as_uri(),
            config,
            session,
        )

        assert result.job_created is True
        assert result.application_created is True
        assert result.title == "Software Engineer"
        assert result.role_group == "software"
        assert result.match_score is not None
        assert result.recommendation in {"possible_match", "good_match", "strong_match"}
        assert session.query(Job).count() == 1
        assert session.query(Application).count() == 1

    engine.dispose()


def test_run_mode_a_with_static_autofill_plan(tmp_path) -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    engine = create_db_engine(tmp_path / "mode_a_autofill.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        result = run_mode_a(
            (FIXTURES / "sample_job.html").as_uri(),
            config,
            session,
            form_url=(FIXTURES / "application_form.html").as_uri(),
            static_file_plan=True,
        )

        assert result.autofill_summary is not None
        assert result.autofill_summary["filled"] == 4
        assert result.autofill_summary["review_required"] == 2
        assert result.autofill_summary["paused"] == 1
        assert session.query(AutofillLog).count() == 7

    engine.dispose()
