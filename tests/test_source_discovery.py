from pathlib import Path

from app.config.loader import load_project_config
from app.db.models import Company
from app.sources.base import CompanySource
from app.sources import discovery
from app.sources.discovery import (
    SourceDiscoveryResult,
    discover_career_url,
    discover_company_source,
    render_career_url_html_report,
    render_discovery_report,
)


def test_discover_company_source_finds_lever_link(monkeypatch) -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    company = Company(
        company_name="Example",
        website="https://example.com",
        career_url="https://example.com/careers",
        priority=1,
    )

    monkeypatch.setattr(
        discovery,
        "fetch_html",
        lambda url: '<a href="https://jobs.lever.co/example">Jobs</a>',
    )

    result = discover_company_source(company, config)

    assert result.status == "supported_ats"
    assert result.confidence == "high"
    assert result.source is not None
    assert result.source.source_type == "lever"
    assert result.source.url == "https://api.lever.co/v0/postings/example?mode=json"


def test_discover_career_url_from_homepage_link(monkeypatch) -> None:
    company = Company(
        company_name="Example",
        website="https://example.com",
        career_url="",
        priority=1,
    )

    monkeypatch.setattr(
        discovery,
        "fetch_html",
        lambda url: '<a href="/about/careers">Careers</a>',
    )

    result = discover_career_url(company)

    assert result.status == "found_link"
    assert result.confidence == "medium"
    assert result.career_url == "https://example.com/about/careers"


def test_discover_company_source_detects_login_required(monkeypatch) -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    company = Company(
        company_name="Example",
        website="https://example.com",
        career_url="https://example.com/candidate/login",
        priority=1,
    )

    monkeypatch.setattr(
        discovery,
        "fetch_html",
        lambda url: "<html>Sign in or create account to apply</html>",
    )

    result = discover_company_source(company, config)

    assert result.status == "login_required"
    assert result.source is None


def test_discover_company_source_falls_back_to_generic_html(monkeypatch) -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    company = Company(
        company_name="Example",
        website="https://example.com",
        career_url="https://example.com/careers",
        priority=1,
    )

    monkeypatch.setattr(
        discovery,
        "fetch_html",
        lambda url: "<html><h1>Open roles</h1><a href='/software-engineer'>View role</a></html>",
    )

    result = discover_company_source(company, config)

    assert result.status == "generic_html"
    assert result.confidence == "low"
    assert result.source is not None
    assert result.source.source_type == "generic_html"
    assert result.source.url == "https://example.com/careers"


def test_render_discovery_report_groups_statuses() -> None:
    report = render_discovery_report(
        [
            SourceDiscoveryResult(
                company_name="Lever Co",
                checked_url="https://example.com/careers",
                source=CompanySource(
                    company_name="Lever Co",
                    source_type="lever",
                    identifier="lever-co",
                    url="https://api.lever.co/v0/postings/lever-co?mode=json",
                ),
                confidence="high",
                status="supported_ats",
                evidence=["Found supported ATS link."],
            ),
            SourceDiscoveryResult(
                company_name="Login Co",
                checked_url="https://example.com/login",
                source=None,
                confidence="medium",
                status="login_required",
                evidence=["Account required."],
            ),
        ]
    )

    assert "# Company Source Discovery Report" in report
    assert "- supported_ats: 1" in report
    assert "- login_required: 1" in report
    assert "Lever Co" in report
    assert "https://api.lever.co/v0/postings/lever-co?mode=json" in report


def test_render_career_url_html_report() -> None:
    html = render_career_url_html_report(
        [
            discovery.CareerUrlDiscoveryResult(
                company_name="Example",
                career_url="https://example.com/careers",
                confidence="medium",
                status="found_link",
                evidence=["Found career-like link."],
            )
        ]
    )

    assert "Career URL Discovery" in html
    assert "https://example.com/careers" in html
    assert "found_link" in html
