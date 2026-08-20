from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import Decision, Goal, Project, SystemSetting


@dataclass(frozen=True)
class BuiltContext:
    text: str
    record_refs: list[dict[str, Any]]
    sha256: str


def build_chat_context(db: Session, message: str) -> BuiltContext:
    """Select a small operational slice for chat; journals and the full DB are deliberately excluded."""
    from app.services.dashboard import today_view

    refs: list[dict[str, Any]] = []
    core: dict[str, Any] = {}
    for key in ("financial_state", "execution_profile", "constitutional_rule"):
        setting = db.scalar(select(SystemSetting).where(SystemSetting.key == key))
        if setting:
            core[key] = setting.value
            refs.append({"type": "SystemSetting", "id": setting.id, "key": key})
    lowered = message.casefold()
    projects = list(db.scalars(select(Project).where(Project.status.in_(("ACTIVE", "VALIDATING")))))
    named = [project for project in projects if project.name.casefold() in lowered]
    if not named:
        named = sorted(projects, key=lambda item: (-item.strategic_value, item.id))[:3]
    project_context = [
        {
            "id": project.id,
            "name": project.name,
            "status": project.status,
            "type": project.type,
            "revenue_potential": project.revenue_potential,
            "time_to_value": project.time_to_value,
            "validation_level": project.validation_level,
            "next_action": project.next_action,
        }
        for project in named[:3]
    ]
    refs.extend({"type": "Project", "id": item.id} for item in named[:3])
    today = today_view(db)
    for task in today["priorities"]:
        refs.append({"type": "Task", "id": task["id"], "role": "today_priority"})
    payload = {
        "USER_MESSAGE": message,
        "CORE_CONTEXT": core,
        "PROJECT_CONTEXT": project_context,
        "TODAY_CONTEXT": {
            "main_goal": today["main_goal"],
            "financial": today["financial"],
            "priorities": today["priorities"],
            "pending_decisions": today["pending_decisions"][:5],
            "alerts": today["alerts"][:5],
        },
        "MUTATION_RULE": "Proponha ações estruturadas, mas não afirme que foram executadas. Toda mutação exige confirmação humana.",
    }
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return BuiltContext(text=text, record_refs=refs, sha256=hashlib.sha256(text.encode("utf-8")).hexdigest())


def build_decision_context(db: Session, decision_id: int) -> BuiltContext:
    decision = db.scalar(
        select(Decision)
        .where(Decision.id == decision_id)
        .options(
            selectinload(Decision.options),
            selectinload(Decision.evidence),
            selectinload(Decision.predictions),
        )
    )
    if decision is None:
        raise LookupError("Decisão não encontrada.")
    refs: list[dict[str, Any]] = []
    core: dict[str, Any] = {}
    for key in ("financial_state", "resources", "execution_profile", "constitutional_rule"):
        setting = db.scalar(select(SystemSetting).where(SystemSetting.key == key))
        if setting:
            core[key] = setting.value
            refs.append({"type": "SystemSetting", "id": setting.id, "key": key})

    goals = list(
        db.scalars(select(Goal).where(Goal.status == "ACTIVE").order_by(Goal.priority.desc()).limit(3))
    )
    goal_context = [
        {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "target_value": item.target_value,
            "current_value": item.current_value,
            "unit": item.unit,
            "deadline": item.deadline,
        }
        for item in goals
    ]
    refs.extend({"type": "Goal", "id": item.id} for item in goals)

    searchable = f"{decision.title} {decision.question} {decision.context or ''}".casefold()
    projects = list(db.scalars(select(Project).where(Project.status.in_(("ACTIVE", "VALIDATING")))))
    relevant_projects = [item for item in projects if item.name.casefold() in searchable]
    if not relevant_projects:
        relevant_projects = projects[:5]
    project_context = [
        {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "type": item.type,
            "status": item.status,
            "strategic_value": item.strategic_value,
            "revenue_potential": item.revenue_potential,
            "time_to_value": item.time_to_value,
            "cash_requirement": item.cash_requirement,
            "risk_level": item.risk_level,
            "validation_level": item.validation_level,
            "next_action": item.next_action,
        }
        for item in relevant_projects[:5]
    ]
    refs.extend({"type": "Project", "id": item.id} for item in relevant_projects[:5])

    decision_context = {
        "id": decision.id,
        "code": decision.code,
        "title": decision.title,
        "question": decision.question,
        "context": decision.context,
        "importance": decision.importance,
        "current_data": decision.current_data,
        "review_at": decision.review_at,
        "options": [
            {
                key: getattr(option, key)
                for key in (
                    "id",
                    "title",
                    "description",
                    "expected_upside",
                    "expected_downside",
                    "estimated_probability",
                    "impact_financial",
                    "speed_to_result",
                    "strategic_alignment",
                    "asset_value",
                    "useful_learning",
                    "reversibility",
                    "evidence_strength",
                    "cash_cost",
                    "time_cost",
                    "execution_risk",
                    "opportunity_cost",
                    "personal_pattern_risk",
                    "uncertainty",
                    "score",
                )
            }
            for option in decision.options
        ],
        "evidence": [
            {
                "id": item.id,
                "type": item.type,
                "title": item.title,
                "content": item.content,
                "source_url": item.source_url,
                "source_date": item.source_date,
                "reliability": item.reliability,
                "freshness": item.freshness,
                "supports_option_id": item.supports_option_id,
                "contradicts_option_id": item.contradicts_option_id,
            }
            for item in decision.evidence
        ],
    }
    refs.append({"type": "Decision", "id": decision.id})
    refs.extend({"type": "DecisionOption", "id": item.id} for item in decision.options)
    refs.extend({"type": "Evidence", "id": item.id} for item in decision.evidence)

    history_words = {word for word in re.findall(r"[\wÀ-ÿ]{5,}", searchable) if len(word) >= 5}
    history_candidates = list(
        db.scalars(
            select(Decision)
            .where(Decision.id != decision.id, Decision.actual_outcome.is_not(None))
            .order_by(Decision.decided_at.desc())
            .limit(20)
        )
    )
    relevant_history = []
    for item in history_candidates:
        words = set(re.findall(r"[\wÀ-ÿ]{5,}", f"{item.title} {item.question}".casefold()))
        if history_words & words:
            relevant_history.append(
                {
                    "id": item.id,
                    "title": item.title,
                    "selected_option": item.selected_option,
                    "actual_outcome": item.actual_outcome,
                }
            )
            refs.append({"type": "Decision", "id": item.id, "role": "relevant_history"})
        if len(relevant_history) == 3:
            break

    payload = {
        "CORE_CONTEXT": core,
        "GOAL_CONTEXT": goal_context,
        "PROJECT_CONTEXT": project_context,
        "DECISION_CONTEXT": decision_context,
        "RELEVANT_HISTORY": relevant_history,
        "DATA_BOUNDARY": (
            "Somente os registros listados acima foram selecionados. Ausência de dado não é evidência negativa. "
            "Não invente registros ou observações."
        ),
    }
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return BuiltContext(text=text, record_refs=refs, sha256=digest)
