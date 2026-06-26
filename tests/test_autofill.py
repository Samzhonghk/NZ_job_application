from pathlib import Path

from app.browser.autofill import (
    plan_autofill_for_file,
    record_autofill_pause,
    record_autofill_plan,
    summarise_plan,
)
from app.browser.field_detector import FormField
from app.browser.field_matcher import build_autofill_plan
from app.config.loader import load_project_config
from app.db.models import Application, Job, AutofillLog
from app.db.session import create_db_engine, init_db, make_session_factory


def test_build_autofill_plan_fills_reviews_and_pauses() -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    fields = [
        FormField(selector="#email", field_type="email", label="Email address", name="email"),
        FormField(selector="#salary", field_type="text", label="Salary expectation", name="salary"),
        FormField(selector="#ird", field_type="text", label="IRD number", name="ird_number"),
    ]

    plan = build_autofill_plan(fields, config)
    summary = summarise_plan(plan)

    assert plan[0].action == "fill"
    assert plan[0].value == "samzhongnz@gmail.com"
    assert plan[1].review_required is True
    assert "NZD 80,000" in plan[1].value
    assert plan[2].paused is True
    assert plan[2].matched_rule == "ird_number"
    assert summary == {"filled": 1, "review_required": 1, "paused": 1, "skipped": 0}


def test_plan_autofill_for_static_form() -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    form_url = (Path(__file__).resolve().parent / "fixtures" / "application_form.html").as_uri()

    plan = plan_autofill_for_file(form_url, config)
    summary = summarise_plan(plan)

    assert summary["filled"] >= 4
    assert summary["review_required"] >= 2
    assert summary["paused"] == 1


def test_record_autofill_plan(tmp_path) -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    engine = create_db_engine(tmp_path / "autofill.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        job = Job(
            title="Data Engineer",
            company_name="Xero",
            source="test",
            source_url="https://example.com/jobs/data",
        )
        session.add(job)
        session.commit()
        application = Application(job_id=job.id, status="prepared")
        session.add(application)
        session.commit()
        session.refresh(application)

        fields = [FormField(selector="#email", field_type="email", label="Email address", name="email")]
        plan = build_autofill_plan(fields, config)
        record_autofill_plan(application, plan, session, mark_completed=True)

        assert session.query(AutofillLog).count() == 1
        assert application.status == "ready_for_manual_submit"

    engine.dispose()


def test_record_autofill_pause(tmp_path) -> None:
    engine = create_db_engine(tmp_path / "autofill_pause.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        job = Job(
            title="Software Engineer",
            company_name="Partly",
            source="test",
            source_url="https://example.com/jobs/software",
        )
        session.add(job)
        session.commit()
        application = Application(job_id=job.id, status="prepared")
        session.add(application)
        session.commit()
        session.refresh(application)

        record_autofill_pause(
            application,
            session,
            pause_reason="captcha_or_bot_verification",
        )

        log = session.query(AutofillLog).one()
        assert application.status == "paused_for_review"
        assert log.action == "pause"
        assert log.paused is True
        assert log.pause_reason == "captcha_or_bot_verification"

    engine.dispose()
