from pathlib import Path

from app.config.loader import load_project_config
from app.db.models import Job
from app.jobs.classifier import classify_job
from app.jobs.scorer import score_job


def test_classifies_software_job() -> None:
    job = Job(
        title="Software Engineer",
        company_name="Xero",
        location="Auckland, NZ",
        description="Build Python, SQL, React and cloud services.",
        source="test",
        source_url="https://example.com/jobs/software",
    )

    result = classify_job(job)

    assert result.is_it_related is True
    assert result.role_group == "software"
    assert result.confidence >= 0.6


def test_classifies_non_it_job() -> None:
    job = Job(
        title="Retail Assistant",
        company_name="Example",
        location="Auckland",
        description="Customer service and store duties.",
        source="test",
        source_url="https://example.com/jobs/retail",
    )

    result = classify_job(job)

    assert result.is_it_related is False
    assert result.role_group == "non_it"


def test_non_it_title_overrides_description_keywords() -> None:
    job = Job(
        title="Personal Assistant",
        company_name="Example",
        location="Auckland",
        description="Support a technology team using data, automation, stakeholder tools and reporting.",
        source="test",
        source_url="https://example.com/jobs/personal-assistant",
    )

    result = classify_job(job)

    assert result.is_it_related is False
    assert result.role_group == "non_it"


def test_advisory_title_overrides_it_keywords() -> None:
    job = Job(
        title="Senior Manager - M&A (Deal Advisory)",
        company_name="Example",
        location="Auckland",
        description="Work with data, AI, automation, digital transformation and cloud teams.",
        source="test",
        source_url="https://example.com/jobs/deal-advisory",
    )

    result = classify_job(job)

    assert result.is_it_related is False
    assert result.role_group == "non_it"


def test_classifies_data_analyst_separately() -> None:
    job = Job(
        title="Data Analyst",
        company_name="Example",
        location="Auckland",
        description="Build dashboards, reporting, SQL datasets and Power BI insights.",
        source="test",
        source_url="https://example.com/jobs/data-analyst",
    )

    result = classify_job(job)

    assert result.is_it_related is True
    assert result.role_group == "data_analyst"


def test_classifies_business_analyst_separately() -> None:
    job = Job(
        title="Business Analyst",
        company_name="Example",
        location="Auckland",
        description="Gather requirements, write user stories, and work with stakeholders.",
        source="test",
        source_url="https://example.com/jobs/business-analyst",
    )

    result = classify_job(job)

    assert result.is_it_related is True
    assert result.role_group == "business_analyst"


def test_scores_strong_data_job() -> None:
    config = load_project_config(Path(__file__).resolve().parents[1])
    job = Job(
        title="Data Engineer",
        company_name="Example",
        location="Auckland, NZ",
        salary_text="NZD 90000-120000 YEAR",
        description="Build SQL ETL pipelines with Python, BigQuery, Airflow and GCP.",
        source="test",
        source_url="https://example.com/jobs/data",
    )

    classification = classify_job(job)
    score = score_job(job, config, classification)

    assert classification.role_group == "data"
    assert score.score >= 85
    assert score.components["skills"] > 10
