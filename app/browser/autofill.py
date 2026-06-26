from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.browser.field_detector import FormField, parse_static_form
from app.browser.field_matcher import AutofillPlanItem, build_autofill_plan
from app.config.schemas import ProjectConfig
from app.db.models import Application, AutofillLog, utc_now


def plan_autofill_for_file(url: str, config: ProjectConfig) -> list[AutofillPlanItem]:
    path = _path_from_file_url(url)
    fields = parse_static_form(path.read_text(encoding="utf-8"))
    return build_autofill_plan(fields, config)


def record_autofill_plan(
    application: Application,
    plan: list[AutofillPlanItem],
    session: Session,
    mark_completed: bool = False,
) -> None:
    application.autofill_started_at = application.autofill_started_at or utc_now()
    for item in plan:
        session.add(
            AutofillLog(
                application_id=application.id,
                field_label=item.field.label or item.field.name or item.field.aria_label,
                field_type=item.field.field_type,
                field_selector=item.field.selector,
                matched_rule=item.matched_rule,
                value_used=item.value if item.action == "fill" else "",
                action=item.action,
                review_required=item.review_required,
                paused=item.paused,
                pause_reason=item.pause_reason,
            )
        )
    if mark_completed:
        application.autofill_completed_at = utc_now()
        application.status = "ready_for_manual_submit" if not any(item.paused for item in plan) else "paused_for_review"
    session.commit()


def record_autofill_pause(
    application: Application,
    session: Session,
    pause_reason: str,
    field_label: str = "Page verification",
) -> None:
    application.autofill_started_at = application.autofill_started_at or utc_now()
    application.status = "paused_for_review"
    session.add(
        AutofillLog(
            application_id=application.id,
            field_label=field_label,
            field_type="page",
            field_selector="document",
            matched_rule="manual_verification",
            value_used="",
            action="pause",
            review_required=True,
            paused=True,
            pause_reason=pause_reason,
        )
    )
    session.commit()


def summarise_plan(plan: list[AutofillPlanItem]) -> dict[str, int]:
    return {
        "filled": sum(1 for item in plan if item.action == "fill" and not item.review_required),
        "review_required": sum(1 for item in plan if item.review_required),
        "paused": sum(1 for item in plan if item.paused),
        "skipped": sum(1 for item in plan if item.action == "skip"),
    }


def _path_from_file_url(url: str) -> Path:
    parsed = urlparse(url)
    if parsed.scheme != "file":
        raise ValueError("Static autofill planning only supports file:// URLs")
    path = parsed.path
    if len(path) >= 3 and path[0] == "/" and path[2] == ":":
        path = path[1:]
    return Path(path)
