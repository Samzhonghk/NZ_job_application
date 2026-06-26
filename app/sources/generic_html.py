from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from app.sources.base import CompanySource, RawJob, SourceAdapter


DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; NZITJobApplicationAutomation/0.1)"
JOB_LINK_KEYWORDS = [
    "job",
    "jobs",
    "career",
    "careers",
    "role",
    "roles",
    "position",
    "positions",
    "vacancy",
    "vacancies",
    "opening",
    "openings",
    "apply",
]
NON_JOB_LINK_KEYWORDS = [
    "privacy",
    "terms",
    "cookie",
    "benefit",
    "culture",
    "life-at",
    "people",
    "blog",
    "news",
    "event",
    "userhome",
    "services",
    "solutions",
    "insights",
    "about",
]
ROLE_TITLE_PATTERN = re.compile(
    r"\b("
    r"software|data|cloud|devops|security|ai|machine learning|"
    r"engineer|developer|analyst|architect|product manager|"
    r"qa|tester|sre|platform|full stack|frontend|backend"
    r")\b",
    flags=re.IGNORECASE,
)
CATEGORY_TITLE_PATTERN = re.compile(
    r"\b(careers?|job opportunities|services? & solutions?|solutions?|powered by|home)\b",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class FetchResult:
    url: str
    final_url: str
    html: str
    status_code: int | None = None


class GenericHtmlAdapter(SourceAdapter):
    source_type = "generic_html"

    def detect(self, url: str) -> float:
        return 0.0

    def source_from_url(self, company_name: str, url: str) -> CompanySource | None:
        return CompanySource(
            company_name=company_name,
            source_type=self.source_type,
            identifier=company_name,
            url=url,
        )

    def fetch_jobs(self, source: CompanySource) -> list[RawJob]:
        result = fetch_html(source.url)
        job_links = extract_job_links(result.html, result.final_url)
        if not job_links and _looks_like_single_job_page(result.html):
            return [_with_company(parse_job_from_html(result.html, result.final_url), source.company_name)]

        jobs: list[RawJob] = []
        for link in job_links[:25]:
            try:
                raw_job = _with_company(fetch_and_parse_job(link), source.company_name)
                if _raw_job_looks_like_job(raw_job):
                    jobs.append(raw_job)
            except Exception:
                continue
        return jobs


def fetch_html(url: str, timeout_seconds: int = 20) -> FetchResult:
    if url.startswith("file://"):
        parsed_path = urlparse(url).path
        if re.match(r"^/[A-Za-z]:", parsed_path):
            parsed_path = parsed_path[1:]
        path = Path(parsed_path)
        html = path.read_text(encoding="utf-8")
        return FetchResult(url=url, final_url=url, html=html, status_code=None)

    request = Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    with urlopen(request, timeout=timeout_seconds) as response:
        body = response.read()
        encoding = response.headers.get_content_charset() or "utf-8"
        return FetchResult(
            url=url,
            final_url=response.geturl(),
            html=body.decode(encoding, errors="replace"),
            status_code=getattr(response, "status", None),
        )


def parse_job_from_html(html: str, source_url: str) -> RawJob:
    parser = _JobHTMLParser()
    parser.feed(html)

    json_ld_job = _find_json_ld_job_posting(parser.json_ld_blocks)
    if json_ld_job:
        return _raw_job_from_json_ld(json_ld_job, parser, source_url)

    title = _clean_text(
        parser.meta.get("og:title")
        or parser.meta.get("twitter:title")
        or parser.title
        or _domain_title(source_url)
    )
    description = _clean_text(
        parser.meta.get("description")
        or parser.meta.get("og:description")
        or parser.main_text
    )

    company_name = _guess_company_name(title, source_url)
    apply_url = _guess_apply_url(parser.links, source_url)

    return RawJob(
        title=title,
        company_name=company_name,
        location="",
        description=description,
        source="generic_html",
        source_url=source_url,
        apply_url=apply_url,
        raw_data={
            "parser": "generic_html",
            "meta": parser.meta,
            "fallback": True,
        },
    )


def fetch_and_parse_job(url: str, timeout_seconds: int = 20) -> RawJob:
    result = fetch_html(url, timeout_seconds=timeout_seconds)
    return parse_job_from_html(result.html, result.final_url)


def extract_job_links(html: str, source_url: str) -> list[str]:
    parser = _JobHTMLParser()
    parser.feed(html)
    candidates: list[tuple[int, str]] = []
    for href, label in parser.links:
        absolute_url = urljoin(source_url, href)
        score = _job_link_score(absolute_url, label)
        if score > 0:
            candidates.append((score, _without_fragment(absolute_url)))

    seen: set[str] = set()
    links: list[str] = []
    for _, link in sorted(candidates, key=lambda item: item[0], reverse=True):
        if link in seen:
            continue
        seen.add(link)
        links.append(link)
    return links


class _JobHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta: dict[str, str] = {}
        self.links: list[tuple[str, str]] = []
        self.json_ld_blocks: list[str] = []
        self._current_tag: str | None = None
        self._capture_json_ld = False
        self._text_parts: list[str] = []
        self._title_parts: list[str] = []
        self._json_ld_parts: list[str] = []
        self._skip_depth = 0

    @property
    def main_text(self) -> str:
        return _clean_text(" ".join(self._text_parts))[:5000]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        self._current_tag = tag.lower()

        if tag.lower() in {"script", "style", "noscript"}:
            self._skip_depth += 1

        if tag.lower() == "meta":
            key = ((
                attrs_dict.get("property")
                or attrs_dict.get("name")
                or attrs_dict.get("itemprop")
                or ""
            ).lower())
            content = attrs_dict.get("content", "")
            if key and content:
                self.meta[key] = _clean_text(content)

        if tag.lower() == "a":
            href = attrs_dict.get("href", "")
            if href:
                self.links.append((href, ""))

        if tag.lower() == "script" and attrs_dict.get("type", "").lower() == "application/ld+json":
            self._capture_json_ld = True
            self._json_ld_parts = []

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "title":
            self.title = _clean_text(" ".join(self._title_parts))
            self._title_parts = []

        if lower == "script" and self._capture_json_ld:
            block = "".join(self._json_ld_parts).strip()
            if block:
                self.json_ld_blocks.append(block)
            self._capture_json_ld = False
            self._json_ld_parts = []

        if lower in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1

        self._current_tag = None

    def handle_data(self, data: str) -> None:
        if self._capture_json_ld:
            self._json_ld_parts.append(data)
            return

        if self._skip_depth:
            return

        if self._current_tag == "title":
            self._title_parts.append(data)

        cleaned = _clean_text(data)
        if cleaned:
            self._text_parts.append(cleaned)
            if self._current_tag == "a" and self.links:
                href, existing_label = self.links[-1]
                self.links[-1] = (href, _clean_text(f"{existing_label} {cleaned}"))


def _find_json_ld_job_posting(blocks: list[str]) -> dict[str, Any] | None:
    for block in blocks:
        for item in _loads_json_ld_items(block):
            found = _find_job_posting_item(item)
            if found:
                return found
    return None


def _loads_json_ld_items(block: str) -> list[Any]:
    try:
        data = json.loads(block)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else [data]


def _find_job_posting_item(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    item_type = item.get("@type")
    if _type_matches_job_posting(item_type):
        return item
    graph = item.get("@graph")
    if isinstance(graph, list):
        for graph_item in graph:
            found = _find_job_posting_item(graph_item)
            if found:
                return found
    return None


def _type_matches_job_posting(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() == "jobposting"
    if isinstance(value, list):
        return any(_type_matches_job_posting(item) for item in value)
    return False


def _raw_job_from_json_ld(data: dict[str, Any], parser: _JobHTMLParser, source_url: str) -> RawJob:
    hiring_org = data.get("hiringOrganization") or {}
    if isinstance(hiring_org, list):
        hiring_org = hiring_org[0] if hiring_org else {}

    location = _format_location(data.get("jobLocation"))
    salary_text = _format_salary(data.get("baseSalary"))

    apply_url = _string(data.get("url")) or _guess_apply_url(parser.links, source_url)
    title = _clean_text(_string(data.get("title")) or parser.title or _domain_title(source_url))
    company_name = _clean_text(
        _string(hiring_org.get("name")) if isinstance(hiring_org, dict) else ""
    )

    return RawJob(
        title=title,
        company_name=company_name or _guess_company_name(title, source_url),
        location=location,
        description=_clean_html(_string(data.get("description"))),
        source="json_ld_job_posting",
        source_url=source_url,
        apply_url=urljoin(source_url, apply_url) if apply_url else "",
        external_id=_string(data.get("identifier")),
        employment_type=_string(data.get("employmentType")),
        salary_text=salary_text,
        posted_at=_string(data.get("datePosted")),
        raw_data={"parser": "json_ld_job_posting", "json_ld": data},
    )


def _format_location(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(filter(None, (_format_location(item) for item in value)))
    if not isinstance(value, dict):
        return _clean_text(_string(value))

    address = value.get("address") or {}
    if isinstance(address, dict):
        parts = [
            address.get("addressLocality"),
            address.get("addressRegion"),
            address.get("addressCountry"),
        ]
        return ", ".join(_clean_text(_string(part)) for part in parts if _string(part))
    return _clean_text(_string(address))


def _format_salary(value: Any) -> str:
    if not isinstance(value, dict):
        return _clean_text(_string(value))
    currency = _string(value.get("currency"))
    amount = value.get("value")
    if isinstance(amount, dict):
        min_value = _string(amount.get("minValue"))
        max_value = _string(amount.get("maxValue"))
        unit = _string(amount.get("unitText"))
        if min_value and max_value:
            return _clean_text(f"{currency} {min_value}-{max_value} {unit}")
        return _clean_text(f"{currency} {_string(amount.get('value'))} {unit}")
    return _clean_text(f"{currency} {_string(amount)}")


def _guess_apply_url(links: list[tuple[str, str]], source_url: str) -> str:
    for href, label in links:
        candidate = f"{href} {label}".lower()
        if "apply" in candidate or "application" in candidate:
            return urljoin(source_url, href)
    return ""


def _job_link_score(url: str, label: str) -> int:
    lower = f"{url} {label}".lower()
    if any(keyword in lower for keyword in NON_JOB_LINK_KEYWORDS):
        return 0

    score = 0
    for keyword in JOB_LINK_KEYWORDS:
        if keyword in lower:
            score += 2
    if re.search(r"/(?:jobs?|careers?|roles?|positions?)/[^/?#]+", lower):
        score += 5
    if re.search(r"(software|engineer|developer|data|cloud|devops|security|analyst|product)", lower):
        score += 4
    return score


def _raw_job_looks_like_job(raw_job: RawJob) -> bool:
    if raw_job.raw_data.get("parser") == "json_ld_job_posting":
        return True

    combined = f"{raw_job.title} {raw_job.source_url} {raw_job.apply_url}".lower()
    if any(keyword in combined for keyword in NON_JOB_LINK_KEYWORDS):
        return False
    if CATEGORY_TITLE_PATTERN.search(raw_job.title):
        return False
    if not ROLE_TITLE_PATTERN.search(raw_job.title):
        return False
    return bool(raw_job.apply_url or len(raw_job.description) >= 40)


def _without_fragment(url: str) -> str:
    return urlparse(url)._replace(fragment="").geturl()


def _looks_like_single_job_page(html: str) -> bool:
    lowered = html.lower()
    return "jobposting" in lowered or ("apply" in lowered and "responsibilities" in lowered)


def _with_company(raw_job: RawJob, company_name: str) -> RawJob:
    if raw_job.company_name and raw_job.company_name != _domain_title(raw_job.source_url):
        return raw_job
    return RawJob(
        title=raw_job.title,
        company_name=company_name,
        location=raw_job.location,
        description=raw_job.description,
        source=raw_job.source,
        source_url=raw_job.source_url,
        apply_url=raw_job.apply_url,
        external_id=raw_job.external_id,
        employment_type=raw_job.employment_type,
        salary_text=raw_job.salary_text,
        posted_at=raw_job.posted_at,
        raw_data=raw_job.raw_data,
    )


def _guess_company_name(title: str, source_url: str) -> str:
    parsed = urlparse(source_url)
    if parsed.netloc.lower() == "jobs.smartrecruiters.com":
        parts = [part for part in parsed.path.split("/") if part]
        if parts:
            return parts[0]

    for separator in [" | ", " - ", " at "]:
        if separator in title:
            parts = [part.strip() for part in title.split(separator) if part.strip()]
            if len(parts) >= 2:
                return parts[-1]
    return _domain_title(source_url)


def _domain_title(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host.split(".")[0].replace("-", " ").title() if host else "Unknown"


def _clean_html(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return _clean_text(unescape(without_tags))


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value or "")).strip()


def _string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True)
    return str(value)
