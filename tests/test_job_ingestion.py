from pathlib import Path

from app.db.importers import import_companies
from app.db.job_repository import upsert_job_from_raw
from app.db.models import Job
from app.db.session import create_db_engine, init_db, make_session_factory
from app.config.loader import load_project_config
from app.sources.base import RawJob
from app.sources.generic_html import parse_job_from_html


JSON_LD_JOB_HTML = """
<html>
  <head>
    <title>Fallback title</title>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org/",
      "@type": "JobPosting",
      "title": "Software Engineer",
      "description": "<p>Build reliable internal tools with Python and SQL.</p>",
      "datePosted": "2026-06-25",
      "employmentType": "FULL_TIME",
      "hiringOrganization": {
        "@type": "Organization",
        "name": "Xero"
      },
      "jobLocation": {
        "@type": "Place",
        "address": {
          "@type": "PostalAddress",
          "addressLocality": "Auckland",
          "addressCountry": "NZ"
        }
      },
      "baseSalary": {
        "@type": "MonetaryAmount",
        "currency": "NZD",
        "value": {
          "@type": "QuantitativeValue",
          "minValue": 90000,
          "maxValue": 120000,
          "unitText": "YEAR"
        }
      },
      "url": "https://example.com/apply/software-engineer"
    }
    </script>
  </head>
  <body></body>
</html>
"""


GENERIC_JOB_HTML = """
<html>
  <head>
    <title>Data Engineer - Example Company</title>
    <meta name="description" content="Work on data pipelines and cloud workflows.">
  </head>
  <body>
    <a href="/apply">Apply now</a>
  </body>
</html>
"""


def test_parse_json_ld_job_posting() -> None:
    raw_job = parse_job_from_html(JSON_LD_JOB_HTML, "https://example.com/jobs/1")

    assert raw_job.title == "Software Engineer"
    assert raw_job.company_name == "Xero"
    assert raw_job.location == "Auckland, NZ"
    assert raw_job.description == "Build reliable internal tools with Python and SQL."
    assert raw_job.salary_text == "NZD 90000-120000 YEAR"
    assert raw_job.apply_url == "https://example.com/apply/software-engineer"
    assert raw_job.source == "json_ld_job_posting"


def test_parse_generic_html_fallback() -> None:
    raw_job = parse_job_from_html(GENERIC_JOB_HTML, "https://example.com/jobs/data-engineer")

    assert raw_job.title == "Data Engineer - Example Company"
    assert raw_job.company_name == "Example Company"
    assert raw_job.description == "Work on data pipelines and cloud workflows."
    assert raw_job.apply_url == "https://example.com/apply"
    assert raw_job.source == "generic_html"


def test_smartrecruiters_url_company_guess_uses_company_slug() -> None:
    raw_job = parse_job_from_html(
        "<html><head><title>Senior Software Engineer | Typescript</title></head></html>",
        "https://jobs.smartrecruiters.com/Partly/743999880344528-senior-software-engineer-typescript",
    )

    assert raw_job.company_name == "Partly"


def test_upsert_job_is_idempotent(tmp_path) -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_project_config(root)
    engine = create_db_engine(tmp_path / "jobs.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        import_companies(config, session)
        raw_job = parse_job_from_html(JSON_LD_JOB_HTML, "https://example.com/jobs/1")

        job, created = upsert_job_from_raw(raw_job, session)
        assert created is True
        assert job.id is not None
        assert job.company_name == "Xero"

        updated_job, created_again = upsert_job_from_raw(raw_job, session)
        assert created_again is False
        assert updated_job.id == job.id
        assert session.query(Job).count() == 1

    engine.dispose()


def test_upsert_job_matches_existing_external_id_when_url_changes(tmp_path) -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_project_config(root)
    engine = create_db_engine(tmp_path / "external_id.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        first = RawJob(
            title="Software Developer",
            company_name="Example",
            location="Auckland",
            description="Build software with Python.",
            source="smartrecruiters",
            source_url="https://jobs.smartrecruiters.com/ExampleOld/123-software-developer",
            external_id="123",
        )
        second = RawJob(
            title="Software Developer",
            company_name="Example",
            location="Auckland",
            description="Build software with Python and SQL.",
            source="smartrecruiters",
            source_url="https://jobs.smartrecruiters.com/ExampleNew/123-software-developer",
            external_id="123",
        )

        job, created = upsert_job_from_raw(first, session, config=config)
        updated, created_again = upsert_job_from_raw(second, session, config=config)

        assert created is True
        assert created_again is False
        assert updated.id == job.id
        assert updated.source_url == "https://jobs.smartrecruiters.com/ExampleNew/123-software-developer"
        assert session.query(Job).count() == 1

    engine.dispose()
