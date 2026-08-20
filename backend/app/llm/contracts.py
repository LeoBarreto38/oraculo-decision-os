from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class AnalysisEvidence(BaseModel):
    origin: Literal[
        "PERSONAL_DATA",
        "USER_STATEMENT",
        "MARKET_DATA",
        "WEB",
        "EXPERIMENT",
        "OBSERVATION",
        "MODEL_INFERENCE",
    ]
    title: str
    content: str
    url: str | None = None


class DecisionAnalysis(BaseModel):
    recommendation_option_id: int | None = None
    recommendation: str
    why: list[str]
    evidence: list[AnalysisEvidence]
    assumptions: list[str]
    principal_risk: str
    change_conditions: list[str]
    evidence_confidence: float = Field(ge=0, le=1)
    next_action: str
    review_date: date
    missing_data: list[str]
    human_confirmation_required: bool = True


class RedTeamAnalysis(BaseModel):
    fragile_assumptions: list[str]
    hidden_costs: list[str]
    adverse_scenarios: list[str]
    contrary_evidence_needed: list[str]
    original_recommendation_may_be_wrong_because: str
    final_position: Literal["MAINTAIN", "REVISE", "INSUFFICIENT_DATA"]
    revised_recommendation: str | None = None
    synthesis: str
    cheapest_disconfirming_test: str


class ChatAction(BaseModel):
    type: Literal["CREATE_DECISION", "CREATE_TASK", "CREATE_HYPOTHESIS", "CREATE_EVIDENCE"]
    payload: dict[str, object]
    reason: str


class ChatAnswer(BaseModel):
    answer: str
    evidence_basis: list[str]
    proposed_actions: list[ChatAction]
    uncertainty: str | None = None
    confirmation_required: bool = True
