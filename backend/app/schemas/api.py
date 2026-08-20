from __future__ import annotations

from datetime import date as Date
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = None
    target_value: float | None = None
    current_value: float | None = None
    unit: str | None = None
    deadline: Date | None = None
    priority: int = 0
    status: str = "ACTIVE"


class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    target_value: float | None = None
    current_value: float | None = None
    unit: str | None = None
    deadline: Date | None = None
    priority: int | None = None
    status: str | None = None


class GoalOut(ORMModel):
    id: int
    title: str
    description: str | None
    target_value: float | None
    current_value: float | None
    unit: str | None
    deadline: Date | None
    priority: int
    status: str
    created_at: datetime
    updated_at: datetime


PROJECT_STATES = Literal["ACTIVE", "VALIDATING", "PAUSED", "INVALIDATED", "COMPLETED", "ARCHIVED"]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    type: str | None = None
    status: PROJECT_STATES = "ACTIVE"
    strategic_value: float = Field(0, ge=0, le=10)
    revenue_potential: float = Field(0, ge=0)
    time_to_value: float = Field(0, ge=0)
    cash_requirement: float = Field(0, ge=0)
    risk_level: float = Field(0, ge=0, le=10)
    validation_level: float = Field(0, ge=0, le=10)
    next_action: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    type: str | None = None
    status: PROJECT_STATES | None = None
    strategic_value: float | None = Field(None, ge=0, le=10)
    revenue_potential: float | None = Field(None, ge=0)
    time_to_value: float | None = Field(None, ge=0)
    cash_requirement: float | None = Field(None, ge=0)
    risk_level: float | None = Field(None, ge=0, le=10)
    validation_level: float | None = Field(None, ge=0, le=10)
    next_action: str | None = None
    last_progress_at: datetime | None = None


class ProjectOut(ORMModel):
    id: int
    name: str
    description: str | None
    type: str | None
    status: str
    strategic_value: float
    revenue_potential: float
    time_to_value: float
    cash_requirement: float
    risk_level: float
    validation_level: float
    next_action: str | None
    last_progress_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    project_id: int | None = None
    goal_id: int | None = None
    title: str = Field(min_length=1, max_length=240)
    description: str | None = None
    priority: int = 0
    due_at: datetime | None = None
    status: str = "TODO"
    estimated_minutes: int | None = Field(None, ge=0)
    actual_minutes: int | None = Field(None, ge=0)
    strategic_category: Literal["CASH", "ASSET", "LEARNING", "MAINTENANCE", "DISTRACTION"] = "MAINTENANCE"
    is_external_interaction: bool = False


class TaskUpdate(BaseModel):
    project_id: int | None = None
    goal_id: int | None = None
    title: str | None = None
    description: str | None = None
    priority: int | None = None
    due_at: datetime | None = None
    status: str | None = None
    estimated_minutes: int | None = Field(None, ge=0)
    actual_minutes: int | None = Field(None, ge=0)
    strategic_category: Literal["CASH", "ASSET", "LEARNING", "MAINTENANCE", "DISTRACTION"] | None = None
    is_external_interaction: bool | None = None


class TaskOut(ORMModel):
    id: int
    project_id: int | None
    goal_id: int | None
    title: str
    description: str | None
    priority: int
    due_at: datetime | None
    status: str
    estimated_minutes: int | None
    actual_minutes: int | None
    strategic_category: str
    completed_at: datetime | None
    is_external_interaction: bool
    created_at: datetime
    updated_at: datetime


class DailyCheckinCreate(BaseModel):
    date: Date = Field(default_factory=Date.today)
    energy: int | None = Field(None, ge=0, le=10)
    focus: int | None = Field(None, ge=0, le=10)
    main_result: str | None = None
    what_worked: str | None = None
    what_failed: str | None = None
    blockers: str | None = None
    learning: str | None = None
    strategy_change: str | None = None
    feedback: str | None = None
    free_text: str | None = None


class DailyCheckinOut(ORMModel):
    id: int
    date: Date
    energy: int | None
    focus: int | None
    main_result: str | None
    what_worked: str | None
    what_failed: str | None
    blockers: str | None
    learning: str | None
    strategy_change: str | None
    feedback: str | None
    free_text: str | None
    created_at: datetime


class DecisionOptionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = None
    expected_upside: float | None = None
    expected_downside: float | None = None
    cash_cost: float = Field(0, ge=0, le=10)
    time_cost: float = Field(0, ge=0, le=10)
    reversibility: float = Field(5, ge=0, le=10)
    strategic_alignment: float = Field(5, ge=0, le=10)
    evidence_strength: float = Field(5, ge=0, le=10)
    execution_risk: float = Field(5, ge=0, le=10)
    personal_pattern_risk: float = Field(5, ge=0, le=10)
    estimated_probability: float | None = Field(None, ge=0, le=1)
    impact_financial: float = Field(5, ge=0, le=10)
    speed_to_result: float = Field(5, ge=0, le=10)
    asset_value: float = Field(5, ge=0, le=10)
    useful_learning: float = Field(5, ge=0, le=10)
    opportunity_cost: float = Field(5, ge=0, le=10)
    uncertainty: float = Field(5, ge=0, le=10)


class DecisionOptionOut(ORMModel):
    id: int
    decision_id: int
    title: str
    description: str | None
    expected_upside: float | None
    expected_downside: float | None
    cash_cost: float
    time_cost: float
    reversibility: float
    strategic_alignment: float
    evidence_strength: float
    execution_risk: float
    personal_pattern_risk: float
    estimated_probability: float | None
    impact_financial: float
    speed_to_result: float
    asset_value: float
    useful_learning: float
    opportunity_cost: float
    uncertainty: float
    score: float | None
    score_breakdown: dict[str, Any] | None


class EvidenceCreate(BaseModel):
    type: Literal[
        "PERSONAL_DATA", "MARKET_DATA", "EXPERIMENT", "OBSERVATION", "MODEL_INFERENCE", "USER_STATEMENT"
    ]
    title: str
    content: str
    source_url: str | None = None
    source_date: Date | None = None
    reliability: float = Field(0.5, ge=0, le=1)
    freshness: float = Field(0.5, ge=0, le=1)
    supports_option_id: int | None = None
    contradicts_option_id: int | None = None


class EvidenceOut(ORMModel):
    id: int
    decision_id: int
    type: str
    title: str
    content: str
    source_url: str | None
    source_date: Date | None
    captured_at: datetime
    reliability: float
    freshness: float
    supports_option_id: int | None
    contradicts_option_id: int | None


class PredictionCreate(BaseModel):
    description: str
    probability: float = Field(ge=0, le=1)
    target_date: Date
    category: str | None = None


class PredictionOut(ORMModel):
    id: int
    decision_id: int | None
    description: str
    probability: float
    target_date: Date
    category: str | None
    outcome: float | None
    resolved_at: datetime | None
    brier_score: float | None


class DecisionCreate(BaseModel):
    code: str | None = None
    title: str = Field(min_length=1, max_length=240)
    question: str = Field(min_length=1)
    context: str | None = None
    importance: Literal["LIGHT", "STANDARD", "HIGH", "CRITICAL"] = "STANDARD"
    current_data: Literal["AUTO", "SIM", "NAO"] = "AUTO"
    review_at: datetime | None = None
    options: list[DecisionOptionCreate] = Field(default_factory=list)
    evidence: list[EvidenceCreate] = Field(default_factory=list)
    predictions: list[PredictionCreate] = Field(default_factory=list)


class DecisionUpdate(BaseModel):
    title: str | None = None
    question: str | None = None
    context: str | None = None
    status: str | None = None
    importance: Literal["LIGHT", "STANDARD", "HIGH", "CRITICAL"] | None = None
    current_data: Literal["AUTO", "SIM", "NAO"] | None = None
    review_at: datetime | None = None


class DecisionOut(ORMModel):
    id: int
    code: str | None
    title: str
    question: str
    context: str | None
    status: str
    importance: str
    current_data: str
    selected_option: str | None
    selected_option_id: int | None
    human_rationale: str | None
    decided_at: datetime | None
    review_at: datetime | None
    actual_outcome: str | None
    recommendation: dict[str, Any] | None
    analysis_mode: str | None
    created_at: datetime
    updated_at: datetime
    options: list[DecisionOptionOut] = Field(default_factory=list)
    evidence: list[EvidenceOut] = Field(default_factory=list)
    predictions: list[PredictionOut] = Field(default_factory=list)


class DecisionAnalyzeRequest(BaseModel):
    use_ai: bool = True
    current_data: Literal["AUTO", "SIM", "NAO"] | None = None
    explicitly_authorized_over_budget: bool = False


class RedTeamResumeRequest(BaseModel):
    analysis_run_id: int
    explicitly_authorized_over_budget: bool = False


class DecisionConfirmRequest(BaseModel):
    selected_option_id: int
    rationale: str = Field(min_length=1)
    review_at: datetime | None = None


class PredictionOutcome(BaseModel):
    prediction_id: int
    outcome: float = Field(ge=0, le=1)


class DecisionOutcomeRequest(BaseModel):
    actual_outcome: str = Field(min_length=1)
    prediction_outcomes: list[PredictionOutcome] = Field(default_factory=list)


class HypothesisCreate(BaseModel):
    project_id: int | None = None
    title: str
    description: str | None = None
    prior_probability: float = Field(0.5, ge=0, le=1)
    current_probability: float | None = Field(None, ge=0, le=1)
    status: str = "TESTING"
    category: str | None = None
    test_definition: str | None = None
    success_condition: str | None = None
    failure_condition: str | None = None
    test_due_at: datetime | None = None

    @model_validator(mode="after")
    def default_current(self) -> "HypothesisCreate":
        if self.current_probability is None:
            self.current_probability = self.prior_probability
        return self


class HypothesisUpdate(BaseModel):
    project_id: int | None = None
    title: str | None = None
    description: str | None = None
    current_probability: float | None = Field(None, ge=0, le=1)
    status: str | None = None
    category: str | None = None
    test_definition: str | None = None
    success_condition: str | None = None
    failure_condition: str | None = None
    test_due_at: datetime | None = None
    resolved_at: datetime | None = None


class HypothesisOut(ORMModel):
    id: int
    project_id: int | None
    title: str
    description: str | None
    prior_probability: float
    current_probability: float
    status: str
    category: str | None
    test_definition: str | None
    success_condition: str | None
    failure_condition: str | None
    test_due_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class JournalCreate(BaseModel):
    date: Date = Field(default_factory=Date.today)
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)


class JournalUpdate(BaseModel):
    date: Date | None = None
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None


class JournalOut(ORMModel):
    id: int
    date: Date
    title: str
    content: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime


class ActivityCreate(BaseModel):
    type: str
    description: str
    occurred_at: datetime | None = None
    is_external: bool = False


class ScoreWeightsUpdate(BaseModel):
    benefits: dict[str, float]
    penalties: dict[str, float]
    reason: str = Field(min_length=3)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    use_ai: bool = True


class ChatConfirmRequest(BaseModel):
    action_indexes: list[int]


class FinancialSnapshotCreate(BaseModel):
    date: Date = Field(default_factory=Date.today)
    cash_available: float
    monthly_income: float
    target_income: float
    experimental_spent: float = 0
    pipeline_potential: float = 0
