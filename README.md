# New Zealand IT Job Application Automation

Personal job application assistant for New Zealand IT roles.

The project follows `PRD.md`. Phase 0 and Phase 1 cover:

- Loading project source files.
- Validating YAML configuration.
- Creating local SQLite storage.
- Importing target companies from `nz_it_company_targets.yaml`.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Commands

Validate source files:

```powershell
python -m app.cli validate-config
```

Initialise the local database:

```powershell
python -m app.cli init-db
```

Import company targets:

```powershell
python -m app.cli import-companies
```

Show database summary:

```powershell
python -m app.cli db-summary
```

Ingest and score a single job URL:

```powershell
python -m app.cli ingest-job "<job-url>"
python -m app.cli list-jobs
```

Import saved SEEK recommendation email files:

```powershell
python -m app.cli import-seek-email "data/seek_emails/seek-recommendations.eml"
python -m app.cli import-seek-email-folder data/seek_emails
```

The SEEK email importer reads saved `.eml`, `.html`, and `.htm` files, extracts recommended job cards, stores them with source `seek_email`, scores them, deduplicates by URL, and refreshes `data/generated/dashboard.html` by default.

Import saved Jora search/job pages:

```powershell
python -m app.cli import-jora-html "data/jora_pages/jora-ai-search.html"
python -m app.cli import-jora-html-folder data/jora_pages
```

The Jora importer reads saved `.html` / `.htm` pages, extracts visible job cards, stores them with source `jora_html`, scores them, deduplicates by URL, and refreshes `data/generated/dashboard.html` by default.

Prepare an application draft:

```powershell
python -m app.cli prepare-application <job-id>
python -m app.cli list-applications
```

Run conservative autofill on a prepared application:

```powershell
python -m app.cli autofill-application <application-id> --url "<form-url>" --headless
```

Run visible-browser autofill and keep the browser open for manual review:

```powershell
python -m app.cli autofill-application <application-id> --url "<form-url>" --keep-open --keep-open-seconds 180
```

For ATS pages that show CAPTCHA or bot verification, the tool pauses and waits for manual verification instead of bypassing it:

```powershell
python -m app.cli autofill-application <application-id> --url "<form-url>" --keep-open --captcha-wait-seconds 300 --form-wait-seconds 90
```

For local static HTML fixtures without launching a browser:

```powershell
python -m app.cli autofill-application <application-id> --url "file:///path/to/form.html" --static-file-plan
```

Run Mode A end to end for one job:

```powershell
python -m app.cli mode-a "<job-url>"
```

With a local/static form autofill plan:

```powershell
python -m app.cli mode-a "<job-url>" --form-url "file:///path/to/form.html" --static-file-plan
```

Run Mode B queue workflow:

```powershell
python -m app.cli queue --minimum-score 55 --limit 20
python -m app.cli manual-queue --minimum-score 55 --limit 10
python -m app.cli manual-queue --minimum-score 55 --limit 10 --role-group data_analyst
python -m app.cli manual-queue --minimum-score 55 --limit 10 --role-group business_analyst
python -m app.cli manual-queue --minimum-score 55 --limit 10 --role-group analyst
python -m app.cli mark-job <job-id> shortlisted
python -m app.cli mark-application <application-id> submitted --note "Submitted manually"
python -m app.cli batch-prepare <job-id-1> <job-id-2>
```

Scan companies by priority:

```powershell
python -m app.cli batch-scan --max-priority 1 --limit 10
python -m app.cli scan-company "Accenture New Zealand" --source-type generic_html --source-url "https://www.accenture.com/nz-en/careers"
```

Discover suggested ATS sources before scanning:

```powershell
python -m app.cli discover-career-url --company "Xero"
python -m app.cli discover-career-urls --max-priority 1 --limit 20 --html-output data/generated/career_url_discovery.html
python -m app.cli discover-company-source --company "Xero"
python -m app.cli discover-company-sources --max-priority 1 --limit 10 --output data/generated/company_source_discovery.md
```

Generate local dashboard and digest:

```powershell
python -m app.cli dashboard --minimum-score 55
python -m app.cli daily-digest --minimum-score 55 --limit 10
```

After running, open the dashboard in your browser:

- [data/generated/dashboard.html](data/generated/dashboard.html)

Run the daily scan workflow manually:

```powershell
python -m app.cli run-daily-scan --max-priority 2 --limit 60 --minimum-score 55 --digest-limit 10
```

Prepare copy/paste material for a manual application page:

```powershell
python -m app.cli manual-assist --url "<job-or-application-url>"
```

This matches the URL to an existing job when possible, prepares or refreshes the application draft, marks it as `manual_apply_in_progress`, and writes a Markdown assist file under `data/generated/`.

## Tests

```powershell
pytest
```
