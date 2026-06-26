from __future__ import annotations

from app.sources.base import CompanySource, SourceAdapter
from app.sources.generic_html import GenericHtmlAdapter
from app.sources.greenhouse import GreenhouseAdapter
from app.sources.lever import LeverAdapter
from app.sources.smartrecruiters import SmartRecruitersAdapter


ADAPTERS: list[SourceAdapter] = [
    GreenhouseAdapter(),
    LeverAdapter(),
    SmartRecruitersAdapter(),
    GenericHtmlAdapter(),
]


def detect_company_source(company_name: str, url: str) -> CompanySource | None:
    candidates: list[tuple[float, SourceAdapter]] = [
        (adapter.detect(url), adapter) for adapter in ADAPTERS
    ]
    confidence, adapter = max(candidates, key=lambda item: item[0])
    if confidence <= 0:
        return None
    source_from_url = getattr(adapter, "source_from_url", None)
    if source_from_url is None:
        return None
    return source_from_url(company_name, url)


def adapter_for_source_type(source_type: str) -> SourceAdapter | None:
    for adapter in ADAPTERS:
        if adapter.source_type == source_type:
            return adapter
    return None
