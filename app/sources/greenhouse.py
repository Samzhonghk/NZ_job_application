from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

from app.sources.base import CompanySource, RawJob, SourceAdapter
from app.sources.http import fetch_json


class GreenhouseAdapter(SourceAdapter):
    source_type = "greenhouse"

    def detect(self, url: str) -> float:
        return 0.95 if "greenhouse.io" in url.lower() else 0.0

    def source_from_url(self, company_name: str, url: str) -> CompanySource | None:
        match = re.search(r"greenhouse\.io/([^/?#]+)", url, flags=re.IGNORECASE)
        if not match:
            return None
        token = match.group(1)
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        return CompanySource(company_name=company_name, source_type=self.source_type, identifier=token, url=api_url)

    def fetch_jobs(self, source: CompanySource) -> list[RawJob]:
        data = fetch_json(source.url)
        jobs = data.get("jobs", []) if isinstance(data, dict) else []
        return [_raw_job(item, source) for item in jobs if isinstance(item, dict)]


def _raw_job(item: dict[str, Any], source: CompanySource) -> RawJob:
    location = item.get("location") or {}
    location_name = location.get("name", "") if isinstance(location, dict) else str(location or "")
    absolute_url = str(item.get("absolute_url") or "")
    source_url = absolute_url or urljoin(source.url, str(item.get("id", "")))
    return RawJob(
        title=str(item.get("title") or ""),
        company_name=source.company_name,
        location=location_name,
        description=str(item.get("content") or ""),
        source=source.source_type,
        source_url=source_url,
        apply_url=absolute_url,
        external_id=str(item.get("id") or ""),
        raw_data={"adapter": source.source_type, "source_identifier": source.identifier, "job": item},
    )

