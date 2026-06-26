from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.config.schemas import ProjectConfig
from app.db.models import Job
from app.jobs.classifier import ClassificationResult, classify_job


@dataclass(frozen=True)
class ScoreResult:
    score: float
    explanation: str
    components: dict[str, float]


PROFILE_SKILLS = [
    "python",
    "javascript",
    "typescript",
    "sql",
    "react",
    "aws",
    "gcp",
    "bigquery",
    "airflow",
    "linux",
    "ci/cd",
    "git",
    "data",
    "etl",
    "spark",
    "kafka",
    "redis",
    "hbase",
    "elasticsearch",
    "power bi",
    "excel",
    "ai",
    "automation",
    "rag",
]


def score_job(
    job: Job,
    config: ProjectConfig,
    classification: ClassificationResult | None = None,
) -> ScoreResult:
    classification = classification or classify_job(job)
    text = _job_text(job)

    role_score = _role_score(job, config, classification)
    skill_score, skill_hits = _skill_score(text)
    location_score = _location_score(job)
    work_rights_score = _work_rights_score(text, config)
    salary_score = _salary_score(job, config)
    freshness_score = _freshness_score(job)

    components = {
        "role": role_score,
        "skills": skill_score,
        "location": location_score,
        "work_rights": work_rights_score,
        "salary": salary_score,
        "freshness": freshness_score,
    }
    total = round(sum(components.values()), 1)
    explanation = _build_explanation(classification, components, skill_hits)

    return ScoreResult(score=total, explanation=explanation, components=components)


def apply_score(job: Job, config: ProjectConfig) -> ScoreResult:
    classification = classify_job(job)
    job.is_it_related = classification.is_it_related
    job.role_group = classification.role_group
    job.classifier_confidence = classification.confidence

    score = score_job(job, config, classification)
    job.match_score = score.score
    job.match_explanation = f"{classification.explanation} {score.explanation}"
    return score


def _role_score(job: Job, config: ProjectConfig, classification: ClassificationResult) -> float:
    if not classification.is_it_related:
        return 0.0

    title = (job.title or "").lower()
    target_titles = [
        str(title).lower()
        for title in config.autofill_rules.get("target_roles", {}).get("target_job_titles", [])
    ]
    if any(target in title for target in target_titles):
        return 25.0

    preferred_groups = {"software", "data", "data_analyst", "ai"}
    if classification.role_group in preferred_groups:
        return 22.0
    if classification.role_group in {"cloud", "business_analyst", "analyst"}:
        return 18.0
    return 12.0


def _skill_score(text: str) -> tuple[float, list[str]]:
    hits = [skill for skill in PROFILE_SKILLS if skill in text]
    score = min(25.0, len(hits) * 3.5)
    return round(score, 1), hits


def _location_score(job: Job) -> float:
    location_text = f"{job.location} {job.remote_type} {job.description}".lower()
    if any(term in location_text for term in ["auckland", "remote", "new zealand", "nz"]):
        return 15.0
    if any(term in location_text for term in ["wellington", "christchurch", "hamilton", "tauranga"]):
        return 12.0
    if not job.location:
        return 8.0
    return 5.0


def _work_rights_score(text: str, config: ProjectConfig) -> float:
    work_rights = config.autofill_rules.get("work_rights_and_availability", {})
    has_nz_rights = work_rights.get("nz_work_rights_status") == "Permanent Resident"
    if not has_nz_rights:
        return 5.0
    if any(term in text for term in ["citizen only", "citizenship required", "security clearance required"]):
        return 6.0
    if any(term in text for term in ["new zealand", "nz", "right to work", "work rights"]):
        return 15.0
    return 13.0


def _salary_score(job: Job, config: ProjectConfig) -> float:
    salary_config = config.autofill_rules.get("salary_and_preferences", {})
    minimum = (
        salary_config.get("minimum_acceptable", {}).get("amount")
        or salary_config.get("salary_expectation_range", {}).get("min")
        or 0
    )
    salary_text = job.salary_text or ""
    numbers = [int(match.replace(",", "")) for match in re.findall(r"\b\d[\d,]{4,}\b", salary_text)]
    if not numbers:
        return 7.0
    if max(numbers) >= int(minimum):
        return 10.0
    return 3.0


def _freshness_score(job: Job) -> float:
    reference = job.posted_at or job.discovered_at
    if reference is None:
        return 6.0
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    age_days = max(0, (datetime.now(timezone.utc) - reference).days)
    if age_days <= 2:
        return 10.0
    if age_days <= 7:
        return 8.0
    if age_days <= 21:
        return 5.0
    return 2.0


def _build_explanation(
    classification: ClassificationResult,
    components: dict[str, float],
    skill_hits: list[str],
) -> str:
    skill_text = ", ".join(skill_hits[:8]) if skill_hits else "no direct skill keywords"
    return (
        f"Score components: role {components['role']}/25, "
        f"skills {components['skills']}/25 ({skill_text}), "
        f"location {components['location']}/15, "
        f"work rights {components['work_rights']}/15, "
        f"salary {components['salary']}/10, "
        f"freshness {components['freshness']}/10. "
        f"Role group: {classification.role_group}."
    )


def _job_text(job: Job) -> str:
    return " ".join(
        [
            job.title or "",
            job.company_name or "",
            job.location or "",
            job.remote_type or "",
            job.salary_text or "",
            job.description or "",
            job.requirements or "",
            job.responsibilities or "",
            job.tech_stack or "",
        ]
    ).lower()
