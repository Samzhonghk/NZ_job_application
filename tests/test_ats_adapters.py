from pathlib import Path

from app.config.loader import load_project_config
from app.db.importers import import_companies
from app.db.models import Job, SourceScan
from app.db.session import create_db_engine, init_db, make_session_factory
from app.sources.base import CompanySource
from app.sources.generic_html import GenericHtmlAdapter, extract_job_links
from app.sources.greenhouse import GreenhouseAdapter
from app.sources.lever import LeverAdapter
from app.sources.scanner import find_company_by_name, scan_company
from app.sources.smartrecruiters import SmartRecruitersAdapter, _raw_job as smartrecruiters_raw_job


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_greenhouse_adapter_fetches_jobs() -> None:
    source = CompanySource(
        company_name="Xero",
        source_type="greenhouse",
        identifier="example",
        url=(FIXTURES / "greenhouse_jobs.json").as_uri(),
    )

    jobs = GreenhouseAdapter().fetch_jobs(source)

    assert len(jobs) == 1
    assert jobs[0].title == "Software Engineer"
    assert jobs[0].company_name == "Xero"
    assert jobs[0].location == "Auckland, New Zealand"


def test_lever_adapter_fetches_jobs() -> None:
    source = CompanySource(
        company_name="Xero",
        source_type="lever",
        identifier="example",
        url=(FIXTURES / "lever_jobs.json").as_uri(),
    )

    jobs = LeverAdapter().fetch_jobs(source)

    assert len(jobs) == 1
    assert jobs[0].title == "Data Engineer"
    assert jobs[0].employment_type == "Full-time"
    assert jobs[0].apply_url.endswith("/apply")


def test_smartrecruiters_adapter_fetches_jobs() -> None:
    source = CompanySource(
        company_name="Xero",
        source_type="smartrecruiters",
        identifier="example",
        url=(FIXTURES / "smartrecruiters_jobs.json").as_uri(),
    )

    jobs = SmartRecruitersAdapter().fetch_jobs(source)

    assert len(jobs) == 1
    assert jobs[0].title == "Cloud Engineer"
    assert jobs[0].location == "Wellington, New Zealand"
    assert jobs[0].source_url == "https://jobs.smartrecruiters.com/example/sr-1-cloud-engineer"


def test_smartrecruiters_adapter_uses_api_company_token_for_generated_url() -> None:
    source = CompanySource(
        company_name="Deloitte New Zealand",
        source_type="smartrecruiters",
        identifier="Deloitte New Zealand",
        url="https://api.smartrecruiters.com/v1/companies/DeloitteNZ/postings",
    )

    job = smartrecruiters_raw_job(
        {"id": "6000000001144823", "name": "Software Developer"},
        source,
    )

    assert job.source_url == "https://jobs.smartrecruiters.com/DeloitteNZ/6000000001144823-software-developer"


def test_generic_html_adapter_fetches_linked_jobs() -> None:
    source = CompanySource(
        company_name="Example",
        source_type="generic_html",
        identifier="example",
        url=(FIXTURES / "generic_careers.html").as_uri(),
    )

    jobs = GenericHtmlAdapter().fetch_jobs(source)

    assert len(jobs) == 2
    assert {job.title for job in jobs} == {"Senior Software Engineer - Example", "Data Engineer"}
    assert all(job.company_name == "Example" for job in jobs)


def test_extract_job_links_filters_non_job_links() -> None:
    html = (FIXTURES / "generic_careers.html").read_text(encoding="utf-8")

    links = extract_job_links(html, (FIXTURES / "generic_careers.html").as_uri())

    assert len(links) == 2
    assert all("privacy" not in link for link in links)


def test_scan_company_imports_and_scores_jobs(tmp_path) -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_project_config(root)
    engine = create_db_engine(tmp_path / "scan.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        import_companies(config, session)
        company = find_company_by_name(session, "Xero")
        assert company is not None
        source = CompanySource(
            company_name="Xero",
            source_type="lever",
            identifier="example",
            url=(FIXTURES / "lever_jobs.json").as_uri(),
        )

        found, created = scan_company(company, session, config, source_override=source)
        found_again, created_again = scan_company(company, session, config, source_override=source)

        assert found == 1
        assert created == 1
        assert found_again == 1
        assert created_again == 0
        assert session.query(Job).count() == 1
        assert session.query(SourceScan).count() == 2
        job = session.query(Job).one()
        assert job.role_group == "data"
        assert job.match_score is not None

    engine.dispose()


def test_scan_company_with_generic_html_source(tmp_path) -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_project_config(root)
    engine = create_db_engine(tmp_path / "generic_scan.sqlite3")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        import_companies(config, session)
        company = find_company_by_name(session, "Xero")
        assert company is not None
        source = CompanySource(
            company_name="Xero",
            source_type="generic_html",
            identifier="example",
            url=(FIXTURES / "generic_careers.html").as_uri(),
        )

        found, created = scan_company(company, session, config, source_override=source)

        assert found == 2
        assert created == 2
        assert session.query(Job).count() == 2
        assert {job.role_group for job in session.query(Job).all()} >= {"software", "data"}

    engine.dispose()
