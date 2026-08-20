from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class SystemSetting(Base, TimestampMixin):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[Any] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(Text)


class SchemaMigration(Base):
    __tablename__ = "schema_migrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    checksum_sha256: Mapped[str] = mapped_column(String(64))
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Goal(Base, TimestampMixin):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(240), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    target_value: Mapped[float | None] = mapped_column(Float)
    current_value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(40))
    deadline: Mapped[date | None] = mapped_column(Date)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)

    tasks: Mapped[list["Task"]] = relationship(back_populates="goal")


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    strategic_value: Mapped[float] = mapped_column(Float, default=0)
    revenue_potential: Mapped[float] = mapped_column(Float, default=0)
    time_to_value: Mapped[float] = mapped_column(Float, default=0)
    cash_requirement: Mapped[float] = mapped_column(Float, default=0)
    risk_level: Mapped[float] = mapped_column(Float, default=0)
    validation_level: Mapped[float] = mapped_column(Float, default=0)
    next_action: Mapped[str | None] = mapped_column(Text)
    last_progress_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tasks: Mapped[list["Task"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    hypotheses: Mapped[list["Hypothesis"]] = relationship(back_populates="project")
    activities: Mapped[list["ProjectActivity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), index=True)
    goal_id: Mapped[int | None] = mapped_column(ForeignKey("goals.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(240), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=0, index=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(32), default="TODO", index=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer)
    actual_minutes: Mapped[int | None] = mapped_column(Integer)
    strategic_category: Mapped[str] = mapped_column(String(32), default="MAINTENANCE", index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_external_interaction: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped[Project | None] = relationship(back_populates="tasks")
    goal: Mapped[Goal | None] = relationship(back_populates="tasks")


class DailyCheckin(Base):
    __tablename__ = "daily_checkins"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    energy: Mapped[int | None] = mapped_column(Integer)
    focus: Mapped[int | None] = mapped_column(Integer)
    main_result: Mapped[str | None] = mapped_column(Text)
    what_worked: Mapped[str | None] = mapped_column(Text)
    what_failed: Mapped[str | None] = mapped_column(Text)
    blockers: Mapped[str | None] = mapped_column(Text)
    learning: Mapped[str | None] = mapped_column(Text)
    strategy_change: Mapped[str | None] = mapped_column(Text)
    feedback: Mapped[str | None] = mapped_column(Text)
    free_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Decision(Base, TimestampMixin):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(240), index=True)
    question: Mapped[str] = mapped_column(Text)
    context: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)
    importance: Mapped[str] = mapped_column(String(32), default="STANDARD", index=True)
    current_data: Mapped[str] = mapped_column(String(16), default="AUTO")
    selected_option: Mapped[str | None] = mapped_column(String(240))
    selected_option_id: Mapped[int | None] = mapped_column(Integer)
    human_rationale: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    actual_outcome: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    analysis_mode: Mapped[str | None] = mapped_column(String(40))

    options: Mapped[list["DecisionOption"]] = relationship(
        back_populates="decision", cascade="all, delete-orphan", order_by="DecisionOption.id"
    )
    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="decision", cascade="all, delete-orphan", order_by="Evidence.id"
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="decision", cascade="all, delete-orphan"
    )
    analyses: Mapped[list["AnalysisRun"]] = relationship(
        back_populates="decision", cascade="all, delete-orphan"
    )


class DecisionOption(Base, TimestampMixin):
    __tablename__ = "decision_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decisions.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str | None] = mapped_column(Text)
    expected_upside: Mapped[float | None] = mapped_column(Float)
    expected_downside: Mapped[float | None] = mapped_column(Float)
    cash_cost: Mapped[float] = mapped_column(Float, default=0)
    time_cost: Mapped[float] = mapped_column(Float, default=0)
    reversibility: Mapped[float] = mapped_column(Float, default=5)
    strategic_alignment: Mapped[float] = mapped_column(Float, default=5)
    evidence_strength: Mapped[float] = mapped_column(Float, default=5)
    execution_risk: Mapped[float] = mapped_column(Float, default=5)
    personal_pattern_risk: Mapped[float] = mapped_column(Float, default=5)
    estimated_probability: Mapped[float | None] = mapped_column(Float)
    impact_financial: Mapped[float] = mapped_column(Float, default=5)
    speed_to_result: Mapped[float] = mapped_column(Float, default=5)
    asset_value: Mapped[float] = mapped_column(Float, default=5)
    useful_learning: Mapped[float] = mapped_column(Float, default=5)
    opportunity_cost: Mapped[float] = mapped_column(Float, default=5)
    uncertainty: Mapped[float] = mapped_column(Float, default=5)
    score: Mapped[float | None] = mapped_column(Float)
    score_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    decision: Mapped[Decision] = relationship(back_populates="options")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decisions.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(240))
    content: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    source_date: Mapped[date | None] = mapped_column(Date)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    reliability: Mapped[float] = mapped_column(Float, default=0.5)
    freshness: Mapped[float] = mapped_column(Float, default=0.5)
    supports_option_id: Mapped[int | None] = mapped_column(ForeignKey("decision_options.id", ondelete="SET NULL"))
    contradicts_option_id: Mapped[int | None] = mapped_column(
        ForeignKey("decision_options.id", ondelete="SET NULL")
    )

    decision: Mapped[Decision] = relationship(back_populates="evidence")


class Hypothesis(Base, TimestampMixin):
    __tablename__ = "hypotheses"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(240), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    prior_probability: Mapped[float] = mapped_column(Float, default=0.5)
    current_probability: Mapped[float] = mapped_column(Float, default=0.5)
    status: Mapped[str] = mapped_column(String(32), default="TESTING", index=True)
    category: Mapped[str | None] = mapped_column(String(80), index=True)
    test_definition: Mapped[str | None] = mapped_column(Text)
    success_condition: Mapped[str | None] = mapped_column(Text)
    failure_condition: Mapped[str | None] = mapped_column(Text)
    test_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project | None] = relationship(back_populates="hypotheses")


class Prediction(Base, TimestampMixin):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    decision_id: Mapped[int | None] = mapped_column(ForeignKey("decisions.id", ondelete="CASCADE"), index=True)
    description: Mapped[str] = mapped_column(Text)
    probability: Mapped[float] = mapped_column(Float)
    target_date: Mapped[date] = mapped_column(Date, index=True)
    category: Mapped[str | None] = mapped_column(String(80), index=True)
    outcome: Mapped[float | None] = mapped_column(Float)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    brier_score: Mapped[float | None] = mapped_column(Float)

    decision: Mapped[Decision | None] = relationship(back_populates="predictions")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    message: Mapped[str] = mapped_column(Text)
    fingerprint: Mapped[str | None] = mapped_column(String(160), unique=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    title: Mapped[str] = mapped_column(String(240))
    content: Mapped[str] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class EntityNode(Base):
    __tablename__ = "entity_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(64), index=True)
    label: Mapped[str] = mapped_column(String(240), index=True)
    reference_type: Mapped[str | None] = mapped_column(String(64))
    reference_id: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class EntityEdge(Base):
    __tablename__ = "entity_edges"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_node_id: Mapped[int] = mapped_column(ForeignKey("entity_nodes.id", ondelete="CASCADE"), index=True)
    target_node_id: Mapped[int] = mapped_column(ForeignKey("entity_nodes.id", ondelete="CASCADE"), index=True)
    relation: Mapped[str] = mapped_column(String(100), index=True)
    weight: Mapped[float] = mapped_column(Float, default=1)


class AIUsage(Base):
    __tablename__ = "ai_usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    model: Mapped[str] = mapped_column(String(100), index=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cached_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    web_search_calls: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0)
    request_type: Mapped[str] = mapped_column(String(80), index=True)
    decision_id: Mapped[int | None] = mapped_column(ForeignKey("decisions.id", ondelete="SET NULL"), index=True)
    response_id: Mapped[str | None] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class LLMContextAudit(Base):
    __tablename__ = "llm_context_audits"

    id: Mapped[int] = mapped_column(primary_key=True)
    decision_id: Mapped[int | None] = mapped_column(ForeignKey("decisions.id", ondelete="SET NULL"), index=True)
    request_type: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(100))
    record_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    context_sha256: Mapped[str] = mapped_column(String(64))
    estimated_chars: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decisions.id", ondelete="CASCADE"), index=True)
    mode: Mapped[str] = mapped_column(String(40))
    model: Mapped[str | None] = mapped_column(String(100))
    scorecards: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    analysis: Mapped[dict[str, Any]] = mapped_column(JSON)
    red_team: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    fallback_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    decision: Mapped[Decision] = relationship(back_populates="analyses")


class ResearchRecord(Base):
    __tablename__ = "research_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    decision_id: Mapped[int | None] = mapped_column(ForeignKey("decisions.id", ondelete="CASCADE"), index=True)
    query: Mapped[str] = mapped_column(Text)
    searched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    sources: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    relevant_excerpts: Mapped[list[str]] = mapped_column(JSON, default=list)
    response_id: Mapped[str | None] = mapped_column(String(160))


class FinancialSnapshot(Base):
    __tablename__ = "financial_snapshots"
    __table_args__ = (UniqueConstraint("date", name="uq_financial_snapshot_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    cash_available: Mapped[float] = mapped_column(Float)
    monthly_income: Mapped[float] = mapped_column(Float)
    target_income: Mapped[float] = mapped_column(Float)
    experimental_spent: Mapped[float] = mapped_column(Float, default=0)
    pipeline_potential: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProjectActivity(Base):
    __tablename__ = "project_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(60), index=True)
    description: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    is_external: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped[Project] = relationship(back_populates="activities")


class ScoreWeightChange(Base):
    __tablename__ = "score_weight_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decisions.id"), index=True)
    previous_weights: Mapped[dict[str, Any]] = mapped_column(JSON)
    new_weights: Mapped[dict[str, Any]] = mapped_column(JSON)
    reason: Mapped[str] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_message: Mapped[str] = mapped_column(Text)
    assistant_answer: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(40))
    proposed_actions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    confirmed_actions: Mapped[list[int]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
