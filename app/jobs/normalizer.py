from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.sources.base import RawJob


def normalise_raw_job(raw_job: RawJob) -> dict[str, Any]:
    return {
        "external_id": raw_job.external_id,
        "title": _required(raw_job.title, "title"),
        "company_name": raw_job.company_name,
        "location": raw_job.location,
        "employment_type": raw_job.employment_type,
        "salary_text": raw_job.salary_text,
        "description": raw_job.description,
        "source": raw_job.source,
        "source_url": _required(raw_job.source_url, "source_url"),
        "apply_url": raw_job.apply_url,
        "posted_at": _parse_date(raw_job.posted_at),
        "raw_data": json.dumps(raw_job.raw_data, ensure_ascii=True),
    }


def _required(value: str, field_name: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError(f"Job field {field_name!r} is required")
    return cleaned


def _parse_date(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    normalised = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalised)
    except ValueError:
        return None

