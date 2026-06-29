# PRD: New Zealand IT Job Application Automation

## 1. Product Overview

### 1.1 Product Name

New Zealand IT Job Application Automation

### 1.2 Purpose

Build a personal job application assistant for New Zealand IT roles. The system monitors company career pages and job sources, identifies relevant IT roles, scores them against the applicant profile, prepares tailored application materials, autofills application forms, and pauses before final submission for user review.

### 1.3 Core Principle

The product is an application assistant, not an uncontrolled mass-application bot.

The system may discover roles, prepare answers, fill forms, upload files, and organise application queues. By default, it must not click the final submit button. The user remains responsible for reviewing sensitive information and confirming each application.

### 1.4 Source Documents

The following files are product inputs and should be treated as project source data:

- `job_application_material_bank.md`: human-readable source of truth for profile, work rights, skills, experience, salary, and reusable content.
- `application_autofill_rules.yaml`: machine-readable autofill rules and pause/review policy.
- `nz_it_company_targets.yaml`: seed company list for job monitoring.
- `prescreen_answer_templates.md`: short-answer templates for screening questions.

## 2. Goals And Non-Goals

### 2.1 Goals

1. Discover new New Zealand IT-related jobs from company websites, ATS platforms, and selected job sources.
2. Normalise job listings into a consistent data model.
3. Detect whether each job is relevant to software, data, AI, cloud, security, QA, product, or analyst roles.
4. Score each job against the user's profile, target roles, location, work rights, salary expectations, and skills.
5. Support Mode A: process a single pasted job URL immediately.
6. Support Mode B: build a daily batch queue of recommended jobs.
7. Generate or select tailored application content for each role.
8. Autofill application forms using the material bank and autofill rules.
9. Pause before final submission and highlight sensitive or uncertain fields.
10. Track application status across the full job search lifecycle.

### 2.2 Non-Goals For MVP

1. Fully autonomous final submission without user review.
2. Circumventing CAPTCHA, bot protection, login walls, or access controls.
3. Scraping private pages or content requiring unauthorised access.
4. Applying to every possible company in New Zealand without filtering.
5. Replacing user judgement for visa, salary, legal, health, criminal record, or identity questions.
6. Building a public SaaS product for multiple users.
7. Handling every ATS on day one.

## 3. User

### 3.1 Primary User

The primary user is Sam, based in Auckland, New Zealand, looking for IT roles including:

- Software Engineer
- AI Engineer
- Data Engineer
- Data Analyst / Business Analyst-adjacent roles when relevant
- Cloud / DevOps / Platform roles when aligned with experience

### 3.2 Known Profile Facts

These facts come from `job_application_material_bank.md` and `application_autofill_rules.yaml`:

- Current location: Auckland
- Current country: New Zealand
- Work rights: New Zealand Permanent Resident
- Sponsorship required: No
- Earliest start date: Any time
- Notice period: Not required
- Open to remote work: Yes
- Open to relocation/travel: open to discussion
- Salary expectation: NZD 80,000 - 120,000
- Minimum acceptable salary: NZD 80,000

## 4. Product Modes

### 4.1 Mode A: Single Job Immediate Processing

Mode A is used when the user has a specific job URL.

Flow:

1. User pastes a job URL.
2. System fetches and parses the job.
3. System extracts job title, company, location, description, salary if available, application URL, and source.
4. System classifies the job as relevant or not relevant.
5. System calculates match score.
6. System generates an application package.
7. System opens the apply page in a browser automation session.
8. System autofills known fields.
9. System pauses before final submission.
10. User reviews and manually confirms submission.

### 4.2 Mode B: Daily Batch Queue

Mode B is used for scheduled job discovery and batch preparation.

Flow:

1. Scheduler scans configured company/job sources.
2. System detects new jobs since last scan.
3. System deduplicates jobs.
4. System classifies IT relevance.
5. System calculates match scores.
6. System creates a queue sorted by match score and freshness.
7. User reviews the queue and selects jobs to prepare.
8. System processes selected jobs one by one.
9. Each application pauses before final submit.
10. System records application status and notes.

## 5. MVP Scope

### 5.1 MVP Features

1. Project file structure and configuration loader.
2. Read profile and autofill rules from `application_autofill_rules.yaml`.
3. Read company targets from `nz_it_company_targets.yaml`.
4. Job data model and local database.
5. Manual job URL ingestion for Mode A.
6. Company source scanner skeleton for Mode B.
7. Initial ATS/source adapters:
   - Greenhouse
   - Lever
   - SmartRecruiters
   - Generic static career page fallback
8. Job normalisation.
9. IT role classifier using keyword rules first.
10. Match scoring engine.
11. Application queue.
12. Basic material generation using templates and profile data.
13. Browser-based autofill using Playwright.
14. Sensitive-field pause policy.
15. Application status tracker.
16. Local dashboard or CLI-first workflow.

### 5.2 MVP Exclusions

1. Full Workday support if it requires complex login, dynamic state, or custom flows.
2. Automatic SEEK application submission.
3. LinkedIn automation beyond opening links and manual user action.
4. Automatic final submit.
5. Mobile app.
6. Multi-user accounts.
7. Cloud deployment.

## 6. Future Scope

### 6.1 Version 2

1. Dashboard UI with daily queue.
2. Email or Telegram notifications.
3. More ATS adapters:
   - Workday
   - Ashby
   - BambooHR
   - Workable
   - Pinpoint
   - Recruitee
   - Teamtailor
4. Automatic ATS detection and backfill into `nz_it_company_targets.yaml`.
5. LLM-assisted job classification and answer tailoring.
6. CV and cover letter version management.
7. Screenshot and audit log viewer.

### 6.2 Version 3

1. Semi-automated batch autofill from dashboard.
2. Advanced deduplication across SEEK, Trade Me, company website, and ATS sources.
3. Recruiter/contact tracking.
4. Follow-up reminders.
5. Interview pipeline tracking.
6. Salary analytics.
7. Company preference learning based on user choices.

### 6.3 Version 4

1. Carefully restricted auto-submit for explicitly whitelisted low-risk forms only.
2. Browser extension or local companion app.
3. Calendar integration.
4. Email inbox parsing for application responses.
5. Automated follow-up draft generation.

## 7. User Stories

### 7.1 Job Discovery

As a job seeker, I want the system to monitor target companies so that I can discover new IT roles quickly.

Acceptance criteria:

- The system loads companies from `nz_it_company_targets.yaml`.
- The system can scan at least one supported source type.
- The system stores newly discovered jobs.
- The system does not duplicate the same job on repeated scans.

### 7.2 Single Job Processing

As a job seeker, I want to paste a job URL and have the system prepare an application so that I can apply faster.

Acceptance criteria:

- User can provide one URL.
- System extracts job title, company, location, description, and apply URL where available.
- System calculates a match score.
- System creates a draft application record.

### 7.3 Batch Queue

As a job seeker, I want a daily list of recommended jobs so that I can apply to the best roles first.

Acceptance criteria:

- Jobs are ranked by match score and freshness.
- Jobs below the relevance threshold are hidden or marked low priority.
- User can mark jobs as shortlisted, ignored, or ready to prepare.

### 7.4 Autofill

As a job seeker, I want the system to fill standard application fields using my profile so that I do not repeatedly type the same information.

Acceptance criteria:

- System reads `application_autofill_rules.yaml`.
- System fills known fields such as name, email, phone, location, work rights, sponsorship, start date, and salary.
- System does not fill fields listed under `must_pause` without user confirmation.
- System stops before final submit.

### 7.5 Review Before Submission

As a job seeker, I want to review each application before submission so that I can avoid mistakes and protect sensitive information.

Acceptance criteria:

- System shows filled fields before final submit.
- System highlights sensitive fields.
- System captures screenshot or structured log before submission.
- System requires explicit user action to continue.

### 7.6 Application Tracking

As a job seeker, I want to track application status so that I know what I have applied to and what needs follow-up.

Acceptance criteria:

- Each job has a status.
- User can update status.
- System stores application date, submitted materials, notes, and source URL.

## 8. Core Workflows

### 8.1 Scheduled Monitoring Workflow

```text
Load company targets
-> For each active company
-> Detect source/ATS type if unknown
-> Fetch job listings
-> Normalise listings
-> Filter IT roles
-> Deduplicate
-> Score
-> Store new jobs
-> Notify or add to daily queue
```

### 8.2 Application Preparation Workflow

```text
Select job
-> Load job details
-> Load profile and templates
-> Pick relevant summary
-> Pick relevant motivation theme
-> Draft cover letter / screening answers
-> Prepare autofill values
-> Mark application as prepared
```

### 8.3 Browser Autofill Workflow

```text
Open apply URL
-> Inspect form fields
-> Match fields to autofill rules
-> Fill safe fields
-> Highlight review fields
-> Pause on must_pause fields
-> Upload files if configured
-> Save screenshot/log
-> Stop before final submit
```

### 8.4 Status Tracking Workflow

```text
Discovered
-> Shortlisted
-> Prepared
-> Autofilled
-> Submitted manually
-> Replied
-> Interview
-> Offer / Rejected / Withdrawn / Archived
```

## 9. Functional Requirements

### 9.1 Configuration Loader

The system must load:

- `application_autofill_rules.yaml`
- `nz_it_company_targets.yaml`
- `prescreen_answer_templates.md`
- `job_application_material_bank.md`

Requirements:

- Validate required sections.
- Fail gracefully with clear error messages.
- Support reloading without restarting where practical.

### 9.2 Company Target Manager

Requirements:

- Load company list from YAML.
- Filter by priority.
- Filter by target role group.
- Track `last_checked_at` in database rather than modifying YAML during MVP.
- Allow later enrichment of `ats_type` and `ats_feed_url`.

### 9.3 Source Scanner

Requirements:

- Scan each active company at configured intervals.
- Respect rate limits.
- Avoid aggressive crawling.
- Prefer official feeds or structured endpoints over browser scraping.
- Store scan status and errors.

### 9.4 ATS Adapters

Each adapter must expose a common interface:

```text
detect(url) -> confidence
fetch_jobs(company) -> list[RawJob]
fetch_job_detail(job_url) -> RawJobDetail
```

Initial adapters:

- Greenhouse
- Lever
- SmartRecruiters
- Generic HTML career page

Future adapters:

- Workday
- Ashby
- BambooHR
- Workable
- Pinpoint
- Recruitee
- Teamtailor

### 9.5 Job Normaliser

Requirements:

- Convert raw listings into a standard `Job` object.
- Extract title, company, location, source, URL, apply URL, posted date if available, description, and employment type.
- Preserve raw source data for debugging.

### 9.6 IT Role Classifier

MVP classifier may be rule-based.

Positive keywords:

- software engineer
- developer
- full stack
- frontend
- backend
- data engineer
- data analyst
- business analyst
- AI engineer
- machine learning
- cloud engineer
- platform engineer
- DevOps
- site reliability
- security engineer
- QA
- test engineer
- product analyst
- systems analyst

Negative keywords:

- sales only
- retail assistant
- warehouse
- driver
- nurse
- accountant
- payroll officer
- customer service only

Requirements:

- Return `is_it_related`.
- Return `role_group`.
- Return confidence score.
- Store classifier explanation.

### 9.7 Match Scoring

Score jobs from 0 to 100.

Suggested scoring:

- Role title match: 25 points
- Skill/technology match: 25 points
- Location/remote match: 15 points
- Work rights compatibility: 15 points
- Salary compatibility: 10 points
- Freshness: 10 points

Thresholds:

- 85-100: strong match
- 70-84: good match
- 55-69: possible match
- below 55: low priority

Requirements:

- Store total score.
- Store component scores.
- Store short explanation.

### 9.8 Material Generator

Requirements:

- Select relevant professional summary based on role group.
- Select relevant motivation theme.
- Generate draft short answers using `prescreen_answer_templates.md`.
- Keep answers concise.
- Mark generated answers as draft until reviewed.
- Avoid inventing experience not present in the material bank.

### 9.9 Autofill Engine

Requirements:

- Use Playwright for browser automation.
- Detect input, textarea, select, checkbox, radio, and file upload fields.
- Match field labels, placeholders, names, aria labels, and nearby text against `field_mappings`.
- Fill fields listed under `can_autofill`.
- Fill and highlight fields listed under `autofill_but_highlight_for_review`.
- Pause on fields listed under `must_pause`.
- Never click final submit when `never_click_final_submit` is true.

### 9.10 Review Screen

MVP may be CLI output or local web page.

Requirements:

- Show employer and destination URL.
- Show filled fields and values.
- Show sensitive/review fields.
- Show paused/unfilled fields.
- Ask user to continue manually in browser.

### 9.11 Application Tracker

Requirements:

- Store job and application records.
- Track status.
- Store generated materials.
- Store autofill log.
- Store manual notes.
- Support status updates.

## 10. Data Model

### 10.1 Company

```text
id
company_name
website
career_url
industry
locations
priority
target_role_groups
ats_type
ats_feed_url
notes
active
last_checked_at
created_at
updated_at
```

### 10.2 Job

```text
id
external_id
title
company_id
company_name
location
remote_type
employment_type
salary_text
salary_min
salary_max
salary_currency
description
requirements
responsibilities
tech_stack
seniority
source
source_url
apply_url
posted_at
discovered_at
is_it_related
role_group
classifier_confidence
match_score
match_explanation
status
raw_data
created_at
updated_at
```

### 10.3 Application

```text
id
job_id
status
selected_cv_path
selected_cover_letter_path
generated_cover_letter
generated_screening_answers
autofill_started_at
autofill_completed_at
submitted_at
submission_confirmed_by_user
notes
created_at
updated_at
```

### 10.4 Autofill Log

```text
id
application_id
field_label
field_type
field_selector
matched_rule
value_used
action
review_required
paused
pause_reason
created_at
```

### 10.5 Source Scan

```text
id
company_id
source_type
started_at
finished_at
status
jobs_found_count
new_jobs_count
error_message
created_at
```

## 11. Status Values

### 11.1 Job Status

```text
discovered
low_priority
shortlisted
ignored
prepared
autofill_ready
applied
archived
```

### 11.2 Application Status

```text
draft
prepared
autofill_started
paused_for_review
ready_for_manual_submit
submitted
replied
interview
offer
rejected
withdrawn
archived
```

## 12. Autofill Policy

### 12.1 Default Behaviour

The system must:

- Fill safe fields automatically.
- Highlight review fields.
- Pause on sensitive or unknown fields.
- Save a screenshot/log before final submit.
- Never click final submit by default.

### 12.2 Can Autofill

Examples:

- Name
- Email
- Phone
- Location
- Portfolio
- Website
- GitHub
- Current country
- Currently in New Zealand
- Work rights
- Sponsorship requirement
- Visa expiry
- Earliest start date
- Notice period
- Remote work preference
- Relocation/travel preference
- Privacy statement consent
- Truthful information declaration

### 12.3 Autofill But Highlight For Review

Examples:

- Salary expectation
- Minimum salary
- Work rights
- Visa status
- Sponsorship
- Relocation
- Travel
- Reference checks
- Criminal record check
- Police vet
- Health or wellbeing adjustments
- Privacy consent
- Declaration

### 12.4 Must Pause

Examples:

- Passport number
- Driver licence number
- National ID
- IRD number
- Date of birth
- Full legal name when missing
- Referee names/contact details
- Criminal record details
- Health condition details
- Disability/accommodation details
- Conflict of interest
- Custom screening questions without matching reusable answer
- CAPTCHA
- Login required
- Payment required
- Unclear or unmapped field

## 13. Safety, Privacy, And Compliance

### 13.1 Platform Behaviour

The system must:

- Prefer official APIs, feeds, sitemaps, or public ATS endpoints.
- Avoid bypassing anti-bot controls.
- Avoid excessive request frequency.
- Respect site restrictions where known.
- Avoid scraping private or authenticated pages unless the user manually logs in and the flow remains user-controlled.

### 13.2 Personal Data Handling

The system stores sensitive personal information. It must:

- Store data locally for MVP.
- Avoid committing secrets or private documents.
- Avoid logging unnecessary sensitive values.
- Allow deletion of application records.
- Keep uploaded files and generated materials organised.

### 13.3 Submission Control

The system must:

- Require user review before final submission.
- Show destination employer and URL.
- Show sensitive values.
- Keep an audit log.

## 14. Notification Requirements

MVP:

- CLI or dashboard notification is enough.

Future:

- Email notification.
- Telegram notification.
- Daily digest.
- Immediate alert for match score above 90.

Notification content:

```text
Company
Title
Location
Source
Match score
Reason for recommendation
Apply URL
```

## 15. Dashboard Requirements

Dashboard can be postponed until after CLI MVP. When built, it should include:

1. Job queue
2. Filters by status, score, company, role group, location
3. Job detail view
4. Application preparation view
5. Autofill launch button
6. Application status tracker
7. Settings view for source files and scan frequency

## 16. Technical Architecture

### 16.1 Recommended Stack

Backend:

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL or SQLite for MVP

Automation:

- Playwright

Scheduling:

- APScheduler for MVP
- Celery/RQ later if needed

Frontend:

- CLI first for MVP
- React/Next.js dashboard later

Configuration:

- YAML files

LLM:

- Optional in MVP
- Use later for job parsing, scoring explanation, cover letter generation, and screening answers

### 16.2 Suggested Folder Structure

```text
nz_it_job_application_automation/
  PRD.md
  job_application_material_bank.md
  application_autofill_rules.yaml
  nz_it_company_targets.yaml
  prescreen_answer_templates.md
  README.md
  pyproject.toml
  app/
    main.py
    config/
      loader.py
      schemas.py
    db/
      models.py
      session.py
      migrations/
    sources/
      base.py
      greenhouse.py
      lever.py
      smartrecruiters.py
      generic_html.py
    jobs/
      normalizer.py
      classifier.py
      scorer.py
      deduper.py
    applications/
      materials.py
      tracker.py
      autofill.py
      review.py
    browser/
      playwright_runner.py
      field_detector.py
      field_matcher.py
    cli/
      commands.py
  data/
    generated/
    screenshots/
    logs/
  tests/
```

## 17. Current Progress

Last updated: 2026-06-26

### 17.1 Completed

Phase 0: Project Setup is complete.

Completed deliverables:

- Created project structure under `nz_it_job_application_automation/`.
- Added `README.md`.
- Added `pyproject.toml`.
- Added configuration loader in `app/config/loader.py`.
- Added configuration schema helpers in `app/config/schemas.py`.
- Added tests for loading source configuration files.
- Verified all four source files can be loaded:
  - `job_application_material_bank.md`
  - `application_autofill_rules.yaml`
  - `nz_it_company_targets.yaml`
  - `prescreen_answer_templates.md`

Verification result:

```text
Config OK: 115 companies loaded
```

Phase 1: Data Models And Local Storage is complete.

Completed deliverables:

- Added SQLAlchemy database models in `app/db/models.py`.
- Added SQLite engine/session helpers in `app/db/session.py`.
- Added company import logic in `app/db/importers.py`.
- Added CLI commands in `app/cli/__main__.py`:
  - `validate-config`
  - `init-db`
  - `import-companies`
  - `db-summary`
- Created local SQLite database at `data/jobs.sqlite3`.
- Imported 115 company targets from `nz_it_company_targets.yaml`.
- Added idempotent company import test.

Verification result:

```text
companies: 115
jobs: 0
applications: 0
autofill_logs: 0
source_scans: 0
2 passed
```

Phase 2: Job Ingestion MVP is complete for the first local end-to-end implementation.

Completed deliverables:

- Added source parsing package under `app/sources/`.
- Added generic HTML and JSON-LD `JobPosting` parser in `app/sources/generic_html.py`.
- Added `RawJob` source DTO in `app/sources/base.py`.
- Added job normalisation in `app/jobs/normalizer.py`.
- Added idempotent job upsert logic in `app/db/job_repository.py`.
- Added CLI command:
  - `ingest-job`
- Added tests for:
  - JSON-LD `JobPosting` parsing
  - generic HTML fallback parsing
  - duplicate job ingestion handling
- Added local sample job fixture at `tests/fixtures/sample_job.html`.
- Verified local end-to-end ingestion into SQLite.

Verification result:

```text
Job created: #1 Software Engineer
Job updated: #1 Software Engineer
companies: 115
jobs: 1
applications: 0
autofill_logs: 0
source_scans: 0
5 passed
```

Phase 3: Classification And Scoring is complete for the first rule-based implementation.

Completed deliverables:

- Added rule-based IT role classifier in `app/jobs/classifier.py`.
- Added match scoring engine in `app/jobs/scorer.py`.
- Supported role groups:
  - software
  - data
  - data_analyst
  - ai
  - cloud
  - security
  - qa
  - product
  - business_analyst
  - analyst
  - non_it
  - unknown
- Added scoring components:
  - role title match
  - skill/technology match
  - location/remote match
  - work rights compatibility
  - salary compatibility
  - freshness
- Updated `ingest-job` so newly ingested jobs are classified and scored automatically.
- Added CLI commands:
  - `score-jobs`
  - `list-jobs`
- Added tests for software classification, non-IT classification, and strong data-job scoring.
- Re-scored existing sample job in SQLite.

Verification result:

```text
#1 | 79.0 | software | Xero | Software Engineer
8 passed
```

Phase 4: ATS Adapters is complete for the first fixture-backed implementation.

Completed deliverables:

- Added ATS/source adapter interface in `app/sources/base.py`.
- Added shared JSON fetch helper in `app/sources/http.py`.
- Added Greenhouse adapter in `app/sources/greenhouse.py`.
- Added Lever adapter in `app/sources/lever.py`.
- Added SmartRecruiters adapter in `app/sources/smartrecruiters.py`.
- Added adapter registry and source detection in `app/sources/registry.py`.
- Added company scanner in `app/sources/scanner.py`.
- Added CLI command:
  - `scan-company`
- Added fixture responses for:
  - Greenhouse
  - Lever
  - SmartRecruiters
- Added tests for adapter parsing and scan import/deduplication.
- Verified scanner writes `SourceScan` records.
- Verified scanned jobs are normalised, deduplicated, classified, scored, and stored.

Verification result:

```text
Company scanned: Xero
Jobs found: 1
New jobs: 1
#2 | 87.0 | data | Xero | Data Engineer
#1 | 79.0 | software | Xero | Software Engineer
companies: 115
jobs: 2
source_scans: 1
12 passed
```

Phase 5: Application Materials is complete for the first deterministic draft implementation.

Completed deliverables:

- Added application materials package under `app/applications/`.
- Added role-specific material selector in `app/applications/materials.py`.
- Added professional summary selection by `role_group`.
- Added motivation theme selection by `role_group`.
- Added deterministic cover letter draft generation.
- Added reusable screening answer draft generation.
- Added idempotent application preparation logic.
- Added CLI commands:
  - `prepare-application`
  - `list-applications`
- Added tests for role-specific material selection and application creation.
- Prepared a real application draft in SQLite for the stored Data Engineer sample job.

Verification result:

```text
Application created: #1
Job: #2 Data Engineer
Company: Xero
Status: prepared
Cover letter characters: 1614
#1 | prepared | job #2 | Xero | Data Engineer
companies: 115
jobs: 2
applications: 1
14 passed
```

Phase 6: Autofill MVP is complete for the first conservative local implementation.

Completed deliverables:

- Added browser/autofill package under `app/browser/`.
- Added static form field parser in `app/browser/field_detector.py`.
- Added field matching and pause/review policy in `app/browser/field_matcher.py`.
- Added autofill planning and logging in `app/browser/autofill.py`.
- Added Playwright runner in `app/browser/playwright_runner.py`.
- Added local test application form at `tests/fixtures/application_form.html`.
- Added CLI command:
  - `autofill-application`
- Added support for:
  - static `file://` autofill planning
  - Playwright browser autofill
  - safe field filling
  - review-required field highlighting
  - must-pause field handling
  - `AutofillLog` records
  - no final submit click
- Installed Playwright Python dependency and Chromium browser binary.
- Verified static autofill planning against local form.
- Verified real Playwright headless autofill against local form.

Verification result:

```text
Autofill processed for application #1
Filled: 4
Review required: 2
Paused: 1
Skipped: 0
Final submit clicked: no
companies: 115
jobs: 2
applications: 1
autofill_logs: 14
source_scans: 1
17 passed
```

Phase 7: Mode A End-To-End is complete for the first local implementation.

Completed deliverables:

- Added workflow package under `app/workflows/`.
- Added Mode A orchestrator in `app/workflows/mode_a.py`.
- Added CLI command:
  - `mode-a`
- Implemented end-to-end single-job flow:
  - ingest job URL
  - classify and score job
  - prepare application draft
  - optionally plan autofill
  - stop before final submit
- Added recommendation labels:
  - `strong_match`
  - `good_match`
  - `possible_match`
  - `low_priority`
  - review labels for non-IT/unscored jobs
- Added tests for Mode A with and without static autofill planning.
- Verified local end-to-end Mode A workflow against sample job and sample form.

Verification result:

```text
Mode A completed
Job: #1 Software Engineer
Company: Xero
Role group: software
Match score: 79.0
Recommendation: good_match
Application: #2
Job record: updated
Application record: created
Autofill filled: 4
Autofill review required: 2
Autofill paused: 1
Final submit clicked: no
companies: 115
jobs: 2
applications: 2
autofill_logs: 21
source_scans: 1
19 passed
```

Phase 8: Mode B End-To-End is complete for the first CLI queue implementation.

Completed deliverables:

- Added Mode B workflow functions in `app/workflows/mode_b.py`.
- Added recommended queue generation ordered by match score and discovery time.
- Added batch application preparation.
- Added job status update helper.
- Added batch company scan helper by priority.
- Added CLI commands:
  - `batch-scan`
  - `queue`
  - `batch-prepare`
  - `mark-job`
- Added tests for recommended queue ordering, ignored job filtering, batch preparation, and status transitions.
- Verified CLI queue, status update, and batch preparation against local SQLite data.

Verification result:

```text
#2 | 87.0 | data | discovered | Xero | Data Engineer
#1 | 79.0 | software | discovered | Xero | Software Engineer
Job #2 marked as shortlisted
Application updated: #2 | job #1 | Xero | Software Engineer
Application updated: #1 | job #2 | Xero | Data Engineer
#2 | 87.0 | data | prepared | Xero | Data Engineer
#1 | 79.0 | software | prepared | Xero | Software Engineer
companies: 115
jobs: 2
applications: 2
autofill_logs: 21
source_scans: 1
21 passed
```

Phase 9: Dashboard And Notifications is complete for the first local dashboard and digest implementation.

Completed deliverables:

- Added dashboard package under `app/dashboard/`.
- Added local HTML dashboard renderer in `app/dashboard/render.py`.
- Added daily digest text renderer.
- Added CLI commands:
  - `dashboard`
  - `daily-digest`
- Dashboard shows:
  - recommended queue
  - application status
  - prepared count
  - paused-for-review count
- Daily digest shows:
  - recommended jobs
  - recent applications
- Generated local dashboard at `data/generated/dashboard.html`.
- Kept CLI workflow as fallback.
- Added tests for dashboard and digest rendering.

Verification result:

```text
Dashboard generated: E:\vscode_proj\Codex_projs\nz_it_job_application_automation\data\generated\dashboard.html
NZ IT Job Application Daily Digest

Recommended jobs, minimum score 55:
- #2 | 87 | data | prepared | Xero | Data Engineer
- #1 | 79 | software | prepared | Xero | Software Engineer

Recent applications:
- #1 | prepared | job #2 | Xero | Data Engineer
- #2 | prepared | job #1 | Xero | Software Engineer
23 passed
```

Post-MVP live smoke testing has started.

Completed smoke-test deliverables:

- Found and verified a real public SmartRecruiters ATS source:
  - Company: Partly
  - Source: `https://api.smartrecruiters.com/v1/companies/Partly/postings`
- Ran `scan-company` against the real Partly source.
- Ran `mode-a` against a real public Partly job page:
  - `https://jobs.smartrecruiters.com/Partly/743999880344528-senior-software-engineer-typescript`
- Backfilled Partly `ats_type` and `ats_feed_url` in `nz_it_company_targets.yaml`.
- Re-imported company targets into SQLite.
- Fixed a real-page parser bug caused by meta tags without `name`, `property`, or `itemprop`.
- Fixed SmartRecruiters company-name fallback so URLs under `jobs.smartrecruiters.com/{company}/...` use the company slug.
- Added regression test for SmartRecruiters company detection.
- Improved SmartRecruiters generated posting URLs.
- Improved job upsert deduplication so identical `source_url` records can update across source adapters.
- Archived the duplicate Partly job created before the dedupe fix.
- Updated dashboard/digest filtering so archived and ignored jobs are excluded from recommendations.
- Added visible-browser review options for real ATS pages:
  - `--keep-open`
  - `--keep-open-seconds`
  - `--captcha-wait-seconds`
- Added CAPTCHA/bot-verification detection for real browser autofill.
- Added manual verification pause handling:
  - The system waits for the user to complete verification.
  - The system does not bypass or solve CAPTCHA automatically.
  - If verification is still present after the wait window, the application is marked `paused_for_review`.
  - A pause log is written to `autofill_logs` with `pause_reason=captcha_or_bot_verification`.
- Added access-limit handling for SmartRecruiters-style blocks:
  - Chinese/English "access temporarily limited" pages are detected.
  - These pages are treated as manual handoff, not as successful autofill.
  - A pause log is written with `pause_reason=access_limited_or_bot_blocked`.
- Added manual application assist workflow:
  - CLI command: `manual-assist --url "<job-or-application-url>"`.
  - Matches manually opened job/application URLs to existing jobs.
  - Supports SmartRecruiters one-click URLs by matching URL tokens such as publication UUIDs.
  - Prepares or refreshes application materials.
  - Marks the application `manual_apply_in_progress`.
  - Generates a copy/paste Markdown file under `data/generated/`.
- Added manual application link discovery:
  - CLI command: `manual-queue --minimum-score 55 --limit 10`.
  - Shows the exact job/application URL the user should open manually.
  - Prints the matching `manual-assist` command for each recommended job.
  - Dashboard recommended queue now includes an explicit `Open` link and assist command.
- Added company source discovery:
  - CLI command: `discover-company-source --company "<company>"`.
  - CLI command: `discover-company-sources --max-priority 1 --limit 10`.
  - Batch discovery can write a Markdown report with `--output`.
  - Detects Greenhouse, Lever, and SmartRecruiters links from career pages.
  - Detects login/account-required pages and marks them as manual handoff candidates.
  - Falls back to `generic_html` when a career page appears to list jobs but no supported ATS feed is found.
  - Discovery prints suggestions only; it does not write to `nz_it_company_targets.yaml` yet.
- Added conservative generic HTML source scanning:
  - Registered `generic_html` as a scan adapter.
  - `scan-company` now accepts `--source-type generic_html`.
  - Extracts likely job links from ordinary careers pages.
  - Parses each linked job page with the existing generic/JSON-LD job parser.
  - Caps linked job parsing to 25 links per source to avoid over-scanning.
- Confirmed and wrote back three supported ATS sources:
  - ClearPoint: Lever, `https://api.lever.co/v0/postings/clearpoint?mode=json`
  - Deloitte New Zealand: SmartRecruiters, `https://api.smartrecruiters.com/v1/companies/DeloitteNZ/postings`
  - KPMG New Zealand: Lever, `https://api.lever.co/v0/postings/kpmgnz?mode=json`
- Verified automatic batch scan after writing sources back:
  - Command: `batch-scan --max-priority 2 --limit 60`
  - Companies with jobs scanned: 3
  - Jobs found: 142
  - New jobs: 0 after prior smoke scans, confirming dedupe works.
- Added manual daily scan workflow:
  - CLI command: `run-daily-scan --max-priority 2 --limit 60 --minimum-score 55`.
  - Imports company config.
  - Runs batch scan.
  - Re-scores all jobs.
  - Regenerates dashboard.
  - Prints daily digest.
  - Recommended frequency before scheduler automation: twice daily, around 09:00 and 16:00 NZ time.
- Verified real daily scan:
  - Companies imported: 0 created, 115 updated
  - Companies with jobs scanned: 3
  - Jobs found: 142
  - New jobs: 2
  - Jobs scored: 173
  - Recommended jobs: 33
- Tightened recommendation filtering:
  - Default dashboard, digest, queue, and manual queue now focus on core role groups: software, data, data_analyst, business_analyst, AI, cloud, security, QA, and product.
  - Broad analyst roles can still be viewed explicitly with `--role-group analyst`.
  - Added non-core title exclusions for advisory, deal advisory, M&A, management consulting, enterprise risk, transaction services, early careers, and related titles.
  - Re-scored existing jobs and refreshed dashboard after the rule change.
- Added application status management:
  - CLI command: `mark-application <application-id> <status>`.
  - Supported statuses include prepared, manual_apply_in_progress, ready_for_manual_submit, paused_for_review, submitted, rejected, withdrawn, follow_up, and archived.
  - Marking an application `submitted` records `submitted_at`, sets `submission_confirmed_by_user`, and marks the related job as `applied`.
  - Dashboard Applications table now shows submitted time and submitted/follow-up summary counts.
- Added dashboard next-action guidance:
  - Recommended Queue now includes a `Next Action` column instead of a bare assist command.
  - Applications table now includes a `Next Action` column.
  - Prepared/manual-in-progress applications show the exact `mark-application ... submitted` command.
  - Paused/submitted/follow-up/rejected/withdrawn states show status-specific next steps.
- Added focused analyst role groups:
  - `data_analyst` covers Data Analyst, Reporting Analyst, Business Intelligence Analyst, and BI Analyst titles.
  - `business_analyst` covers Business Analyst, Systems Analyst, Technical Analyst, Digital Analyst, and Process Analyst titles.
  - These two focused analyst groups now appear in the default dashboard/recommended/manual queues.
  - Generic `analyst` remains excluded from default recommendations to avoid broad/non-target analyst noise.
  - Re-scored 173 existing jobs and refreshed `data/generated/dashboard.html`; current recommended jobs count is 21.
- Added SEEK recommendation email import, option B:
  - User saves SEEK recommendation emails as `.eml`, `.html`, or `.htm` files under `data/seek_emails/`.
  - CLI command: `import-seek-email <path>` for one saved email.
  - CLI command: `import-seek-email-folder <path>` for a folder of saved emails.
  - Parser extracts job title, company, location, SEEK URL, and short card description from email HTML body.
  - Imported jobs use source `seek_email`, are deduplicated by URL, classified, scored, and shown in the local dashboard.
  - This avoids direct Gmail login and keeps mailbox access out of the MVP.
- Added Jora saved-page import:
  - User saves Jora search result or job pages as `.html` / `.htm` files under `data/jora_pages/`.
  - CLI command: `import-jora-html <path>` for one saved page.
  - CLI command: `import-jora-html-folder <path>` for a folder of saved pages.
  - Parser extracts visible job cards, company, location, Jora URL, and description snippets.
  - Imported jobs use source `jora_html`, are deduplicated by URL, classified, scored, and shown in the local dashboard.
  - The importer remains file-based for MVP safety instead of automated account/session scraping.

Verification result:

```text
Company scanned: Partly
Jobs found: 1
New jobs: 1

Mode A completed
Job: #4 Senior Software Engineer | Typescript
Company: Partly
Role group: software
Match score: 66.5
Recommendation: possible_match
Application: #3
Job record: updated
Application record: updated

Recommended jobs, minimum score 55:
- #2 | 87 | data | prepared | Xero | Data Engineer
- #1 | 79 | software | prepared | Xero | Software Engineer
- #4 | 66.5 | software | discovered | Partly | Senior Software Engineer | Typescript

24 passed
```

### 17.2 In Progress

No phase is currently in progress.

### 17.3 Next Phase

Post-MVP: Live Smoke Testing And Hardening.

Next deliverables:

- Smoke-test additional real public job URLs across different ATS providers.
- Smoke-test a real Greenhouse source.
- Smoke-test a real Lever source.
- Add company ATS enrichment for selected priority target companies.
- Add optional email or Telegram delivery for the daily digest.
- Add generated material preview/export.
- Improve real-form field detection based on observed ATS pages.
- Consider a local API/dashboard only after live smoke tests are stable.

### 17.4 Notes And Constraints

- Runtime writes to the project SQLite database may require elevated permission in the current sandbox environment.
- Tests pass using temporary writable test databases.
- The workspace `.git` directory currently does not behave as a valid Git repository, so Git status is not available yet.
- Phase 2 has been verified with a local `file://` fixture. Live external URL ingestion should be smoke-tested with a real public job URL when ready.
- Phase 4 has been verified with local ATS JSON fixtures. Live Greenhouse/Lever/SmartRecruiters endpoints should be smoke-tested with real public company sources when ready.
- Phase 5 uses deterministic template-based generation. LLM-assisted tailoring remains future scope.
- Phase 6 has been verified with a local form fixture. Real ATS application pages should be smoke-tested carefully and manually reviewed before use.
- Real ATS verification/CAPTCHA screens are treated as manual handoff points. The product must pause, wait, and log review status; bypassing verification is out of scope.
- Phase 7 has been verified locally. Live Mode A should be smoke-tested with one public job URL before regular use.
- Phase 8 has been verified with local stored jobs. Live batch scans depend on companies having supported public ATS URLs configured.
- Phase 9 currently generates a local static dashboard and terminal digest. Email/Telegram delivery remains future scope.
- Automatic final submission remains out of scope.

## 18. Development Plan

### Phase 0: Project Setup

Deliverables:

- Create project structure.
- Add README.
- Add dependency file.
- Add config loader.
- Add basic tests for loading YAML files.

Done when:

- Running the config loader successfully reads all source files.
- Tests pass.

### Phase 1: Data Models And Local Storage

Deliverables:

- Database setup.
- Company, Job, Application, AutofillLog, SourceScan models.
- Import companies from YAML into database.

Done when:

- Companies can be imported.
- Duplicate import does not create duplicates.

### Phase 2: Job Ingestion MVP

Deliverables:

- Manual URL ingestion.
- Generic HTML job parser.
- Job normaliser.

Done when:

- User can add one job URL.
- System stores a normalised job record.

### Phase 3: Classification And Scoring

Deliverables:

- Rule-based IT classifier.
- Match scoring engine.
- Job queue sorting.

Done when:

- Jobs receive role group and match score.
- Queue displays strongest matches first.

### Phase 4: ATS Adapters

Deliverables:

- Greenhouse adapter.
- Lever adapter.
- SmartRecruiters adapter.
- Source scan records.

Done when:

- At least three source types can fetch jobs.
- New jobs are deduplicated.

### Phase 5: Application Materials

Deliverables:

- Material selector.
- Role-specific summary selection.
- Screening answer draft generation from templates.

Done when:

- Each shortlisted job can produce an application draft.
- Drafts do not invent facts outside the material bank.

### Phase 6: Autofill MVP

Deliverables:

- Playwright launcher.
- Field detection.
- Field mapping from YAML rules.
- Safe autofill.
- Pause before final submit.

Done when:

- A test form can be filled using profile data.
- Sensitive fields pause.
- Final submit is not clicked.

### Phase 7: Mode A End-To-End

Deliverables:

- CLI command or minimal local endpoint for one URL.
- Job parse -> score -> draft -> autofill.

Done when:

- User can process a single job URL end to end.

### Phase 8: Mode B End-To-End

Deliverables:

- Scheduled source scan.
- Daily queue.
- Batch selection.
- Process selected jobs.

Done when:

- System scans company sources and builds a recommended queue.

### Phase 9: Dashboard And Notifications

Deliverables:

- Local dashboard.
- Daily digest.
- Job status update UI.

Done when:

- User can manage applications without using CLI directly.

## 19. Acceptance Criteria For MVP

MVP is complete when:

1. System loads all four source files.
2. System stores company targets.
3. User can add a single job URL.
4. System normalises job data.
5. System classifies IT relevance.
6. System calculates match score.
7. System creates an application draft.
8. System can autofill a representative web form.
9. System pauses on sensitive fields.
10. System never clicks final submit.
11. System tracks job/application status.
12. At least three ATS/source adapters are functional or stubbed with clear extension points.

## 20. Success Metrics

### 20.1 Efficiency Metrics

- Time to prepare one application reduced by at least 50%.
- Daily recommended queue generated automatically.
- Duplicate job discovery rate below 5%.

### 20.2 Quality Metrics

- Autofill accuracy above 90% for standard fields.
- Zero accidental final submissions.
- Zero known sensitive-field autofill without review.

### 20.3 Job Search Metrics

- Number of relevant jobs discovered per week.
- Number of applications prepared per week.
- Number of applications submitted after review.
- Response/interview rate.

## 21. Open Questions

1. Which CV file should be used by default?
2. Should cover letters be generated as Markdown, PDF, DOCX, or plain text?
3. Should SQLite be used for MVP, then PostgreSQL later?
4. Which notification channel should be first: email, Telegram, or dashboard only?
5. Should the first UI be CLI only, or a minimal local web dashboard?
6. Should salary filtering be strict or advisory?
7. Which companies should be priority 1 after the first week of real scan results?

## 22. Implementation Rules

1. Build in small phases.
2. Verify each phase before moving to the next.
3. Keep source YAML/Markdown files human-editable.
4. Do not hardcode personal facts in application code; read them from configuration files.
5. Keep browser automation conservative.
6. Log enough for review, but do not over-log sensitive personal data.
7. Do not implement automatic final submission until explicitly approved in a future PRD update.
