from __future__ import annotations

import re
from dataclasses import dataclass
from html import escape
from pathlib import Path
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from app.config.schemas import ProjectConfig
from app.db.models import Company
from app.sources.base import CompanySource
from app.sources.registry import detect_company_source


LOGIN_REQUIRED_KEYWORDS = [
    "sign in",
    "sign-in",
    "login",
    "log in",
    "register",
    "create account",
    "myworkdayjobs",
    "workday",
]

CAREER_LINK_KEYWORDS = [
    "career",
    "careers",
    "jobs",
    "job",
    "join-us",
    "join us",
    "work-with-us",
    "vacancies",
    "open-roles",
    "positions",
]

COMMON_CAREER_PATHS = [
    "/careers",
    "/careers/",
    "/jobs",
    "/jobs/",
    "/about/careers",
    "/about/careers/",
    "/company/careers",
    "/company/careers/",
    "/join-us",
    "/join-us/",
    "/work-with-us",
    "/work-with-us/",
]


@dataclass(frozen=True)
class CareerUrlDiscoveryResult:
    company_name: str
    career_url: str
    confidence: str
    status: str
    evidence: list[str]
    error_message: str = ""


@dataclass(frozen=True)
class SourceDiscoveryResult:
    company_name: str
    checked_url: str
    source: CompanySource | None
    confidence: str
    status: str
    evidence: list[str]
    error_message: str = ""


def write_discovery_report(results: list[SourceDiscoveryResult], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_discovery_report(results), encoding="utf-8")
    return output_path


def write_discovery_html_report(results: list[SourceDiscoveryResult], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_discovery_html_report(results), encoding="utf-8")
    return output_path


def write_career_url_html_report(results: list[CareerUrlDiscoveryResult], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_career_url_html_report(results), encoding="utf-8")
    return output_path


def render_career_url_html_report(results: list[CareerUrlDiscoveryResult]) -> str:
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    summary_cards = "\n".join(
        f'<div class="metric"><strong>{count}</strong><span>{escape(status)}</span></div>'
        for status, count in sorted(counts.items())
    ) or '<div class="metric"><strong>0</strong><span>No companies checked</span></div>'
    rows = "\n".join(_career_result_html_row(result) for result in results)
    return _html_page(
        title="Career URL Discovery",
        description="Candidate company career websites discovered from configured websites and common paths.",
        summary_cards=summary_cards,
        table_head="<tr><th>Company</th><th>Status</th><th>Confidence</th><th>Career URL</th><th>Evidence</th></tr>",
        table_rows=rows,
    )


def render_discovery_report(results: list[SourceDiscoveryResult]) -> str:
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1

    lines = [
        "# Company Source Discovery Report",
        "",
        "## Summary",
        "",
    ]
    if results:
        for status, count in sorted(counts.items()):
            lines.append(f"- {status}: {count}")
    else:
        lines.append("- No companies checked.")

    lines.extend(
        [
            "",
            "## Suggested Actions",
            "",
            "- `supported_ats`: Review and write confirmed `ats_type` / `ats_feed_url` back to `nz_it_company_targets.yaml`.",
            "- `generic_html`: Manually inspect before using for scanning; first version may only support single job pages reliably.",
            "- `login_required`: Keep in manual workflow; use manual login plus `manual-assist`.",
            "- `fetch_failed` / `not_found`: Recheck the career URL or skip for now.",
            "",
            "## Results",
            "",
        ]
    )

    for result in results:
        lines.extend(_result_lines(result))

    return "\n".join(lines).rstrip() + "\n"


def render_discovery_html_report(results: list[SourceDiscoveryResult]) -> str:
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1

    summary_cards = "\n".join(
        f'<div class="metric"><strong>{count}</strong><span>{escape(status)}</span></div>'
        for status, count in sorted(counts.items())
    ) or '<div class="metric"><strong>0</strong><span>No companies checked</span></div>'
    rows = "\n".join(_result_html_row(result) for result in results)

    return _html_page(
        title="Company Source Discovery",
        description="Suggested ATS sources for company career pages. Suggestions require confirmation before writing to YAML.",
        summary_cards=summary_cards,
        table_head="""<tr>
          <th>Company</th>
          <th>Status</th>
          <th>Confidence</th>
          <th>Checked URL</th>
          <th>ATS Type</th>
          <th>ATS Feed URL</th>
          <th>Evidence</th>
        </tr>""",
        table_rows=rows,
    )


def _html_page(
    title: str,
    description: str,
    summary_cards: str,
    table_head: str,
    table_rows: str,
) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f8fa;
      --surface: #ffffff;
      --text: #17202a;
      --muted: #5f6b7a;
      --border: #d8dee7;
      --accent: #176b87;
      --soft: #e7f4f7;
      --warning: #8a5a00;
      --warning-soft: #fff4d6;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--text);
      font-size: 14px;
      line-height: 1.45;
    }}
    header {{
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 20px 28px;
    }}
    h1 {{ margin: 0 0 6px; font-size: 24px; letter-spacing: 0; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 24px; }}
    .meta {{ color: var(--muted); margin: 0; }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }}
    .metric {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 14px;
    }}
    .metric strong {{ display: block; font-size: 22px; margin-bottom: 4px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
    }}
    th, td {{
      text-align: left;
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      background: #fbfcfd;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    .status {{
      display: inline-block;
      border-radius: 999px;
      padding: 2px 8px;
      background: var(--warning-soft);
      color: var(--warning);
      white-space: nowrap;
    }}
    .confidence {{
      display: inline-block;
      border-radius: 999px;
      padding: 2px 8px;
      background: var(--soft);
      color: var(--accent);
      white-space: nowrap;
    }}
    code {{ white-space: normal; word-break: break-word; }}
    a {{ color: var(--accent); }}
  </style>
</head>
<body>
  <header>
    <h1>{escape(title)}</h1>
    <p class="meta">{escape(description)}</p>
  </header>
  <main>
    <div class="summary">{summary_cards}</div>
    <table>
      <thead>
        {table_head}
      </thead>
      <tbody>{table_rows}</tbody>
    </table>
  </main>
</body>
</html>
"""


def _result_lines(result: SourceDiscoveryResult) -> list[str]:
    source_type = result.source.source_type if result.source else "none"
    source_url = result.source.url if result.source else "none"
    lines = [
        f"### {result.company_name}",
        "",
        f"- Status: `{result.status}`",
        f"- Confidence: `{result.confidence}`",
        f"- Checked URL: {result.checked_url or 'none'}",
        f"- Suggested ats_type: `{source_type}`",
        f"- Suggested ats_feed_url: {source_url}",
    ]
    if result.evidence:
        lines.append("- Evidence:")
        for item in result.evidence:
            lines.append(f"  - {item}")
    if result.error_message:
        lines.append(f"- Error: `{result.error_message}`")
    lines.append("")
    return lines


def _result_html_row(result: SourceDiscoveryResult) -> str:
    source_type = result.source.source_type if result.source else "none"
    source_url = result.source.url if result.source else "none"
    evidence = "<br>".join(escape(item) for item in result.evidence) or ""
    checked_url = escape(result.checked_url or "none")
    checked_cell = (
        f'<a href="{checked_url}">{checked_url}</a>'
        if result.checked_url.startswith(("http://", "https://"))
        else checked_url
    )
    source_url_escaped = escape(source_url)
    source_cell = (
        f'<a href="{source_url_escaped}">{source_url_escaped}</a>'
        if source_url.startswith(("http://", "https://"))
        else source_url_escaped
    )
    return f"""<tr>
  <td>{escape(result.company_name)}</td>
  <td><span class="status">{escape(result.status)}</span></td>
  <td><span class="confidence">{escape(result.confidence)}</span></td>
  <td>{checked_cell}</td>
  <td><code>{escape(source_type)}</code></td>
  <td>{source_cell}</td>
  <td>{evidence}</td>
</tr>"""


def _career_result_html_row(result: CareerUrlDiscoveryResult) -> str:
    evidence = "<br>".join(escape(item) for item in result.evidence) or ""
    url = escape(result.career_url or "none")
    url_cell = (
        f'<a href="{url}">{url}</a>'
        if result.career_url.startswith(("http://", "https://"))
        else url
    )
    return f"""<tr>
  <td>{escape(result.company_name)}</td>
  <td><span class="status">{escape(result.status)}</span></td>
  <td><span class="confidence">{escape(result.confidence)}</span></td>
  <td>{url_cell}</td>
  <td>{evidence}</td>
</tr>"""


def discover_company_source(company: Company, config: ProjectConfig) -> SourceDiscoveryResult:
    if company.ats_type and company.ats_feed_url:
        return SourceDiscoveryResult(
            company_name=company.company_name,
            checked_url=company.ats_feed_url,
            source=CompanySource(
                company_name=company.company_name,
                source_type=company.ats_type,
                identifier=company.company_name,
                url=company.ats_feed_url,
            ),
            confidence="configured",
            status="already_configured",
            evidence=["Company already has ats_type and ats_feed_url."],
        )

    career_result = discover_career_url(company)
    start_urls = _unique_urls([career_result.career_url, company.career_url, company.website])
    if not start_urls:
        return SourceDiscoveryResult(
            company_name=company.company_name,
            checked_url="",
            source=None,
            confidence="none",
            status="missing_url",
            evidence=["Company has no career_url or website."],
        )

    checked: set[str] = set()
    errors: list[str] = []
    for start_url in start_urls:
        result = _discover_from_url(company.company_name, start_url, checked)
        if result.source is not None or result.status in {"login_required", "generic_html"}:
            return result
        if result.error_message:
            errors.append(result.error_message)

    return SourceDiscoveryResult(
        company_name=company.company_name,
        checked_url=start_urls[0],
        source=None,
        confidence="none",
        status="not_found",
        evidence=["No supported ATS link found in checked pages."],
        error_message="; ".join(errors),
    )


def discover_career_url(company: Company) -> CareerUrlDiscoveryResult:
    existing = _normalise_url(company.career_url)
    if existing:
        return CareerUrlDiscoveryResult(
            company_name=company.company_name,
            career_url=existing,
            confidence="configured",
            status="configured",
            evidence=["Company already has career_url configured."],
        )

    website = _normalise_url(company.website)
    if not website:
        return CareerUrlDiscoveryResult(
            company_name=company.company_name,
            career_url="",
            confidence="none",
            status="missing_website",
            evidence=["Company has no website."],
        )

    try:
        html = fetch_html(website)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        common_url = _best_common_career_path(website)
        return CareerUrlDiscoveryResult(
            company_name=company.company_name,
            career_url=common_url,
            confidence="low",
            status="guessed_common_path",
            evidence=["Website homepage could not be fetched; guessed common career path."],
            error_message=str(exc),
        )

    parser = LinkParser(website)
    parser.feed(html)
    career_links = _career_links(parser.links)
    if career_links:
        best = career_links[0]
        return CareerUrlDiscoveryResult(
            company_name=company.company_name,
            career_url=best,
            confidence="medium",
            status="found_link",
            evidence=[f"Found career-like link on website: {best}"],
        )

    common_url = _best_common_career_path(website)
    return CareerUrlDiscoveryResult(
        company_name=company.company_name,
        career_url=common_url,
        confidence="low",
        status="guessed_common_path",
        evidence=["No career link found on homepage; guessed common career path."],
    )


def _discover_from_url(company_name: str, url: str, checked: set[str]) -> SourceDiscoveryResult:
    normalised_url = _normalise_url(url)
    if normalised_url in checked:
        return SourceDiscoveryResult(company_name, normalised_url, None, "none", "not_found", [])
    checked.add(normalised_url)

    direct_source = detect_company_source(company_name, normalised_url)
    if direct_source is not None:
        return SourceDiscoveryResult(
            company_name=company_name,
            checked_url=normalised_url,
            source=direct_source,
            confidence="high",
            status="supported_ats",
            evidence=[f"URL directly matches {direct_source.source_type}."],
        )

    try:
        html = fetch_html(normalised_url)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        return SourceDiscoveryResult(
            company_name=company_name,
            checked_url=normalised_url,
            source=None,
            confidence="none",
            status="fetch_failed",
            evidence=[],
            error_message=str(exc),
        )

    page_text = _plain_text(html)
    if _looks_login_required(page_text, normalised_url):
        return SourceDiscoveryResult(
            company_name=company_name,
            checked_url=normalised_url,
            source=None,
            confidence="medium",
            status="login_required",
            evidence=["Page text or URL suggests login/account registration is required."],
        )

    parser = LinkParser(normalised_url)
    parser.feed(html)
    links = _prioritise_links(parser.links)
    for link in links:
        source = detect_company_source(company_name, link)
        if source is not None:
            return SourceDiscoveryResult(
                company_name=company_name,
                checked_url=normalised_url,
                source=source,
                confidence="high",
                status="supported_ats",
                evidence=[f"Found supported ATS link: {link}"],
            )

    if _looks_like_job_page(page_text, parser.links):
        return SourceDiscoveryResult(
            company_name=company_name,
            checked_url=normalised_url,
            source=CompanySource(
                company_name=company_name,
                source_type="generic_html",
                identifier=company_name,
                url=normalised_url,
            ),
            confidence="low",
            status="generic_html",
            evidence=["Career page contains job-related text but no supported ATS feed was found."],
        )

    for link in links[:8]:
        if link in checked or _host(link) != _host(normalised_url):
            continue
        if any(keyword in link.lower() for keyword in CAREER_LINK_KEYWORDS):
            result = _discover_from_url(company_name, link, checked)
            if result.source is not None or result.status in {"login_required", "generic_html"}:
                return result

    return SourceDiscoveryResult(
        company_name=company_name,
        checked_url=normalised_url,
        source=None,
        confidence="none",
        status="not_found",
        evidence=["No supported ATS links found on page."],
    )


def fetch_html(url: str, timeout_seconds: int = 20) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 job-source-discovery/0.1",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            raise ValueError(f"Unsupported content type: {content_type}")
        raw = response.read(2_000_000)
    return raw.decode("utf-8", errors="replace")


def _unique_urls(values: list[str]) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for value in values:
        url = _normalise_url(value)
        if url and url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def _normalise_url(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    parsed = urlparse(text)
    if not parsed.scheme:
        text = f"https://{text}"
        parsed = urlparse(text)
    path = parsed.path or "/"
    return parsed._replace(path=path, fragment="").geturl()


def _host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _looks_login_required(text: str, url: str) -> bool:
    combined = f"{url} {text}".lower()
    return any(keyword in combined for keyword in LOGIN_REQUIRED_KEYWORDS) and (
        "apply" in combined or "candidate" in combined or "account" in combined
    )


def _looks_like_job_page(text: str, links: list[str]) -> bool:
    combined = " ".join([text.lower(), " ".join(links).lower()])
    signals = ["current openings", "open roles", "job openings", "vacancies", "apply now", "view role"]
    return any(signal in combined for signal in signals)


def _prioritise_links(links: list[str]) -> list[str]:
    def score(link: str) -> int:
        lower = link.lower()
        ats_score = 10 if any(domain in lower for domain in ["greenhouse.io", "lever.co", "smartrecruiters.com"]) else 0
        career_score = 3 if any(keyword in lower for keyword in CAREER_LINK_KEYWORDS) else 0
        return ats_score + career_score

    return sorted(dict.fromkeys(links), key=score, reverse=True)


def _career_links(links: list[str]) -> list[str]:
    return [
        link
        for link in _prioritise_links(links)
        if any(keyword in link.lower() for keyword in CAREER_LINK_KEYWORDS)
    ]


def _best_common_career_path(website: str) -> str:
    parsed = urlparse(website)
    root = f"{parsed.scheme}://{parsed.netloc}"
    return urljoin(root, COMMON_CAREER_PATHS[0])


def _plain_text(html: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class LinkParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() not in {"a", "link"}:
            return
        values = dict(attrs)
        href = values.get("href")
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            return
        self.links.append(urljoin(self.base_url, href))
