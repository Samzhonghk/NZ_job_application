from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.schemas import ProjectConfig
from app.db.models import Application, Job


@dataclass(frozen=True)
class MaterialDraft:
    summary: str
    motivation: str
    cover_letter: str
    screening_answers: dict[str, str]


SUMMARY_BY_ROLE_GROUP = {
    "software": "software_engineer",
    "ai": "ai_engineer",
    "data": "data_engineer",
    "data_analyst": "data_engineer",
    "cloud": "software_engineer",
    "security": "software_engineer",
    "qa": "software_engineer",
    "product": "main",
    "business_analyst": "main",
    "analyst": "main",
}

MOTIVATION_BY_ROLE_GROUP = {
    "software": "software_engineering",
    "ai": "ai_engineering",
    "data": "data_engineering",
    "data_analyst": "data_engineering",
    "cloud": "software_engineering",
    "security": "software_engineering",
    "qa": "software_engineering",
    "product": "career_stage",
    "business_analyst": "data_or_business_analysis",
    "analyst": "data_or_business_analysis",
}


def build_material_draft(job: Job, config: ProjectConfig) -> MaterialDraft:
    summary = select_summary(job, config)
    motivation = select_motivation(job, config)
    reusable_answers = config.autofill_rules.get("reusable_answers", {})

    screening_answers = {
        "interest_and_motivation": _interest_answer(job, motivation),
        "strengths_and_experience": _strengths_answer(job, summary),
        "work_rights": str(reusable_answers.get("work_rights", "")),
        "health_and_wellbeing": str(reusable_answers.get("health_and_wellbeing", "")),
        "salary_expectations": str(reusable_answers.get("salary_expectations", "")),
        "declaration": str(reusable_answers.get("declaration", "")),
    }

    return MaterialDraft(
        summary=summary,
        motivation=motivation,
        cover_letter=_cover_letter(job, summary, motivation),
        screening_answers=screening_answers,
    )


def prepare_application(job: Job, config: ProjectConfig, session: Session) -> tuple[Application, bool]:
    existing = session.scalar(select(Application).where(Application.job_id == job.id))
    draft = build_material_draft(job, config)

    values = {
        "status": "prepared",
        "generated_cover_letter": draft.cover_letter,
        "generated_screening_answers": json.dumps(draft.screening_answers, ensure_ascii=True, indent=2),
        "notes": _notes(job, draft),
    }

    if existing is not None:
        for key, value in values.items():
            setattr(existing, key, value)
        session.commit()
        session.refresh(existing)
        return existing, False

    application = Application(job_id=job.id, **values)
    session.add(application)
    session.commit()
    session.refresh(application)
    return application, True


def select_summary(job: Job, config: ProjectConfig) -> str:
    summaries = config.autofill_rules.get("professional_summaries", {})
    key = SUMMARY_BY_ROLE_GROUP.get(job.role_group or "", "main")
    return str(summaries.get(key) or summaries.get("main") or "")


def select_motivation(job: Job, config: ProjectConfig) -> str:
    motivations = config.autofill_rules.get("motivation_themes", {})
    key = MOTIVATION_BY_ROLE_GROUP.get(job.role_group or "", "career_stage")
    return str(motivations.get(key) or motivations.get("career_stage") or "")


def _interest_answer(job: Job, motivation: str) -> str:
    return (
        f"I am interested in the {job.title} role at {job.company_name or 'your organisation'} "
        f"because it aligns with the kind of practical, useful technology work I am looking for. "
        f"{motivation}"
    )


def _strengths_answer(job: Job, summary: str) -> str:
    return (
        f"For this {job.role_group or 'technology'} role, I would bring structured problem-solving, "
        f"careful technical execution, and a practical focus on useful outcomes. {summary}"
    )


def _cover_letter(job: Job, summary: str, motivation: str) -> str:
    company = job.company_name or "your team"
    return "\n\n".join(
        [
            f"Dear {company} hiring team,",
            f"I am writing to express my interest in the {job.title} role. {motivation}",
            summary,
            (
                "My background includes software development, data engineering, automation, cloud-based "
                "workflows, and practical AI-assisted delivery. I enjoy turning ambiguous requirements into "
                "working systems, improving data and process reliability, and building tools that are useful "
                "for the people who depend on them."
            ),
            (
                "I am currently based in Auckland, hold New Zealand Permanent Resident status, and do not "
                "require employer sponsorship. I would welcome the opportunity to discuss how my experience "
                "could support this role."
            ),
            "Kind regards,\nSam",
        ]
    )


def _notes(job: Job, draft: MaterialDraft) -> str:
    return (
        f"Prepared draft for job #{job.id}. "
        f"Role group: {job.role_group or 'unknown'}. "
        f"Summary length: {len(draft.summary)}. "
        f"Screening answers: {len(draft.screening_answers)}."
    )
