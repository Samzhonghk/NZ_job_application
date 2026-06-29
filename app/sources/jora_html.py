from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin

from app.sources.base import RawJob


JORA_BASE_URL = "https://nz.jora.com"

JOB_TITLE_HINTS = [
    "engineer",
    "developer",
    "analyst",
    "architect",
    "consultant",
    "data",
    "software",
    "cloud",
    "security",
    "devops",
    "qa",
    "tester",
    "product",
    "manager",
    "lead",
    "specialist",
    "ai",
]

NOISE_TEXT = {
    "jora",
    "search",
    "matches",
    "saved jobs",
    "applied jobs",
    "search jobs",
    "save job",
    "open in new tab",
    "view or apply for job",
    "reset all filters",
}


@dataclass(frozen=True)
class JoraHtmlParseResult:
    path: Path
    jobs: list[RawJob]


@dataclass
class _Anchor:
    href: str
    text: str
    line_index: int


class _JoraHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self.anchors: list[_Anchor] = []
        self._current_href = ""
        self._current_text: list[str] = []
        self._current_start_index = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attr_map = {name.lower(): value or "" for name, value in attrs}
        self._current_href = attr_map.get("href", "")
        self._current_text = []
        self._current_start_index = len(self.lines)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._current_href:
            return
        text = _clean_text(" ".join(self._current_text))
        if text:
            self.anchors.append(_Anchor(self._current_href, text, self._current_start_index))
        self._current_href = ""
        self._current_text = []

    def handle_data(self, data: str) -> None:
        text = _clean_text(data)
        if not text:
            return
        self.lines.append(text)
        if self._current_href:
            self._current_text.append(text)


def parse_jora_html_file(path: str | Path) -> JoraHtmlParseResult:
    html_path = Path(path)
    parser = _JoraHtmlParser()
    parser.feed(html_path.read_text(encoding="utf-8", errors="ignore"))

    job_anchors = [anchor for anchor in parser.anchors if _looks_like_job_anchor(anchor)]
    jobs: list[RawJob] = []
    seen_urls: set[str] = set()
    for index, anchor in enumerate(job_anchors):
        source_url = _normalise_url(anchor.href)
        if source_url in seen_urls:
            continue
        next_anchor_index = job_anchors[index + 1].line_index if index + 1 < len(job_anchors) else None
        raw_job = _raw_job_from_anchor(anchor, parser.lines, html_path, source_url, next_anchor_index)
        if not raw_job.company_name:
            continue
        seen_urls.add(source_url)
        jobs.append(raw_job)

    return JoraHtmlParseResult(path=html_path, jobs=jobs)


def parse_jora_html_folder(path: str | Path) -> list[JoraHtmlParseResult]:
    folder = Path(path)
    files = sorted(
        file
        for pattern in ("*.html", "*.htm")
        for file in folder.glob(pattern)
        if file.is_file()
    )
    return [parse_jora_html_file(file) for file in files]


def _raw_job_from_anchor(
    anchor: _Anchor,
    lines: list[str],
    path: Path,
    source_url: str,
    next_anchor_index: int | None,
) -> RawJob:
    title = _clean_title(anchor.text)
    context = _context_after_anchor(anchor, lines, next_anchor_index)
    company = _pick_company(context)
    location = _pick_location(context, company)
    description = _pick_description(context)

    return RawJob(
        title=title,
        company_name=company,
        location=location,
        description=description,
        source="jora_html",
        source_url=source_url,
        apply_url=source_url,
        external_id=_external_id(source_url),
        raw_data={
            "html_file": str(path),
            "anchor_text": anchor.text,
            "context": context[:10],
        },
    )


def _context_after_anchor(anchor: _Anchor, lines: list[str], next_anchor_index: int | None) -> list[str]:
    context: list[str] = []
    end_index = next_anchor_index if next_anchor_index is not None else anchor.line_index + 16
    for line in lines[anchor.line_index + 1 : end_index]:
        cleaned = _clean_text(line)
        if not cleaned:
            continue
        if cleaned == anchor.text:
            continue
        if cleaned.lower() in NOISE_TEXT:
            continue
        context.append(cleaned)
    return context


def _pick_company(context: list[str]) -> str:
    for line in context:
        if _looks_like_metadata(line) or _looks_like_bullet(line):
            continue
        if _looks_like_location_only(line) and not re.search(r"\s+[–-]\s+", line):
            continue
        return _clean_company(line)
    return ""


def _pick_location(context: list[str], company: str) -> str:
    for line in context:
        if company and line.strip().lower() == company.strip().lower():
            continue
        if _looks_like_description(line):
            continue
        if _looks_like_location(line):
            return _clean_location(line, company)
    return ""


def _pick_description(context: list[str]) -> str:
    description_lines = [
        line
        for line in context
        if _looks_like_bullet(line) or _looks_like_description(line)
    ]
    return "\n".join(description_lines[:5])


def _looks_like_job_anchor(anchor: _Anchor) -> bool:
    text = _clean_title(anchor.text)
    lower_text = text.lower()
    href = anchor.href.lower()
    if not text or lower_text in NOISE_TEXT:
        return False
    if len(text) < 4 or len(text) > 140:
        return False
    if any(noise in href for noise in ["saved", "applied", "login", "signup"]):
        return False
    normalised_href = _normalise_url(anchor.href).lower()
    if "/job/" not in normalised_href:
        return False
    return any(hint in lower_text for hint in JOB_TITLE_HINTS)


def _looks_like_metadata(text: str) -> bool:
    lower = text.lower()
    return any(
        hint in lower
        for hint in [
            "new to you",
            "posted",
            "recently posted",
            "full time",
            "part time",
            "contract",
            "hybrid",
            "remote",
            "from seek.co.nz",
            "from jora",
        ]
    )


def _looks_like_location(text: str) -> bool:
    lower = text.lower()
    return any(
        hint in lower
        for hint in [
            "auckland",
            "wellington",
            "christchurch",
            "hamilton",
            "dunedin",
            "tauranga",
            "new zealand",
            "north island",
            "south island",
            "remote",
            "hybrid",
            "cbd",
        ]
    )


def _looks_like_location_only(text: str) -> bool:
    lower = text.lower()
    if lower in {
        "new zealand",
        "north island",
        "south island",
        "auckland",
        "wellington",
        "christchurch",
        "hamilton",
        "dunedin",
        "tauranga",
        "rotorua",
        "whangarei",
        "invercargill",
        "west coast",
        "north shore",
    }:
        return True
    if "," not in lower and " island" not in lower and "cbd" not in lower:
        return False
    return any(
        hint in lower
        for hint in [
            "auckland",
            "wellington",
            "christchurch",
            "hamilton",
            "dunedin",
            "tauranga",
            "cbd",
            "north shore",
            "west coast",
            "newstead",
            "rotorua",
            "whangarei",
            "invercargill",
        ]
    )


def _looks_like_bullet(text: str) -> bool:
    return text.startswith(("-", "*", chr(8226)))


def _looks_like_description(text: str) -> bool:
    lower = text.lower()
    return any(
        hint in lower
        for hint in [
            "work with",
            "work across",
            "build",
            "develop",
            "deliver",
            "support",
            "design",
            "lead",
            "join",
            "you'll",
            "you will",
            "what will you do",
        ]
    )


def _external_id(source_url: str) -> str:
    match = re.search(r"/job/([^/?#]+)", source_url)
    if match:
        return match.group(1)[:255]
    return hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:16]


def _normalise_url(value: str) -> str:
    return urljoin(JORA_BASE_URL, html.unescape(unquote(value.strip())))


def _clean_company(value: str) -> str:
    return re.split(r"\s+[–-]\s+", value, maxsplit=1)[0].strip()


def _clean_location(value: str, company: str) -> str:
    text = value.strip()
    if company and text.lower().startswith(company.lower()):
        text = re.sub(rf"^{re.escape(company)}\s+[–-]\s+", "", text, flags=re.IGNORECASE).strip()
    return text


def _clean_title(value: str) -> str:
    return _clean_text(value).strip(" -|")


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()
