from __future__ import annotations

from datetime import timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.schemas import ProjectConfig
from app.db.job_repository import upsert_job_from_raw
from app.db.models import Company, SourceScan, utc_now
from app.sources.base import CompanySource
from app.sources.registry import adapter_for_source_type, detect_company_source


def scan_company(
    company: Company,
    session: Session,
    config: ProjectConfig,
    source_override: CompanySource | None = None,
) -> tuple[int, int]:
    source = source_override or _source_from_company(company)
    if source is None:
        _record_scan(session, company, "unknown", "skipped", 0, 0, "No supported ATS source detected.")
        return 0, 0

    adapter = adapter_for_source_type(source.source_type)
    if adapter is None:
        _record_scan(session, company, source.source_type, "skipped", 0, 0, "No adapter registered.")
        return 0, 0

    scan = SourceScan(company_id=company.id, source_type=source.source_type, status="started")
    session.add(scan)
    session.commit()

    try:
        raw_jobs = adapter.fetch_jobs(source)
        created_count = 0
        for raw_job in raw_jobs:
            _, created = upsert_job_from_raw(raw_job, session, config=config)
            if created:
                created_count += 1
        scan.jobs_found_count = len(raw_jobs)
        scan.new_jobs_count = created_count
        scan.status = "completed"
        company.last_checked_at = utc_now()
        session.commit()
        return len(raw_jobs), created_count
    except Exception as exc:
        scan.status = "failed"
        scan.error_message = str(exc)
        scan.finished_at = utc_now()
        session.commit()
        raise
    finally:
        if scan.finished_at is None:
            scan.finished_at = utc_now()
            session.commit()


def find_company_by_name(session: Session, company_name: str) -> Company | None:
    return session.scalar(select(Company).where(Company.company_name == company_name))


def _source_from_company(company: Company) -> CompanySource | None:
    if company.ats_type and company.ats_feed_url:
        return CompanySource(
            company_name=company.company_name,
            source_type=company.ats_type,
            identifier=company.company_name,
            url=company.ats_feed_url,
        )
    return detect_company_source(company.company_name, company.career_url or company.website)


def _record_scan(
    session: Session,
    company: Company,
    source_type: str,
    status: str,
    jobs_found_count: int,
    new_jobs_count: int,
    error_message: str = "",
) -> None:
    now = utc_now().astimezone(timezone.utc)
    session.add(
        SourceScan(
            company_id=company.id,
            source_type=source_type,
            started_at=now,
            finished_at=now,
            status=status,
            jobs_found_count=jobs_found_count,
            new_jobs_count=new_jobs_count,
            error_message=error_message,
        )
    )
    session.commit()
