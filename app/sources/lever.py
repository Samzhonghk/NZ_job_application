from __future__ import annotations

import re
from typing import Any

from app.sources.base import CompanySource, RawJob, SourceAdapter
from app.sources.http import fetch_json


class LeverAdapter(SourceAdapter):
    source_type = "lever"

    def detect(self, url: str) -> float:
        return 0.95 if "lever.co" in url.lower() else 0.0

    def source_from_url(self, company_name: str, url: str) -> CompanySource | None:
        match = re.search(r"jobs\.lever\.co/([^/?#]+)", url, flags=re.IGNORECASE)
        if not match:
            return None
        company = match.group(1)
        api_url = f"https://api.lever.co/v0/postings/{company}?mode=json"
        return CompanySource(company_name=company_name, source_type=self.source_type, identifier=company, url=api_url)

    def fetch_jobs(self, source: CompanySource) -> list[RawJob]:
        data = fetch_json(source.url)
        jobs = data if isinstance(data, list) else []
        return [_raw_job(item, source) for item in jobs if isinstance(item, dict)]


def _raw_job(item: dict[str, Any], source: CompanySource) -> RawJob:
    categories = item.get("categories") or {}
    location = categories.get("location", "") if isinstance(categories, dict) else ""
    commitment = categories.get("commitment", "") if isinstance(categories, dict) else ""
    lists = item.get("lists") or []
    description_parts = [str(item.get("descriptionPlain") or item.get("description") or "")]
    if isinstance(lists, list):
        for block in lists:
            if isinstance(block, dict):
                description_parts.append(str(block.get("text") or ""))
                content = block.get("content") or ""
                if isinstance(content, str):
                    description_parts.append(content)

    hosted_url = str(item.get("hostedUrl") or item.get("applyUrl") or "")
    return RawJob(
        title=str(item.get("text") or ""),
        company_name=source.company_name,
        location=str(location or ""),
        description=" ".join(part for part in description_parts if part),
        source=source.source_type,
        source_url=hosted_url or str(item.get("id") or source.url),
        apply_url=str(item.get("applyUrl") or hosted_url),
        external_id=str(item.get("id") or ""),
        employment_type=str(commitment or ""),
        raw_data={"adapter": source.source_type, "source_identifier": source.identifier, "job": item},
    )

