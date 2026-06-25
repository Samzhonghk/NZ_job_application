from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    website: Mapped[str] = mapped_column(Text, default="")
    career_url: Mapped[str] = mapped_column(Text, default="")
    industry: Mapped[str] = mapped_column(String(255), default="")
    locations: Mapped[str] = mapped_column(Text, default="[]")
    priority: Mapped[int] = mapped_column(Integer, default=3)
    target_role_groups: Mapped[str] = mapped_column(Text, default="[]")
    ats_type: Mapped[str] = mapped_column(String(100), default="")
    ats_feed_url: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    jobs: Mapped[list["Job"]] = relationship(back_populates="company")
    source_scans: Mapped[list["SourceScan"]] = relationship(back_populates="company")


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source", "source_url", name="uq_jobs_source_source_url"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), default="")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    company_name: Mapped[str] = mapped_column(String(255), default="")
    location: Mapped[str] = mapped_column(String(500), default="")
    remote_type: Mapped[str] = mapped_column(String(100), default="")
    employment_type: Mapped[str] = mapped_column(String(100), default="")
    salary_text: Mapped[str] = mapped_column(String(500), default="")
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(20), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    requirements: Mapped[str] = mapped_column(Text, default="")
    responsibilities: Mapped[str] = mapped_column(Text, default="")
    tech_stack: Mapped[str] = mapped_column(Text, default="[]")
    seniority: Mapped[str] = mapped_column(String(100), default="")
    source: Mapped[str] = mapped_column(String(100), default="")
    source_url: Mapped[str] = mapped_column(Text, default="")
    apply_url: Mapped[str] = mapped_column(Text, default="")
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    is_it_related: Mapped[bool] = mapped_column(Boolean, default=False)
    role_group: Mapped[str] = mapped_column(String(100), default="")
    classifier_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    match_explanation: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(100), default="discovered")
    raw_data: Mapped[str] = mapped_column(Text, default="{}")

    company: Mapped[Company | None] = relationship(back_populates="jobs")
    applications: Mapped[list["Application"]] = relationship(back_populates="job")


class Application(TimestampMixin, Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(100), default="draft")
    selected_cv_path: Mapped[str] = mapped_column(Text, default="")
    selected_cover_letter_path: Mapped[str] = mapped_column(Text, default="")
    generated_cover_letter: Mapped[str] = mapped_column(Text, default="")
    generated_screening_answers: Mapped[str] = mapped_column(Text, default="{}")
    autofill_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    autofill_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submission_confirmed_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")

    job: Mapped[Job] = relationship(back_populates="applications")
    autofill_logs: Mapped[list["AutofillLog"]] = relationship(back_populates="application")


class AutofillLog(TimestampMixin, Base):
    __tablename__ = "autofill_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), nullable=False)
    field_label: Mapped[str] = mapped_column(Text, default="")
    field_type: Mapped[str] = mapped_column(String(100), default="")
    field_selector: Mapped[str] = mapped_column(Text, default="")
    matched_rule: Mapped[str] = mapped_column(String(255), default="")
    value_used: Mapped[str] = mapped_column(Text, default="")
    action: Mapped[str] = mapped_column(String(100), default="")
    review_required: Mapped[bool] = mapped_column(Boolean, default=False)
    paused: Mapped[bool] = mapped_column(Boolean, default=False)
    pause_reason: Mapped[str] = mapped_column(Text, default="")

    application: Mapped[Application] = relationship(back_populates="autofill_logs")


class SourceScan(TimestampMixin, Base):
    __tablename__ = "source_scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), default="")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(100), default="started")
    jobs_found_count: Mapped[int] = mapped_column(Integer, default=0)
    new_jobs_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")

    company: Mapped[Company] = relationship(back_populates="source_scans")

