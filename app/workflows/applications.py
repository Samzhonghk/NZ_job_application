from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Application, utc_now


APPLICATION_STATUSES = [
    "draft",
    "prepared",
    "manual_apply_in_progress",
    "ready_for_manual_submit",
    "paused_for_review",
    "submitted",
    "rejected",
    "withdrawn",
    "follow_up",
    "archived",
]


def mark_application_status(
    session: Session,
    application_id: int,
    status: str,
    note: str = "",
) -> Application | None:
    if status not in APPLICATION_STATUSES:
        raise ValueError(f"Unsupported application status: {status}")

    application = session.get(Application, application_id)
    if application is None:
        return None

    application.status = status
    if status == "submitted":
        application.submitted_at = application.submitted_at or utc_now()
        application.submission_confirmed_by_user = True
        application.job.status = "applied"
    if note:
        separator = "\n" if application.notes else ""
        application.notes = f"{application.notes}{separator}{note}"
    session.commit()
    session.refresh(application)
    return application
