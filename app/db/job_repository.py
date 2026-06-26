from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Company, Job
from app.jobs.scorer import apply_score
from app.jobs.normalizer import normalise_raw_job
from app.sources.base import RawJob
from app.config.schemas import ProjectConfig


def upsert_job_from_raw(
    raw_job: RawJob,
    session: Session,
    config: ProjectConfig | None = None,
) -> tuple[Job, bool]:
    values = normalise_raw_job(raw_job)
    existing = session.scalar(
        select(Job).where(
            Job.source == values["source"],
            Job.source_url == values["source_url"],
        )
    )
    if existing is None:
        existing = session.scalar(select(Job).where(Job.source_url == values["source_url"]))
    if existing is None and values.get("external_id"):
        existing = session.scalar(
            select(Job).where(
                Job.source == values["source"],
                Job.external_id == values["external_id"],
            )
        )

    company = _find_company(session, values.get("company_name", ""))
    if company:
        values["company_id"] = company.id

    if existing is not None:
        for key, value in values.items():
            setattr(existing, key, value)
        if config is not None:
            apply_score(existing, config)
        session.commit()
        return existing, False

    job = Job(**values)
    if config is not None:
        apply_score(job, config)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job, True


def _find_company(session: Session, company_name: str) -> Company | None:
    name = (company_name or "").strip()
    if not name:
        return None
    return session.scalar(select(Company).where(Company.company_name == name))
