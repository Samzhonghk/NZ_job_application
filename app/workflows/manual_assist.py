from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.applications.materials import prepare_application
from app.config.schemas import ProjectConfig
from app.db.job_repository import upsert_job_from_raw
from app.db.models import Application, Job
from app.sources.generic_html import fetch_and_parse_job


@dataclass(frozen=True)
class ManualAssistResult:
    job_id: int
    application_id: int
    job_created: bool
    application_created: bool
    matched_by: str
    title: str
    company_name: str
    status: str
    output_path: Path


def run_manual_assist(
    url: str,
    config: ProjectConfig,
    session: Session,
    output_dir: Path | None = None,
    fetch_if_missing: bool = True,
) -> ManualAssistResult:
    job, matched_by = find_job_for_url(url, session)
    job_created = False

    if job is None:
        if not fetch_if_missing:
            raise ValueError(f"No local job matched URL: {url}")
        raw_job = fetch_and_parse_job(url)
        job, job_created = upsert_job_from_raw(raw_job, session, config=config)
        matched_by = "ingested_from_url"

    application, application_created = prepare_application(job, config, session)
    application.status = "manual_apply_in_progress"
    session.commit()
    session.refresh(application)

    path = render_manual_assist_file(
        application,
        url,
        output_dir or config.paths.root / "data" / "generated",
    )

    return ManualAssistResult(
        job_id=job.id,
        application_id=application.id,
        job_created=job_created,
        application_created=application_created,
        matched_by=matched_by,
        title=job.title,
        company_name=job.company_name,
        status=application.status,
        output_path=path,
    )


def find_job_for_url(url: str, session: Session) -> tuple[Job | None, str]:
    clean_url = _normalise_url(url)
    if not clean_url:
        return None, "none"

    exact = session.scalar(
        select(Job).where(or_(Job.source_url == clean_url, Job.apply_url == clean_url))
    )
    if exact is not None:
        return _active_duplicate_or_self(exact, session), "exact_url"

    url_tokens = _url_tokens(clean_url)
    jobs = session.scalars(select(Job).order_by(Job.id.desc())).all()
    for job in jobs:
        if _url_matches_job(clean_url, url_tokens, job):
            return _active_duplicate_or_self(job, session), "url_token"

    return None, "none"


def render_manual_assist_file(application: Application, source_url: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    job = application.job
    path = output_dir / f"manual_assist_application_{application.id}.md"
    answers = _screening_answers(application)

    lines = [
        f"# Manual Application Assist: {job.company_name or 'Unknown'} - {job.title}",
        "",
        "## Job",
        "",
        f"- Job ID: {job.id}",
        f"- Application ID: {application.id}",
        f"- Company: {job.company_name or 'Unknown'}",
        f"- Title: {job.title}",
        f"- Location: {job.location or 'Unknown'}",
        f"- Role group: {job.role_group or 'unknown'}",
        f"- Match score: {job.match_score if job.match_score is not None else 'unscored'}",
        f"- Source URL: {job.source_url or source_url}",
        f"- Manual URL: {source_url}",
        "",
        "## Quick Answers",
        "",
        f"- Work rights: {answers.get('work_rights', '')}",
        f"- Salary expectations: {answers.get('salary_expectations', '')}",
        f"- Declaration: {answers.get('declaration', '')}",
        "",
        "## Cover Letter",
        "",
        application.generated_cover_letter.strip(),
        "",
        "## Screening Answers",
        "",
    ]

    for key, value in answers.items():
        lines.extend([f"### {key}", "", str(value).strip(), ""])

    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return path


def _screening_answers(application: Application) -> dict[str, str]:
    try:
        value = json.loads(application.generated_screening_answers or "{}")
    except json.JSONDecodeError:
        return {}
    return {str(key): str(item) for key, item in value.items()}


def _url_matches_job(url: str, url_tokens: set[str], job: Job) -> bool:
    candidates = [
        job.source_url or "",
        job.apply_url or "",
        job.external_id or "",
        job.raw_data or "",
    ]
    for candidate in candidates:
        candidate_normalised = _normalise_url(candidate)
        if candidate_normalised and (url in candidate_normalised or candidate_normalised in url):
            return True
        if url_tokens and any(token in candidate for token in url_tokens):
            return True
    return False


def _active_duplicate_or_self(job: Job, session: Session) -> Job:
    if job.status not in {"archived", "ignored"}:
        return job

    duplicate = session.scalar(
        select(Job)
        .where(
            Job.id != job.id,
            Job.company_name == job.company_name,
            Job.title == job.title,
            Job.status.not_in(["archived", "ignored"]),
        )
        .order_by(Job.id.desc())
    )
    return duplicate or job


def _url_tokens(url: str) -> set[str]:
    parsed = urlparse(url)
    parts = re.split(r"[^A-Za-z0-9-]+", parsed.path)
    tokens = {part for part in parts if len(part) >= 8}
    publication_match = re.search(r"/publication/([A-Za-z0-9-]+)", parsed.path)
    if publication_match:
        tokens.add(publication_match.group(1))
    posting_match = re.search(r"/(\d{8,})[-/]", parsed.path)
    if posting_match:
        tokens.add(posting_match.group(1))
    return tokens


def _normalise_url(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    parsed = urlparse(text)
    if not parsed.scheme or not parsed.netloc:
        return text
    path = parsed.path.rstrip("/")
    return parsed._replace(path=path, query="", fragment="").geturl()
