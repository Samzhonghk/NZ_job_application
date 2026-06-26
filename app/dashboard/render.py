from __future__ import annotations

from html import escape
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Application, Job


HIDDEN_JOB_STATUSES = ["ignored", "archived", "superseded_duplicate"]
HIDDEN_APPLICATION_STATUSES = ["sample_archived", "superseded_duplicate", "archived"]
CORE_RECOMMENDED_ROLE_GROUPS = [
    "software",
    "data",
    "data_analyst",
    "business_analyst",
    "ai",
    "cloud",
    "security",
    "qa",
    "product",
]


def render_dashboard(session: Session, output_path: Path, minimum_score: float = 55.0) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    jobs = session.scalars(
        select(Job)
        .where(Job.is_it_related.is_(True))
        .where(Job.match_score.is_not(None), Job.match_score >= minimum_score)
        .where(Job.status.not_in(HIDDEN_JOB_STATUSES))
        .where(Job.role_group.in_(CORE_RECOMMENDED_ROLE_GROUPS))
        .order_by(Job.match_score.desc(), Job.discovered_at.desc())
    ).all()
    applications = session.scalars(
        select(Application)
        .where(Application.status.not_in(HIDDEN_APPLICATION_STATUSES))
        .order_by(Application.updated_at.desc())
    ).all()

    output_path.write_text(
        _dashboard_html(jobs, applications, minimum_score),
        encoding="utf-8",
    )
    return output_path


def render_daily_digest(session: Session, minimum_score: float = 55.0, limit: int = 10) -> str:
    jobs = session.scalars(
        select(Job)
        .where(Job.is_it_related.is_(True))
        .where(Job.match_score.is_not(None), Job.match_score >= minimum_score)
        .where(Job.status.not_in(HIDDEN_JOB_STATUSES))
        .where(Job.role_group.in_(CORE_RECOMMENDED_ROLE_GROUPS))
        .order_by(Job.match_score.desc(), Job.discovered_at.desc())
        .limit(limit)
    ).all()
    applications = session.scalars(
        select(Application)
        .where(Application.status.not_in(HIDDEN_APPLICATION_STATUSES))
        .order_by(Application.updated_at.desc())
        .limit(10)
    ).all()

    lines = [
        "NZ IT Job Application Daily Digest",
        "",
        f"Recommended jobs, minimum score {minimum_score:g}:",
    ]
    if jobs:
        for job in jobs:
            lines.append(
                f"- #{job.id} | {job.match_score:g} | {job.role_group or 'unknown'} | "
                f"{job.status} | {job.company_name or 'Unknown'} | {job.title}"
            )
    else:
        lines.append("- No recommended jobs found.")

    lines.extend(["", "Recent applications:"])
    if applications:
        for application in applications:
            job = application.job
            lines.append(
                f"- #{application.id} | {application.status} | job #{job.id} | "
                f"{job.company_name or 'Unknown'} | {job.title}"
            )
    else:
        lines.append("- No applications prepared yet.")

    return "\n".join(lines)


def _dashboard_html(jobs: list[Job], applications: list[Application], minimum_score: float) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NZ IT Job Application Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f8fa;
      --surface: #ffffff;
      --text: #17202a;
      --muted: #5f6b7a;
      --border: #d8dee7;
      --accent: #176b87;
      --accent-soft: #e7f4f7;
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
    h1 {{
      margin: 0 0 6px;
      font-size: 24px;
      letter-spacing: 0;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }}
    section {{
      margin-bottom: 28px;
    }}
    h2 {{
      font-size: 18px;
      margin: 0 0 12px;
      letter-spacing: 0;
    }}
    .meta {{
      color: var(--muted);
      margin: 0;
    }}
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
    .metric strong {{
      display: block;
      font-size: 22px;
      margin-bottom: 4px;
    }}
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
    .score {{
      font-weight: 700;
      color: var(--accent);
      white-space: nowrap;
    }}
    .tag {{
      display: inline-block;
      border-radius: 999px;
      padding: 2px 8px;
      background: var(--accent-soft);
      color: var(--accent);
      white-space: nowrap;
    }}
    .status {{
      display: inline-block;
      border-radius: 999px;
      padding: 2px 8px;
      background: var(--warning-soft);
      color: var(--warning);
      white-space: nowrap;
    }}
    a {{ color: var(--accent); }}
  </style>
</head>
<body>
  <header>
    <h1>NZ IT Job Application Dashboard</h1>
    <p class="meta">Recommended jobs with match score >= {minimum_score:g}. Final submission remains manual.</p>
  </header>
  <main>
    <div class="summary">
      <div class="metric"><strong>{len(jobs)}</strong><span>Recommended jobs</span></div>
      <div class="metric"><strong>{len(applications)}</strong><span>Applications</span></div>
      <div class="metric"><strong>{_count_status(applications, "prepared")}</strong><span>Prepared</span></div>
      <div class="metric"><strong>{_count_status(applications, "paused_for_review")}</strong><span>Paused for review</span></div>
      <div class="metric"><strong>{_count_status(applications, "submitted")}</strong><span>Submitted</span></div>
      <div class="metric"><strong>{_count_status(applications, "follow_up")}</strong><span>Follow up</span></div>
    </div>
    <section>
      <h2>Recommended Queue</h2>
      {_jobs_table(jobs)}
    </section>
    <section>
      <h2>Applications</h2>
      {_applications_table(applications)}
    </section>
  </main>
</body>
</html>
"""


def _jobs_table(jobs: list[Job]) -> str:
    if not jobs:
        return "<p>No recommended jobs found.</p>"
    rows = "\n".join(
        _job_row(job)
        for job in jobs
    )
    return f"""<table>
  <thead><tr><th>ID</th><th>Score</th><th>Role</th><th>Status</th><th>Company</th><th>Title</th><th>Open</th><th>Next Action</th></tr></thead>
  <tbody>{rows}</tbody>
</table>"""


def _job_row(job: Job) -> str:
    open_url = job.apply_url or job.source_url
    assist_command = f'python -m app.cli manual-assist --url "{open_url}"'
    return (
        f"""<tr>
  <td>#{job.id}</td>
  <td><span class="score">{_score(job.match_score)}</span></td>
  <td><span class="tag">{escape(job.role_group or "unknown")}</span></td>
  <td><span class="status">{escape(job.status)}</span></td>
  <td>{escape(job.company_name or "Unknown")}</td>
  <td><a href="{escape(job.source_url)}">{escape(job.title)}</a></td>
  <td><a href="{escape(open_url)}">Open</a></td>
  <td>{_job_next_action(job, assist_command)}</td>
</tr>"""
    )


def _applications_table(applications: list[Application]) -> str:
    if not applications:
        return "<p>No applications prepared yet.</p>"
    rows = "\n".join(
        f"""<tr>
  <td>#{application.id}</td>
  <td><span class="status">{escape(application.status)}</span></td>
  <td>#{application.job.id}</td>
  <td>{escape(application.job.company_name or "Unknown")}</td>
  <td>{escape(application.job.title)}</td>
  <td>{escape(_date_text(application.submitted_at))}</td>
  <td>{_application_next_action(application)}</td>
</tr>"""
        for application in applications
    )
    return f"""<table>
  <thead><tr><th>ID</th><th>Status</th><th>Job</th><th>Company</th><th>Title</th><th>Submitted</th><th>Next Action</th></tr></thead>
  <tbody>{rows}</tbody>
</table>"""


def _count_status(applications: list[Application], status: str) -> int:
    return sum(1 for application in applications if application.status == status)


def _score(value: float | None) -> str:
    return "unscored" if value is None else f"{value:g}"


def _date_text(value) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d %H:%M")


def _job_next_action(job: Job, assist_command: str) -> str:
    if job.status == "applied":
        return "Already applied. Wait for response or update the application status."
    if job.status == "shortlisted":
        return f"Open the role, then run <code>{escape(assist_command)}</code>"
    return f"Open the role, review it, then run <code>{escape(assist_command)}</code>"


def _application_next_action(application: Application) -> str:
    status = application.status
    if status in {"prepared", "ready_for_manual_submit"}:
        return (
            "Open the application page, submit manually after review, then run "
            f"<code>python -m app.cli mark-application {application.id} submitted --note \"Submitted manually\"</code>"
        )
    if status == "manual_apply_in_progress":
        return (
            "Finish the manual application, then run "
            f"<code>python -m app.cli mark-application {application.id} submitted --note \"Submitted manually\"</code>"
        )
    if status == "paused_for_review":
        return "Resolve the login, CAPTCHA, or access issue manually, then continue with manual-assist."
    if status == "submitted":
        return "Wait for response. Mark follow_up, rejected, or withdrawn when needed."
    if status == "follow_up":
        return "Follow up with the recruiter or hiring team."
    if status == "rejected":
        return "No action needed unless you want to archive notes."
    if status == "withdrawn":
        return "No action needed."
    return "Review this application status."
