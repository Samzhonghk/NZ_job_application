from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RawJob:
    title: str
    company_name: str
    location: str
    description: str
    source: str
    source_url: str
    apply_url: str = ""
    external_id: str = ""
    employment_type: str = ""
    salary_text: str = ""
    posted_at: str = ""
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CompanySource:
    company_name: str
    source_type: str
    identifier: str
    url: str


class SourceAdapter:
    source_type: str

    def detect(self, url: str) -> float:
        raise NotImplementedError

    def fetch_jobs(self, source: CompanySource) -> list[RawJob]:
        raise NotImplementedError
