from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import func, select

from app.applications.materials import prepare_application
from app.browser.autofill import plan_autofill_for_file, record_autofill_plan, summarise_plan
from app.browser.playwright_runner import run_playwright_autofill
from app.config.loader import load_project_config
from app.dashboard.render import render_daily_digest, render_dashboard
from app.db.importers import import_companies
from app.db.job_repository import upsert_job_from_raw
from app.db.models import Application, AutofillLog, Company, Job, SourceScan
from app.db.session import create_db_engine, init_db, make_session_factory
from app.jobs.scorer import apply_score
from app.sources.generic_html import fetch_and_parse_job
from app.sources.scanner import find_company_by_name, scan_company
from app.sources.base import CompanySource
from app.sources.discovery import (
    CareerUrlDiscoveryResult,
    SourceDiscoveryResult,
    discover_career_url,
    discover_company_source,
    write_career_url_html_report,
    write_discovery_html_report,
    write_discovery_report,
)
from app.workflows.mode_b import (
    mark_job_status,
    prepare_jobs_batch,
    recommended_queue,
    run_daily_scan,
    scan_companies_by_priority,
)
from app.workflows.mode_a import run_mode_a
from app.workflows.manual_assist import run_manual_assist
from app.workflows.applications import APPLICATION_STATUSES, mark_application_status


def main() -> None:
    parser = argparse.ArgumentParser(description="NZ IT job application automation CLI")
    parser.add_argument(
        "--root",
        default=str(Path.cwd()),
        help="Project root containing YAML and Markdown source files.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-config", help="Validate project source files.")
    subparsers.add_parser("init-db", help="Create local SQLite tables.")
    subparsers.add_parser("import-companies", help="Import company targets into the database.")
    subparsers.add_parser("db-summary", help="Show local database record counts.")
    ingest_parser = subparsers.add_parser("ingest-job", help="Fetch and store a single job URL.")
    ingest_parser.add_argument("url", help="Public job URL to ingest.")
    subparsers.add_parser("score-jobs", help="Classify and score all jobs in the database.")
    subparsers.add_parser("list-jobs", help="List stored jobs with classification and score.")
    scan_parser = subparsers.add_parser("scan-company", help="Scan one company using a supported ATS source.")
    scan_parser.add_argument("company_name", help="Company name as stored in the database.")
    scan_parser.add_argument("--source-type", choices=["greenhouse", "lever", "smartrecruiters", "generic_html"], help="Override detected source type.")
    scan_parser.add_argument("--source-url", help="Override source API URL. Useful for smoke tests and fixtures.")
    discover_parser = subparsers.add_parser("discover-company-source", help="Suggest ATS source details for one company.")
    discover_parser.add_argument("--company", required=True, help="Company name as stored in the database.")
    career_parser = subparsers.add_parser("discover-career-url", help="Find the likely careers page for one company.")
    career_parser.add_argument("--company", required=True, help="Company name as stored in the database.")
    career_many_parser = subparsers.add_parser("discover-career-urls", help="Find likely careers pages for multiple companies.")
    career_many_parser.add_argument("--max-priority", type=int, default=1)
    career_many_parser.add_argument("--limit", type=int, default=20)
    career_many_parser.add_argument(
        "--html-output",
        help="HTML report path. Defaults to data/generated/career_url_discovery.html.",
    )
    discover_many_parser = subparsers.add_parser("discover-company-sources", help="Suggest ATS source details for multiple companies.")
    discover_many_parser.add_argument("--max-priority", type=int, default=1)
    discover_many_parser.add_argument("--limit", type=int, default=10)
    discover_many_parser.add_argument(
        "--output",
        help="Markdown report path. Defaults to data/generated/company_source_discovery.md.",
    )
    discover_many_parser.add_argument(
        "--html-output",
        help="HTML report path. Defaults to data/generated/company_source_discovery.html.",
    )
    prepare_parser = subparsers.add_parser("prepare-application", help="Create or update an application draft for a stored job.")
    prepare_parser.add_argument("job_id", type=int, help="Stored job ID.")
    subparsers.add_parser("list-applications", help="List prepared applications.")
    autofill_parser = subparsers.add_parser("autofill-application", help="Autofill or plan autofill for an application.")
    autofill_parser.add_argument("application_id", type=int, help="Prepared application ID.")
    autofill_parser.add_argument("--url", required=True, help="Application form URL.")
    autofill_parser.add_argument(
        "--static-file-plan",
        action="store_true",
        help="Plan and log autofill using static file:// HTML without launching a browser.",
    )
    autofill_parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Playwright in headless mode when browser autofill is used.",
    )
    autofill_parser.add_argument(
        "--keep-open",
        action="store_true",
        help="Keep the browser open after autofill for a review window.",
    )
    autofill_parser.add_argument(
        "--keep-open-seconds",
        type=int,
        default=300,
        help="Seconds to keep the browser open when --keep-open is used.",
    )
    autofill_parser.add_argument(
        "--captcha-wait-seconds",
        type=int,
        default=300,
        help="Seconds to wait for manual CAPTCHA/bot verification before continuing.",
    )
    autofill_parser.add_argument(
        "--form-wait-seconds",
        type=int,
        default=60,
        help="Seconds to wait for dynamic application form fields to render.",
    )
    mode_a_parser = subparsers.add_parser("mode-a", help="Run single-job end-to-end workflow.")
    mode_a_parser.add_argument("job_url", help="Public job URL to ingest and prepare.")
    mode_a_parser.add_argument("--form-url", help="Optional application form URL for autofill planning.")
    mode_a_parser.add_argument(
        "--static-file-plan",
        action="store_true",
        help="Use static file:// form planning for the optional form URL.",
    )
    mode_a_parser.add_argument(
        "--minimum-score",
        type=float,
        default=55.0,
        help="Minimum match score used for recommendation labelling.",
    )
    batch_scan_parser = subparsers.add_parser("batch-scan", help="Scan companies by priority for Mode B.")
    batch_scan_parser.add_argument("--max-priority", type=int, default=1, help="Scan companies with priority <= this value.")
    batch_scan_parser.add_argument("--limit", type=int, help="Maximum number of companies to scan.")
    daily_scan_parser = subparsers.add_parser("run-daily-scan", help="Run import, scan, scoring, dashboard, and digest in one command.")
    daily_scan_parser.add_argument("--max-priority", type=int, default=2)
    daily_scan_parser.add_argument("--limit", type=int, default=60)
    daily_scan_parser.add_argument("--minimum-score", type=float, default=55.0)
    daily_scan_parser.add_argument("--dashboard-output", help="Dashboard HTML path. Defaults to data/generated/dashboard.html.")
    daily_scan_parser.add_argument("--digest-limit", type=int, default=10)
    queue_parser = subparsers.add_parser("queue", help="Show recommended job queue.")
    queue_parser.add_argument("--minimum-score", type=float, default=55.0)
    queue_parser.add_argument("--limit", type=int, default=20)
    queue_parser.add_argument("--include-prepared", action="store_true")
    queue_parser.add_argument("--role-group", action="append", help="Filter queue by role group. Can be repeated.")
    manual_queue_parser = subparsers.add_parser("manual-queue", help="Show recommended links to open manually.")
    manual_queue_parser.add_argument("--minimum-score", type=float, default=55.0)
    manual_queue_parser.add_argument("--limit", type=int, default=10)
    manual_queue_parser.add_argument("--include-prepared", action="store_true")
    manual_queue_parser.add_argument("--role-group", action="append", help="Filter queue by role group. Can be repeated.")
    batch_prepare_parser = subparsers.add_parser("batch-prepare", help="Prepare applications for selected job IDs.")
    batch_prepare_parser.add_argument("job_ids", nargs="+", type=int)
    mark_parser = subparsers.add_parser("mark-job", help="Mark a job status.")
    mark_parser.add_argument("job_id", type=int)
    mark_parser.add_argument("status", choices=["discovered", "shortlisted", "ignored", "prepared", "archived"])
    mark_application_parser = subparsers.add_parser("mark-application", help="Mark an application status.")
    mark_application_parser.add_argument("application_id", type=int)
    mark_application_parser.add_argument("status", choices=APPLICATION_STATUSES)
    mark_application_parser.add_argument("--note", default="", help="Optional note to append to the application.")
    dashboard_parser = subparsers.add_parser("dashboard", help="Generate a local HTML dashboard.")
    dashboard_parser.add_argument("--minimum-score", type=float, default=55.0)
    dashboard_parser.add_argument("--output", help="Output HTML path. Defaults to data/generated/dashboard.html.")
    digest_parser = subparsers.add_parser("daily-digest", help="Print a daily digest of jobs and applications.")
    digest_parser.add_argument("--minimum-score", type=float, default=55.0)
    digest_parser.add_argument("--limit", type=int, default=10)
    manual_parser = subparsers.add_parser("manual-assist", help="Prepare copy/paste material for a manual application.")
    manual_parser.add_argument("--url", required=True, help="Job or application URL currently opened manually.")
    manual_parser.add_argument(
        "--output-dir",
        help="Directory for the generated manual assist Markdown file. Defaults to data/generated.",
    )

    args = parser.parse_args()
    root = Path(args.root)

    if args.command == "validate-config":
        config = load_project_config(root)
        print(f"Config OK: {len(config.companies)} companies loaded")
        return

    config = load_project_config(root)
    engine = create_db_engine(config.paths.database)
    session_factory = make_session_factory(engine)

    if args.command == "init-db":
        init_db(engine)
        print(f"Database initialised: {config.paths.database}")
        engine.dispose()
        return

    init_db(engine)
    try:
        with session_factory() as session:
            if args.command == "import-companies":
                created, updated = import_companies(config, session)
                print(f"Companies imported: {created} created, {updated} updated")
                return

            if args.command == "db-summary":
                counts = {
                    "companies": _count(session, Company),
                    "jobs": _count(session, Job),
                    "applications": _count(session, Application),
                    "autofill_logs": _count(session, AutofillLog),
                    "source_scans": _count(session, SourceScan),
                }
                for name, count in counts.items():
                    print(f"{name}: {count}")
                return

            if args.command == "ingest-job":
                raw_job = fetch_and_parse_job(args.url)
                job, created = upsert_job_from_raw(raw_job, session, config=config)
                action = "created" if created else "updated"
                print(f"Job {action}: #{job.id} {job.title}")
                print(f"Company: {job.company_name or 'Unknown'}")
                print(f"Source: {job.source}")
                print(f"Role group: {job.role_group or 'unknown'}")
                print(f"Match score: {job.match_score if job.match_score is not None else 'unscored'}")
                print(f"URL: {job.source_url}")
                return

            if args.command == "score-jobs":
                jobs = session.scalars(select(Job)).all()
                for job in jobs:
                    apply_score(job, config)
                session.commit()
                print(f"Jobs scored: {len(jobs)}")
                return

            if args.command == "list-jobs":
                jobs = session.scalars(select(Job).order_by(Job.match_score.desc().nullslast(), Job.id)).all()
                if not jobs:
                    print("No jobs stored yet.")
                    return
                for job in jobs:
                    score = job.match_score if job.match_score is not None else "unscored"
                    print(
                        f"#{job.id} | {score} | {job.role_group or 'unknown'} | "
                        f"{job.company_name or 'Unknown'} | {job.title}"
                    )
                return

            if args.command == "scan-company":
                company = find_company_by_name(session, args.company_name)
                if company is None:
                    raise SystemExit(f"Company not found: {args.company_name}")
                source_override = None
                if args.source_type and args.source_url:
                    source_override = CompanySource(
                        company_name=company.company_name,
                        source_type=args.source_type,
                        identifier=company.company_name,
                        url=args.source_url,
                    )
                found, created = scan_company(company, session, config, source_override=source_override)
                print(f"Company scanned: {company.company_name}")
                print(f"Jobs found: {found}")
                print(f"New jobs: {created}")
                return

            if args.command == "discover-company-source":
                company = find_company_by_name(session, args.company)
                if company is None:
                    raise SystemExit(f"Company not found: {args.company}")
                _print_discovery_result(discover_company_source(company, config))
                return

            if args.command == "discover-career-url":
                company = find_company_by_name(session, args.company)
                if company is None:
                    raise SystemExit(f"Company not found: {args.company}")
                _print_career_url_result(discover_career_url(company))
                return

            if args.command == "discover-career-urls":
                companies = session.scalars(
                    select(Company)
                    .where(Company.active.is_(True), Company.priority <= args.max_priority)
                    .order_by(Company.priority, Company.company_name)
                    .limit(args.limit)
                ).all()
                if not companies:
                    print("No companies found for career URL discovery.")
                    return
                results = []
                for index, company in enumerate(companies, start=1):
                    if index > 1:
                        print("")
                    result = discover_career_url(company)
                    results.append(result)
                    _print_career_url_result(result)
                html_output = (
                    Path(args.html_output)
                    if args.html_output
                    else config.paths.root / "data" / "generated" / "career_url_discovery.html"
                )
                html_path = write_career_url_html_report(results, html_output)
                print("")
                print(f"Career URL website written: {html_path}")
                return

            if args.command == "discover-company-sources":
                companies = session.scalars(
                    select(Company)
                    .where(Company.active.is_(True), Company.priority <= args.max_priority)
                    .order_by(Company.priority, Company.company_name)
                    .limit(args.limit)
                ).all()
                if not companies:
                    print("No companies found for discovery.")
                    return
                results = []
                for index, company in enumerate(companies, start=1):
                    if index > 1:
                        print("")
                    result = discover_company_source(company, config)
                    results.append(result)
                    _print_discovery_result(result)
                output = (
                    Path(args.output)
                    if args.output
                    else config.paths.root / "data" / "generated" / "company_source_discovery.md"
                )
                path = write_discovery_report(results, output)
                html_output = (
                    Path(args.html_output)
                    if args.html_output
                    else config.paths.root / "data" / "generated" / "company_source_discovery.html"
                )
                html_path = write_discovery_html_report(results, html_output)
                print("")
                print(f"Discovery report written: {path}")
                print(f"Discovery website written: {html_path}")
                return

            if args.command == "prepare-application":
                job = session.get(Job, args.job_id)
                if job is None:
                    raise SystemExit(f"Job not found: {args.job_id}")
                application, created = prepare_application(job, config, session)
                action = "created" if created else "updated"
                print(f"Application {action}: #{application.id}")
                print(f"Job: #{job.id} {job.title}")
                print(f"Company: {job.company_name or 'Unknown'}")
                print(f"Status: {application.status}")
                print(f"Cover letter characters: {len(application.generated_cover_letter)}")
                return

            if args.command == "list-applications":
                applications = session.scalars(select(Application).order_by(Application.id)).all()
                if not applications:
                    print("No applications prepared yet.")
                    return
                for application in applications:
                    job = application.job
                    print(
                        f"#{application.id} | {application.status} | "
                        f"job #{job.id} | {job.company_name or 'Unknown'} | {job.title}"
                    )
                return

            if args.command == "autofill-application":
                application = session.get(Application, args.application_id)
                if application is None:
                    raise SystemExit(f"Application not found: {args.application_id}")

                if args.static_file_plan:
                    plan = plan_autofill_for_file(args.url, config)
                    record_autofill_plan(application, plan, session, mark_completed=True)
                    summary = summarise_plan(plan)
                else:
                    summary = run_playwright_autofill(
                        application,
                        args.url,
                        config,
                        session,
                        headless=args.headless,
                        keep_open=args.keep_open,
                        keep_open_seconds=args.keep_open_seconds,
                        captcha_wait_seconds=args.captcha_wait_seconds,
                        form_wait_seconds=args.form_wait_seconds,
                    )

                print(f"Autofill processed for application #{application.id}")
                print(f"Filled: {summary['filled']}")
                print(f"Review required: {summary['review_required']}")
                print(f"Paused: {summary['paused']}")
                print(f"Skipped: {summary['skipped']}")
                print("Final submit clicked: no")
                return

            if args.command == "mode-a":
                result = run_mode_a(
                    args.job_url,
                    config,
                    session,
                    form_url=args.form_url,
                    static_file_plan=args.static_file_plan,
                    minimum_score=args.minimum_score,
                )
                print("Mode A completed")
                print(f"Job: #{result.job_id} {result.title}")
                print(f"Company: {result.company_name or 'Unknown'}")
                print(f"Role group: {result.role_group or 'unknown'}")
                print(f"Match score: {result.match_score if result.match_score is not None else 'unscored'}")
                print(f"Recommendation: {result.recommendation}")
                print(f"Application: #{result.application_id}")
                print(f"Job record: {'created' if result.job_created else 'updated'}")
                print(f"Application record: {'created' if result.application_created else 'updated'}")
                if result.autofill_summary is not None:
                    print(f"Autofill filled: {result.autofill_summary['filled']}")
                    print(f"Autofill review required: {result.autofill_summary['review_required']}")
                    print(f"Autofill paused: {result.autofill_summary['paused']}")
                    print("Final submit clicked: no")
                return

            if args.command == "batch-scan":
                scanned, found, created = scan_companies_by_priority(
                    session,
                    config,
                    max_priority=args.max_priority,
                    limit=args.limit,
                )
                print(f"Companies with jobs scanned: {scanned}")
                print(f"Jobs found: {found}")
                print(f"New jobs: {created}")
                return

            if args.command == "run-daily-scan":
                result = run_daily_scan(
                    session,
                    config,
                    max_priority=args.max_priority,
                    limit=args.limit,
                    minimum_score=args.minimum_score,
                    dashboard_output=Path(args.dashboard_output) if args.dashboard_output else None,
                    digest_limit=args.digest_limit,
                )
                print("Daily scan completed")
                print(f"Companies imported: {result.companies_created} created, {result.companies_updated} updated")
                print(f"Companies with jobs scanned: {result.companies_scanned}")
                print(f"Jobs found: {result.jobs_found}")
                print(f"New jobs: {result.new_jobs}")
                print(f"Jobs scored: {result.jobs_scored}")
                print(f"Recommended jobs: {result.recommended_count}")
                print(f"Dashboard: {result.dashboard_path}")
                print("")
                print(result.digest)
                return

            if args.command == "queue":
                items = recommended_queue(
                    session,
                    minimum_score=args.minimum_score,
                    limit=args.limit,
                    include_prepared=args.include_prepared,
                    role_groups=args.role_group,
                )
                if not items:
                    print("No recommended jobs found.")
                    return
                for item in items:
                    score = item.match_score if item.match_score is not None else "unscored"
                    print(
                        f"#{item.job_id} | {score} | {item.role_group or 'unknown'} | "
                        f"{item.status} | {item.company_name or 'Unknown'} | {item.title}"
                    )
                return

            if args.command == "manual-queue":
                items = recommended_queue(
                    session,
                    minimum_score=args.minimum_score,
                    limit=args.limit,
                    include_prepared=args.include_prepared,
                    role_groups=args.role_group,
                )
                if not items:
                    print("No recommended manual links found.")
                    return
                print("Manual application queue")
                print(f"Minimum score: {args.minimum_score:g}")
                for item in items:
                    score = item.match_score if item.match_score is not None else "unscored"
                    print("")
                    print(
                        f"#{item.job_id} | {score} | {item.status} | "
                        f"{item.company_name or 'Unknown'} | {item.title}"
                    )
                    print(f"Open: {item.open_url}")
                    print(f"Assist: python -m app.cli manual-assist --url \"{item.open_url}\"")
                return

            if args.command == "batch-prepare":
                results = prepare_jobs_batch(session, config, args.job_ids)
                if not results:
                    print("No applications prepared.")
                    return
                for result in results:
                    action = "created" if result.created else "updated"
                    print(
                        f"Application {action}: #{result.application_id} | "
                        f"job #{result.job_id} | {result.company_name or 'Unknown'} | {result.title}"
                    )
                return

            if args.command == "mark-job":
                job = mark_job_status(session, args.job_id, args.status)
                if job is None:
                    raise SystemExit(f"Job not found: {args.job_id}")
                print(f"Job #{job.id} marked as {job.status}")
                return

            if args.command == "mark-application":
                application = mark_application_status(
                    session,
                    args.application_id,
                    args.status,
                    note=args.note,
                )
                if application is None:
                    raise SystemExit(f"Application not found: {args.application_id}")
                print(f"Application #{application.id} marked as {application.status}")
                if application.submitted_at:
                    print(f"Submitted at: {application.submitted_at}")
                return

            if args.command == "dashboard":
                output = Path(args.output) if args.output else config.paths.root / "data" / "generated" / "dashboard.html"
                path = render_dashboard(session, output, minimum_score=args.minimum_score)
                print(f"Dashboard generated: {path}")
                return

            if args.command == "daily-digest":
                print(render_daily_digest(session, minimum_score=args.minimum_score, limit=args.limit))
                return

            if args.command == "manual-assist":
                result = run_manual_assist(
                    args.url,
                    config,
                    session,
                    output_dir=Path(args.output_dir) if args.output_dir else None,
                )
                print("Manual assist ready")
                print(f"Matched by: {result.matched_by}")
                print(f"Job: #{result.job_id} {result.title}")
                print(f"Company: {result.company_name or 'Unknown'}")
                print(f"Application: #{result.application_id}")
                print(f"Status: {result.status}")
                print(f"Job record: {'created' if result.job_created else 'existing'}")
                print(f"Application record: {'created' if result.application_created else 'updated'}")
                print(f"Assist file: {result.output_path}")
                return
    finally:
        engine.dispose()


def _count(session, model: type) -> int:
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


def _print_discovery_result(result: SourceDiscoveryResult) -> None:
    print(f"Company: {result.company_name}")
    print(f"Checked URL: {result.checked_url or 'none'}")
    print(f"Status: {result.status}")
    print(f"Confidence: {result.confidence}")
    if result.source is not None:
        print(f"Suggested ats_type: {result.source.source_type}")
        print(f"Suggested ats_feed_url: {result.source.url}")
    else:
        print("Suggested ats_type: none")
        print("Suggested ats_feed_url: none")
    if result.evidence:
        print("Evidence:")
        for item in result.evidence:
            print(f"- {item}")
    if result.error_message:
        print(f"Error: {result.error_message}")


def _print_career_url_result(result: CareerUrlDiscoveryResult) -> None:
    print(f"Company: {result.company_name}")
    print(f"Status: {result.status}")
    print(f"Confidence: {result.confidence}")
    print(f"Career URL: {result.career_url or 'none'}")
    if result.evidence:
        print("Evidence:")
        for item in result.evidence:
            print(f"- {item}")
    if result.error_message:
        print(f"Error: {result.error_message}")


if __name__ == "__main__":
    main()
