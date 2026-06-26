from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

from app.sources.base import CompanySource, RawJob, SourceAdapter
from app.sources.http import fetch_json


class SmartRecruitersAdapter(SourceAdapter):
    source_type = "smartrecruiters"

    def detect(self, url: str) -> float:
        return 0.95 if "smartrecruiters.com" in url.lower() else 0.0

    def source_from_url(self, company_name: str, url: str) -> CompanySource | None:
        match = re.search(r"smartrecruiters\.com/([^/?#]+)", url, flags=re.IGNORECASE)
        if not match:
            return None
        company = match.group(1)
        api_url = f"https://api.smartrecruiters.com/v1/companies/{company}/postings"
        return CompanySource(company_name=company_name, source_type=self.source_type, identifier=company, url=api_url)

    def fetch_jobs(self, source: CompanySource) -> list[RawJob]:
        data = fetch_json(source.url)
        jobs = data.get("content", []) if isinstance(data, dict) else []
        return [_raw_job(item, source) for item in jobs if isinstance(item, dict)]


def _raw_job(item: dict[str, Any], source: CompanySource) -> RawJob:
    location = item.get("location") or {}
    location_text = location.get("city", "") if isinstance(location, dict) else ""
    if isinstance(location, dict) and location.get("country"):
        location_text = ", ".join(part for part in [location_text, str(location.get("country"))] if part)

    job_id = str(item.get("id") or item.get("ref") or "")
    ref = str(item.get("ref") or job_id)
    job_url = str(item.get("postingUrl") or item.get("url") or "")
    if not job_url and job_id:
        company_token = _company_token(source)
        job_url = f"https://jobs.smartrecruiters.com/{company_token}/{job_id}-{_slug(str(item.get('name') or item.get('title') or 'job'))}"

    return RawJob(
        title=str(item.get("name") or item.get("title") or ""),
        company_name=source.company_name,
        location=location_text,
        description=str(item.get("jobAd") or item.get("description") or ""),
        source=source.source_type,
        source_url=job_url or source.url,
        apply_url=job_url,
        external_id=job_id or ref,
        posted_at=str(item.get("releasedDate") or item.get("createdOn") or ""),
        raw_data={"adapter": source.source_type, "source_identifier": source.identifier, "job": item},
    )


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return quote(cleaned or "job")


def _company_token(source: CompanySource) -> str:
    match = re.search(r"/companies/([^/?#]+)/postings", source.url, flags=re.IGNORECASE)
    if match:
        return quote(match.group(1), safe="")
    return quote(source.identifier.strip().replace(" ", ""), safe="")
