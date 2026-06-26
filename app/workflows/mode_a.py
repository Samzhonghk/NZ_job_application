from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.applications.materials import prepare_application
from app.browser.autofill import plan_autofill_for_file, record_autofill_plan, summarise_plan
from app.config.schemas import ProjectConfig
from app.db.job_repository import upsert_job_from_raw
from app.sources.generic_html import fetch_and_parse_job


@dataclass(frozen=True)
class ModeAResult:
    job_id: int
    application_id: int
    job_created: bool
    application_created: bool
    title: str
    company_name: str
    role_group: str
    match_score: float | None
    recommendation: str
    autofill_summary: dict[str, int] | None = None


def run_mode_a(
    job_url: str,
    config: ProjectConfig,
    session: Session,
    form_url: str | None = None,
    static_file_plan: bool = False,
    minimum_score: float = 55.0,
) -> ModeAResult:
    raw_job = fetch_and_parse_job(job_url)
    job, job_created = upsert_job_from_raw(raw_job, session, config=config)
    application, application_created = prepare_application(job, config, session)

    recommendation = _recommendation(job.match_score, job.is_it_related, minimum_score)
    autofill_summary = None
    if form_url:
        if not static_file_plan:
            raise ValueError("Mode A currently supports form_url only with static_file_plan=True.")
        plan = plan_autofill_for_file(form_url, config)
        record_autofill_plan(application, plan, session, mark_completed=True)
        autofill_summary = summarise_plan(plan)

    return ModeAResult(
        job_id=job.id,
        application_id=application.id,
        job_created=job_created,
        application_created=application_created,
        title=job.title,
        company_name=job.company_name,
        role_group=job.role_group,
        match_score=job.match_score,
        recommendation=recommendation,
        autofill_summary=autofill_summary,
    )


def _recommendation(score: float | None, is_it_related: bool, minimum_score: float) -> str:
    if not is_it_related:
        return "review: job was not classified as IT-related"
    if score is None:
        return "review: job has no match score"
    if score >= 85:
        return "strong_match"
    if score >= 70:
        return "good_match"
    if score >= minimum_score:
        return "possible_match"
    return "low_priority"

