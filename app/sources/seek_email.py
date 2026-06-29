from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

from app.sources.base import RawJob


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
]

NOISE_TEXT = {
    "seek",
    "unsubscribe",
    "view job",
    "view jobs",
    "view all jobs",
    "apply now",
    "see job",
    "see jobs",
    "privacy policy",
}


@dataclass(frozen=True)
class SeekEmailParseResult:
    path: Path
    jobs: list[RawJob]


@dataclass
class _Anchor:
    href: str
    text: str
    line_index: int


class _EmailHtmlParser(HTMLParser):
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


def parse_seek_email_file(path: str | Path) -> SeekEmailParseResult:
    email_path = Path(path)
    content = _read_email_content(email_path)
    parser = _EmailHtmlParser()
    parser.feed(content)

    job_anchors = [anchor for anchor in parser.anchors if _looks_like_job_anchor(anchor)]

    jobs: list[RawJob] = []
    seen_urls: set[str] = set()
    for index, anchor in enumerate(job_anchors):
        source_url = _normalise_url(anchor.href)
        if source_url in seen_urls:
            continue
        seen_urls.add(source_url)
        next_anchor_index = job_anchors[index + 1].line_index if index + 1 < len(job_anchors) else None
        jobs.append(_raw_job_from_anchor(anchor, parser.lines, email_path, source_url, next_anchor_index))

    return SeekEmailParseResult(path=email_path, jobs=jobs)


def parse_seek_email_folder(path: str | Path) -> list[SeekEmailParseResult]:
    folder = Path(path)
    files = sorted(
        file
        for pattern in ("*.html", "*.htm", "*.eml")
        for file in folder.glob(pattern)
        if file.is_file()
    )
    return [parse_seek_email_file(file) for file in files]


def _read_email_content(path: Path) -> str:
    if path.suffix.lower() != ".eml":
        return path.read_text(encoding="utf-8", errors="ignore")

    message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    html_body = message.get_body(preferencelist=("html",))
    if html_body is not None:
        content = html_body.get_content()
        return content if isinstance(content, str) else content.decode("utf-8", errors="ignore")

    plain_body = message.get_body(preferencelist=("plain",))
    if plain_body is not None:
        content = plain_body.get_content()
        text = content if isinstance(content, str) else content.decode("utf-8", errors="ignore")
        return _plain_text_to_link_html(text)

    return ""


def _plain_text_to_link_html(text: str) -> str:
    escaped = html.escape(text)
    return re.sub(
        r"(https?://\S+)",
        lambda match: f'<a href="{match.group(1)}">{match.group(1)}</a>',
        escaped,
    )


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
    location = _pick_location(context)
    description = _pick_description(context)
    external_id = _external_id(source_url)

    return RawJob(
        title=title,
        company_name=company,
        location=location,
        description=description,
        source="seek_email",
        source_url=source_url,
        apply_url=source_url,
        external_id=external_id,
        raw_data={
            "email_file": str(path),
            "anchor_text": anchor.text,
            "context": context[:8],
        },
    )


def _context_after_anchor(anchor: _Anchor, lines: list[str], next_anchor_index: int | None) -> list[str]:
    context: list[str] = []
    end_index = next_anchor_index if next_anchor_index is not None else anchor.line_index + 10
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
        if _looks_like_bullet(line):
            continue
        return line
    return ""


def _pick_location(context: list[str]) -> str:
    for line in context[1:] if context else []:
        if _looks_like_location(line):
            return line
    return ""


def _pick_description(context: list[str]) -> str:
    description_lines = [
        line
        for line in context
        if _looks_like_bullet(line) or _looks_like_description(line)
    ]
    return "\n".join(description_lines[:4])


def _looks_like_job_anchor(anchor: _Anchor) -> bool:
    text = _clean_title(anchor.text)
    lower = text.lower()
    href = anchor.href.lower()
    if not text or lower in NOISE_TEXT:
        return False
    if len(text) < 4 or len(text) > 120:
        return False
    if "unsubscribe" in href or "privacy" in href:
        return False
    if not href.startswith(("http://", "https://")):
        return False
    if "seek" not in href and "seek" not in lower:
        return False
    return any(hint in lower for hint in JOB_TITLE_HINTS)


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
            "nz",
            "remote",
            "hybrid",
            "cbd",
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
            "work alongside",
            "bring",
            "build",
            "develop",
            "deliver",
            "support",
            "design",
            "lead",
            "join",
        ]
    )


def _external_id(source_url: str) -> str:
    match = re.search(r"/job/(\d+)", source_url)
    if match:
        return match.group(1)
    return hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:16]


def _normalise_url(value: str) -> str:
    return html.unescape(unquote(value.strip()))


def _clean_title(value: str) -> str:
    return _clean_text(value).strip(" -|")


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()
