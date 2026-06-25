from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.config.schemas import ConfigValidationError, ProjectConfig, ProjectPaths


REQUIRED_AUTOFILL_SECTIONS = {
    "profile",
    "work_rights_and_availability",
    "target_roles",
    "salary_and_preferences",
    "autofill_policy",
    "field_mappings",
}

REQUIRED_COMPANY_KEYS = {
    "company_name",
    "website",
    "career_url",
    "industry",
    "locations",
    "priority",
    "target_role_groups",
    "ats_type",
    "ats_feed_url",
    "notes",
}


def load_project_config(root: Path | str | None = None) -> ProjectConfig:
    paths = ProjectPaths.from_root(root or Path.cwd())

    material_bank_text = _read_text(paths.material_bank)
    prescreen_templates_text = _read_text(paths.prescreen_templates)
    autofill_rules = _read_yaml_dict(paths.autofill_rules)
    company_targets = _read_yaml_dict(paths.company_targets)

    config = ProjectConfig(
        paths=paths,
        material_bank_text=material_bank_text,
        prescreen_templates_text=prescreen_templates_text,
        autofill_rules=autofill_rules,
        company_targets=company_targets,
    )
    validate_project_config(config)
    return config


def validate_project_config(config: ProjectConfig) -> None:
    _validate_non_empty_text(config.material_bank_text, "job_application_material_bank.md")
    _validate_non_empty_text(config.prescreen_templates_text, "prescreen_answer_templates.md")
    _validate_autofill_rules(config.autofill_rules)
    _validate_company_targets(config.company_targets)


def _read_text(path: Path) -> str:
    if not path.exists():
        raise ConfigValidationError(f"Missing required file: {path}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ConfigValidationError(f"Required file is empty: {path}")
    return text


def _read_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigValidationError(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ConfigValidationError(f"YAML file must contain a mapping: {path}")
    return data


def _validate_non_empty_text(text: str, name: str) -> None:
    if not text.strip():
        raise ConfigValidationError(f"{name} must not be empty")


def _validate_autofill_rules(data: dict[str, Any]) -> None:
    missing = REQUIRED_AUTOFILL_SECTIONS - set(data)
    if missing:
        raise ConfigValidationError(
            "application_autofill_rules.yaml is missing sections: "
            + ", ".join(sorted(missing))
        )

    policy = data.get("autofill_policy")
    if not isinstance(policy, dict):
        raise ConfigValidationError("autofill_policy must be a mapping")
    if policy.get("never_click_final_submit") is not True:
        raise ConfigValidationError("never_click_final_submit must be true")

    mappings = data.get("field_mappings")
    if not isinstance(mappings, dict) or not mappings:
        raise ConfigValidationError("field_mappings must be a non-empty mapping")


def _validate_company_targets(data: dict[str, Any]) -> None:
    if "metadata" not in data:
        raise ConfigValidationError("nz_it_company_targets.yaml is missing metadata")

    companies = data.get("companies")
    if not isinstance(companies, list) or not companies:
        raise ConfigValidationError("nz_it_company_targets.yaml must include companies")

    names: set[str] = set()
    for index, company in enumerate(companies, start=1):
        if not isinstance(company, dict):
            raise ConfigValidationError(f"Company entry #{index} must be a mapping")
        missing = REQUIRED_COMPANY_KEYS - set(company)
        if missing:
            name = company.get("company_name", f"entry #{index}")
            raise ConfigValidationError(
                f"Company {name!r} is missing keys: {', '.join(sorted(missing))}"
            )
        company_name = str(company["company_name"]).strip()
        if not company_name:
            raise ConfigValidationError(f"Company entry #{index} has an empty company_name")
        normalised = company_name.casefold()
        if normalised in names:
            raise ConfigValidationError(f"Duplicate company_name: {company_name}")
        names.add(normalised)

