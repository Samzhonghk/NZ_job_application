from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.applications.materials import prepare_application
from app.config.schemas import ProjectConfig
from app.dashboard.render import render_daily_digest, render_dashboard
from app.db.importers import import_companies
from app.db.models import Company, Job
from app.jobs.scorer import apply_score
from app.sources.scanner import scan_company


CORE_RECOMMENDED_ROLE_GROUPS = [
    "software",
    "data",
    "data_analyst",
    "business_analyst",
    "ai",
    "cloud",
    "security",
    "qa",
    "product",
]


@dataclass(frozen=True)
class QueueItem:
    job_id: int
    title: str
    company_name: str
    role_group: str
    match_score: float | None
    status: str
    source_url: str
    open_url: str


@dataclass(frozen=True)
class BatchPrepareResult:
    job_id: int
    application_id: int
    created: bool
    title: str
    company_name: str


@dataclass(frozen=True)
class DailyScanResult:
    companies_created: int
    companies_updated: int
    companies_scanned: int
    jobs_found: int
    new_jobs: int
    jobs_scored: int
    recommended_count: int
    dashboard_path: Path
    digest: str


def scan_companies_by_priority(
    session: Session,
    config: ProjectConfig,
    max_priority: int = 1,
    limit: int | None = None,
) -> tuple[int, int, int]:
    query = (
        select(Company)
        .where(Company.active.is_(True), Company.priority <= max_priority)
        .order_by(Company.priority, Company.company_name)
    )
    companies = list(session.scalars(query).all())
    if limit is not None:
        companies = companies[:limit]

    scanned = 0
    found_total = 0
    created_total = 0
    for company in companies:
        found, created = scan_company(company, session, config)
        if found or created:
            scanned += 1
        found_total += found
        created_total += created
    return scanned, found_total, created_total


def run_daily_scan(
    session: Session,
    config: ProjectConfig,
    max_priority: int = 2,
    limit: int | None = 60,
    minimum_score: float = 55.0,
    dashboard_output: Path | None = None,
    digest_limit: int = 10,
) -> DailyScanResult:
    companies_created, companies_updated = import_companies(config, session)
    companies_scanned, jobs_found, new_jobs = scan_companies_by_priority(
        session,
        config,
        max_priority=max_priority,
        limit=limit,
    )

    jobs = session.scalars(select(Job)).all()
    for job in jobs:
        apply_score(job, config)
    session.commit()

    dashboard_path = render_dashboard(
        session,
        dashboard_output or config.paths.root / "data" / "generated" / "dashboard.html",
        minimum_score=minimum_score,
    )
    digest = render_daily_digest(session, minimum_score=minimum_score, limit=digest_limit)
    recommended_count = len(
        recommended_queue(
            session,
            minimum_score=minimum_score,
            limit=1000,
            include_prepared=True,
        )
    )

    return DailyScanResult(
        companies_created=companies_created,
        companies_updated=companies_updated,
        companies_scanned=companies_scanned,
        jobs_found=jobs_found,
        new_jobs=new_jobs,
        jobs_scored=len(jobs),
        recommended_count=recommended_count,
        dashboard_path=dashboard_path,
        digest=digest,
    )


def recommended_queue(
    session: Session,
    minimum_score: float = 55.0,
    limit: int = 20,
    include_prepared: bool = False,
    role_groups: list[str] | None = None,
) -> list[QueueItem]:
    query = select(Job).where(Job.is_it_related.is_(True))
    query = query.where(Job.match_score.is_not(None), Job.match_score >= minimum_score)
    query = query.where(Job.status.not_in(["ignored", "archived", "superseded_duplicate"]))
    query = query.where(Job.role_group.in_(role_groups or CORE_RECOMMENDED_ROLE_GROUPS))
    if not include_prepared:
        query = query.where(Job.status != "prepared")
    query = query.order_by(Job.match_score.desc(), Job.discovered_at.desc()).limit(limit)
    return [_queue_item(job) for job in session.scalars(query).all()]


def prepare_jobs_batch(
    session: Session,
    config: ProjectConfig,
    job_ids: list[int],
) -> list[BatchPrepareResult]:
    results: list[BatchPrepareResult] = []
    for job_id in job_ids:
        job = session.get(Job, job_id)
        if job is None:
            continue
        application, created = prepare_application(job, config, session)
        job.status = "prepared"
        session.commit()
        results.append(
            BatchPrepareResult(
                job_id=job.id,
                application_id=application.id,
                created=created,
                title=job.title,
                company_name=job.company_name,
            )
        )
    return results


def mark_job_status(session: Session, job_id: int, status: str) -> Job | None:
    job = session.get(Job, job_id)
    if job is None:
        return None
    job.status = status
    session.commit()
    session.refresh(job)
    return job


def _queue_item(job: Job) -> QueueItem:
    open_url = job.apply_url or job.source_url
    return QueueItem(
        job_id=job.id,
        title=job.title,
        company_name=job.company_name,
        role_group=job.role_group,
        match_score=job.match_score,
        status=job.status,
        source_url=job.source_url,
        open_url=open_url,
    )
