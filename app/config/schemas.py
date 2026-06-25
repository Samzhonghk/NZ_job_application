from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigValidationError(ValueError):
    """Raised when project configuration files are missing required data."""


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    material_bank: Path
    autofill_rules: Path
    company_targets: Path
    prescreen_templates: Path
    database: Path

    @classmethod
    def from_root(cls, root: Path | str) -> "ProjectPaths":
        root_path = Path(root).resolve()
        return cls(
            root=root_path,
            material_bank=root_path / "job_application_material_bank.md",
            autofill_rules=root_path / "application_autofill_rules.yaml",
            company_targets=root_path / "nz_it_company_targets.yaml",
            prescreen_templates=root_path / "prescreen_answer_templates.md",
            database=root_path / "data" / "jobs.sqlite3",
        )


@dataclass(frozen=True)
class ProjectConfig:
    paths: ProjectPaths
    material_bank_text: str
    prescreen_templates_text: str
    autofill_rules: dict[str, Any]
    company_targets: dict[str, Any]

    @property
    def companies(self) -> list[dict[str, Any]]:
        companies = self.company_targets.get("companies", [])
        if not isinstance(companies, list):
            raise ConfigValidationError("company_targets.companies must be a list")
        return companies

