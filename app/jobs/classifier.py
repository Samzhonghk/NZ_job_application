from __future__ import annotations

from dataclasses import dataclass

from app.db.models import Job


@dataclass(frozen=True)
class ClassificationResult:
    is_it_related: bool
    role_group: str
    confidence: float
    explanation: str


ROLE_KEYWORDS: dict[str, list[str]] = {
    "software": [
        "software engineer",
        "software developer",
        "developer",
        "full stack",
        "frontend",
        "front end",
        "backend",
        "back end",
        "web developer",
        "application developer",
        "java",
        "python",
        "javascript",
        "typescript",
        "react",
        "node",
    ],
    "data": [
        "data engineer",
        "analytics engineer",
        "sql",
        "etl",
        "pipeline",
        "bigquery",
        "warehouse",
        "spark",
        "kafka",
    ],
    "data_analyst": [
        "data analyst",
        "reporting analyst",
        "business intelligence analyst",
        "bi analyst",
        "business intelligence",
        "power bi",
        "dashboard",
        "reporting",
        "analytics",
    ],
    "ai": [
        "ai engineer",
        "artificial intelligence",
        "machine learning",
        "ml engineer",
        "llm",
        "rag",
        "prompt engineer",
        "data scientist",
    ],
    "cloud": [
        "cloud engineer",
        "platform engineer",
        "devops",
        "site reliability",
        "sre",
        "aws",
        "azure",
        "gcp",
        "kubernetes",
        "terraform",
        "infrastructure",
    ],
    "security": [
        "security engineer",
        "cybersecurity",
        "cyber security",
        "security analyst",
        "identity",
        "iam",
        "soc analyst",
    ],
    "qa": [
        "qa engineer",
        "quality assurance",
        "test engineer",
        "automation tester",
        "software tester",
    ],
    "product": [
        "product manager",
        "product owner",
        "product analyst",
        "technical product",
    ],
    "business_analyst": [
        "business analyst",
        "systems analyst",
        "technical analyst",
        "digital analyst",
        "process analyst",
        "reporting analyst",
        "requirements",
        "stakeholder",
        "user stories",
        "business requirements",
    ],
    "analyst": [
        "analyst",
    ],
}

TITLE_ROLE_OVERRIDES: dict[str, list[str]] = {
    "data_analyst": [
        "data analyst",
        "reporting analyst",
        "business intelligence analyst",
        "bi analyst",
    ],
    "business_analyst": [
        "business analyst",
        "systems analyst",
        "technical analyst",
        "digital analyst",
        "process analyst",
    ],
}

NEGATIVE_KEYWORDS = [
    "retail assistant",
    "store manager",
    "warehouse assistant",
    "driver",
    "nurse",
    "accountant",
    "accounts receivable",
    "accounts payable",
    "payroll officer",
    "customer service representative",
    "sales consultant",
    "chef",
    "mechanic",
]
NEGATIVE_TITLE_KEYWORDS = [
    "personal assistant",
    "executive assistant",
    "accounts receivable",
    "accounts payable",
    "payroll",
    "office administrator",
    "receptionist",
    "advisory",
    "deal advisory",
    "enterprise advisory",
    "management consulting",
    "m&a",
    "transaction services",
    "turnaround & restructuring",
    "enterprise risk",
    "early careers manager",
    "auditor",
    "internal auditor",
    "insolvency",
    "ethics and independence",
]


def classify_job(job: Job) -> ClassificationResult:
    text = _job_text(job)
    title = (job.title or "").lower()
    negative_title_hits = _hits(title, NEGATIVE_TITLE_KEYWORDS)
    if negative_title_hits:
        return ClassificationResult(
            is_it_related=False,
            role_group="non_it",
            confidence=0.9,
            explanation=f"Matched non-IT title keywords: {', '.join(negative_title_hits[:5])}",
        )
    title_override = _title_role_override(title)
    if title_override:
        return ClassificationResult(
            is_it_related=True,
            role_group=title_override,
            confidence=0.9,
            explanation=f"Matched {title_override} title pattern.",
        )

    negative_hits = _hits(text, NEGATIVE_KEYWORDS)
    role_hits = {
        role_group: _hits(text, keywords)
        for role_group, keywords in ROLE_KEYWORDS.items()
    }
    role_hits = {role_group: hits for role_group, hits in role_hits.items() if hits}

    if not role_hits:
        if negative_hits:
            return ClassificationResult(
                is_it_related=False,
                role_group="non_it",
                confidence=0.85,
                explanation=f"Matched non-IT keywords: {', '.join(negative_hits[:5])}",
            )
        return ClassificationResult(
            is_it_related=False,
            role_group="unknown",
            confidence=0.25,
            explanation="No strong IT role keywords matched.",
        )

    best_role = max(role_hits, key=lambda group: (len(role_hits[group]), _title_bonus(job, role_hits[group])))
    best_hits = role_hits[best_role]
    confidence = min(0.95, 0.45 + len(best_hits) * 0.12 + _title_bonus(job, best_hits))

    if negative_hits and confidence < 0.75:
        return ClassificationResult(
            is_it_related=False,
            role_group=best_role,
            confidence=round(confidence, 2),
            explanation=(
                f"Matched IT keywords ({', '.join(best_hits[:5])}) but also non-IT "
                f"keywords ({', '.join(negative_hits[:5])})."
            ),
        )

    return ClassificationResult(
        is_it_related=True,
        role_group=best_role,
        confidence=round(confidence, 2),
        explanation=f"Matched {best_role} keywords: {', '.join(best_hits[:6])}",
    )


def apply_classification(job: Job) -> ClassificationResult:
    result = classify_job(job)
    job.is_it_related = result.is_it_related
    job.role_group = result.role_group
    job.classifier_confidence = result.confidence
    if job.match_explanation:
        job.match_explanation = f"{result.explanation} {job.match_explanation}"
    else:
        job.match_explanation = result.explanation
    return result


def _job_text(job: Job) -> str:
    return " ".join(
        [
            job.title or "",
            job.company_name or "",
            job.location or "",
            job.description or "",
            job.requirements or "",
            job.responsibilities or "",
            job.tech_stack or "",
        ]
    ).lower()


def _hits(text: str, keywords: list[str]) -> list[str]:
    return [keyword for keyword in keywords if keyword in text]


def _title_bonus(job: Job, hits: list[str]) -> float:
    title = (job.title or "").lower()
    return 0.2 if any(hit in title for hit in hits) else 0.0


def _title_role_override(title: str) -> str:
    for role_group, keywords in TITLE_ROLE_OVERRIDES.items():
        if _hits(title, keywords):
            return role_group
    return ""
