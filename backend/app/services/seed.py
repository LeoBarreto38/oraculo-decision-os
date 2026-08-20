from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import (
    Decision, DecisionOption, EntityEdge, EntityNode, FinancialSnapshot,
    Goal, Hypothesis, Project, SystemSetting, Task,
)


def _database_has_user_state(db: Session) -> bool:
    """Never add public demo records to an existing installation."""
    state_models = (SystemSetting, Goal, Project, Decision, Task, Hypothesis, EntityNode)
    return any(db.scalar(select(model.id).limit(1)) is not None for model in state_models)


def seed_estado_zero(db: Session) -> bool:
    """Create a small, clearly labelled DEMO dataset only in an empty database."""
    if _database_has_user_state(db):
        return False

    now = datetime.now(timezone.utc)
    goal = Goal(
        title="DEMO: Reach first measurable objective",
        description="Example goal for exploring the application. Replace or remove it.",
        target_value=10, current_value=0, unit="milestones", priority=10, status="ACTIVE",
    )
    project = Project(
        name="DEMO: Example Project",
        description="Neutral sample project for evaluating the Oráculo workflow.",
        type="DEMO", status="ACTIVE", strategic_value=5, revenue_potential=0,
        time_to_value=5, cash_requirement=0, risk_level=2, validation_level=1,
        next_action="Replace this demo with a real project.", last_progress_at=now,
    )
    db.add_all([goal, project])
    db.flush()

    task = Task(
        project_id=project.id, goal_id=goal.id,
        title="DEMO: Define one measurable milestone",
        description="Choose a small result that can be verified objectively.",
        priority=10, due_at=now + timedelta(days=1), status="TODO",
        estimated_minutes=30, strategic_category="LEARNING",
    )
    hypothesis = Hypothesis(
        project_id=project.id,
        title="DEMO: A focused strategy will produce a measurable result",
        description="Example hypothesis. Replace it with an assumption you can test.",
        prior_probability=0.5, current_probability=0.5, status="TESTING", category="DEMO",
        test_definition="Run one small test and record the result.",
        success_condition="The selected milestone is reached.",
        failure_condition="The milestone is not reached within the test period.",
        test_due_at=now + timedelta(days=7),
    )
    decision = Decision(
        code="DEMO-DECISION-001",
        title="DEMO: Allocate time between two example strategies",
        question="Which example strategy should receive the next focused work session?",
        context="Neutral demonstration data. No personal or financial information is included.",
        status="OPEN", importance="STANDARD", current_data="NAO",
        review_at=now + timedelta(days=7),
    )
    db.add_all([task, hypothesis, decision])
    db.flush()
    db.add_all([
        DecisionOption(
            decision_id=decision.id, title="DEMO: Strategy A",
            description="Use the session to validate the most uncertain assumption.",
            expected_upside=10, expected_downside=0, cash_cost=0, time_cost=5,
            reversibility=9, strategic_alignment=7, evidence_strength=4,
            execution_risk=3, personal_pattern_risk=2, estimated_probability=0.6,
            impact_financial=0, speed_to_result=7, asset_value=5, useful_learning=9,
            opportunity_cost=4, uncertainty=6,
        ),
        DecisionOption(
            decision_id=decision.id, title="DEMO: Strategy B",
            description="Use the session to improve the existing example workflow.",
            expected_upside=8, expected_downside=0, cash_cost=0, time_cost=5,
            reversibility=9, strategic_alignment=6, evidence_strength=5,
            execution_risk=2, personal_pattern_risk=2, estimated_probability=0.7,
            impact_financial=0, speed_to_result=6, asset_value=7, useful_learning=6,
            opportunity_cost=5, uncertainty=4,
        ),
    ])
    db.add_all([
        SystemSetting(
            key="financial_state",
            value={"cash_available": 0, "minimum_monthly_cost": 0, "monthly_income": 0,
                   "target_monthly_income": 0, "income_gap": 0, "protected_capital": 0,
                   "max_experimental_capital": 0,
                   "strategic_priority": "DEMO: Replace with your priority"},
            description="Neutral demonstration values; replace with your own data.",
        ),
        SystemSetting(
            key="resources",
            value={"availability": "not configured", "infrastructure": "not configured", "tools": []},
            description="Neutral demonstration values; replace with your own data.",
        ),
        SystemSetting(
            key="execution_profile",
            value={"strengths": [], "known_risk_pattern": [], "interpretation": "Not configured."},
            description="Neutral demonstration values; replace with your own data.",
        ),
        SystemSetting(
            key="constitutional_rule",
            value={"rule": "Important external actions require explicit human confirmation.",
                   "project_states": ["ACTIVE", "VALIDATING", "PAUSED", "INVALIDATED", "COMPLETED", "ARCHIVED"]},
            description="Generic safety rule included with the public demo.",
        ),
        FinancialSnapshot(date=date.today(), cash_available=0, monthly_income=0,
                          target_income=0, experimental_spent=0, pipeline_potential=0),
    ])

    person_node = EntityNode(type="Person", label="DEMO: Demo User", reference_type="PERSON", reference_id=1)
    goal_node = EntityNode(type="Goal", label=goal.title, reference_type="Goal", reference_id=goal.id)
    project_node = EntityNode(type="Project", label=project.name, reference_type="Project", reference_id=project.id)
    decision_node = EntityNode(type="Decision", label=decision.code,
                               reference_type="Decision", reference_id=decision.id)
    db.add_all([person_node, goal_node, project_node, decision_node])
    db.flush()
    db.add_all([
        EntityEdge(source_node_id=person_node.id, target_node_id=project_node.id, relation="owns"),
        EntityEdge(source_node_id=project_node.id, target_node_id=goal_node.id, relation="contributes_to"),
        EntityEdge(source_node_id=decision_node.id, target_node_id=project_node.id, relation="affects"),
    ])
    db.commit()
    return True
