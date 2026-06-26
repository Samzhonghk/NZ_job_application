from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.browser.field_detector import FormField
from app.config.schemas import ProjectConfig


@dataclass(frozen=True)
class AutofillPlanItem:
    field: FormField
    matched_rule: str
    value: str
    action: str
    review_required: bool = False
    paused: bool = False
    pause_reason: str = ""


MUST_PAUSE_KEYWORDS: dict[str, list[str]] = {
    "passport_number": ["passport"],
    "driver_licence_number": ["driver licence", "driver license"],
    "national_id": ["national id", "identity number"],
    "ird_number": ["ird", "tax number"],
    "date_of_birth": ["date of birth", "dob", "birth date"],
    "referee_names_or_contact_details": ["referee", "reference contact"],
    "criminal_record_details": ["criminal record details", "conviction details"],
    "health_condition_details": ["health condition details", "medical details"],
    "disability_or_accommodation_details": ["disability", "accommodation", "adjustment details"],
    "conflict_of_interest": ["conflict of interest"],
    "captcha": ["captcha"],
}


def build_autofill_plan(fields: list[FormField], config: ProjectConfig) -> list[AutofillPlanItem]:
    return [plan_field(field, config) for field in fields]


def plan_field(field: FormField, config: ProjectConfig) -> AutofillPlanItem:
    pause_key = _must_pause_key(field, config)
    if pause_key:
        return AutofillPlanItem(
            field=field,
            matched_rule=pause_key,
            value="",
            action="pause",
            paused=True,
            pause_reason=f"Field matches must_pause rule: {pause_key}",
        )

    matched_rule = _match_field_rule(field, config)
    if not matched_rule:
        return AutofillPlanItem(
            field=field,
            matched_rule="",
            value="",
            action="skip",
            paused=True,
            pause_reason="No mapped autofill rule matched this field.",
        )

    value_path = config.autofill_rules["field_mappings"][matched_rule].get("value_path", "")
    value = _resolve_value(config.autofill_rules, value_path)
    if value == "":
        return AutofillPlanItem(
            field=field,
            matched_rule=matched_rule,
            value="",
            action="pause",
            paused=True,
            pause_reason=f"Matched {matched_rule}, but value_path {value_path!r} is empty.",
        )

    policy = config.autofill_rules.get("autofill_policy", {})
    review_rules = set(policy.get("autofill_but_highlight_for_review", []))
    safe_rules = set(policy.get("can_autofill", []))

    if matched_rule in review_rules:
        return AutofillPlanItem(
            field=field,
            matched_rule=matched_rule,
            value=value,
            action="fill",
            review_required=True,
        )

    if matched_rule in safe_rules or matched_rule in config.autofill_rules.get("field_mappings", {}):
        return AutofillPlanItem(field=field, matched_rule=matched_rule, value=value, action="fill")

    return AutofillPlanItem(
        field=field,
        matched_rule=matched_rule,
        value=value,
        action="pause",
        paused=True,
        pause_reason=f"Matched {matched_rule}, but no autofill policy was found.",
    )


def _match_field_rule(field: FormField, config: ProjectConfig) -> str:
    text = _normalise(field.search_text)
    for rule, mapping in config.autofill_rules.get("field_mappings", {}).items():
        aliases = [rule.replace("_", " ")] + list(mapping.get("aliases", []))
        if any(_normalise(alias) in text for alias in aliases):
            return rule
    return ""


def _must_pause_key(field: FormField, config: ProjectConfig) -> str:
    text = _normalise(field.search_text)
    policy_pause = set(config.autofill_rules.get("autofill_policy", {}).get("must_pause", []))
    for key, aliases in MUST_PAUSE_KEYWORDS.items():
        if key in policy_pause and any(_normalise(alias) in text for alias in aliases):
            return key
    return ""


def _resolve_value(data: dict[str, Any], path: str) -> str:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return ""
        current = current[part]
    if isinstance(current, bool):
        return "Yes" if current else "No"
    if current is None:
        return ""
    return str(current)


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").replace("_", " ").lower()).strip()

