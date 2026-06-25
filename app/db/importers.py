from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.schemas import ProjectConfig
from app.db.models import Company


def import_companies(config: ProjectConfig, session: Session) -> tuple[int, int]:
    created = 0
    updated = 0

    for item in config.companies:
        company_name = str(item["company_name"]).strip()
        existing = session.scalar(select(Company).where(Company.company_name == company_name))

        values = _company_values(item)
        if existing is None:
            session.add(Company(company_name=company_name, **values))
            created += 1
        else:
            for key, value in values.items():
                setattr(existing, key, value)
            updated += 1

    session.commit()
    return created, updated


def _company_values(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "website": _string(item.get("website")),
        "career_url": _string(item.get("career_url")),
        "industry": _string(item.get("industry")),
        "locations": json.dumps(item.get("locations", []), ensure_ascii=True),
        "priority": int(item.get("priority") or 3),
        "target_role_groups": json.dumps(item.get("target_role_groups", []), ensure_ascii=True),
        "ats_type": _string(item.get("ats_type")),
        "ats_feed_url": _string(item.get("ats_feed_url")),
        "notes": _string(item.get("notes")),
        "active": True,
    }


def _string(value: Any) -> str:
    return "" if value is None else str(value)

