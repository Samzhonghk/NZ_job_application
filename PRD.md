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

### 17.2 In Progress

No phase is currently in progress.

### 17.3 Next Phase

Phase 2: Job Ingestion MVP.

Next deliverables:

- Add manual job URL ingestion command.
- Fetch a public job page.
- Extract basic job fields:
  - title
  - company
  - location
  - description
  - source URL
  - apply URL when available
- Normalise the extracted data into the `Job` model.
- Store the job in SQLite.
- Add tests for normalisation and duplicate handling.

### 17.4 Notes And Constraints

- Runtime writes to the project SQLite database may require elevated permission in the current sandbox environment.
- Tests pass using temporary writable test databases.
- The workspace `.git` directory currently does not behave as a valid Git repository, so Git status is not available yet.
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
