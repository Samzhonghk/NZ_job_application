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

## Tests

```powershell
pytest
```

