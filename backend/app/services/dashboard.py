from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Alert, Decision, FinancialSnapshot, Goal, Hypothesis, Project, Task


DONE_STATES = ("DONE", "COMPLETED", "CANCELLED", "ARCHIVED")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _task_dict(task: Task) -> dict[str, Any]:
    return {
        "id": task.id,
        "project_id": task.project_id,
        "goal_id": task.goal_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "due_at": task.due_at,
        "status": task.status,
        "estimated_minutes": task.estimated_minutes,
        "strategic_category": task.strategic_category,
    }


def today_view(db: Session) -> dict[str, Any]:
    now = _now()
    settings = get_settings()
    main_goal = db.scalar(
        select(Goal).where(Goal.status == "ACTIVE").order_by(Goal.priority.desc(), Goal.id).limit(1)
    )
    financial = db.scalar(select(FinancialSnapshot).order_by(FinancialSnapshot.date.desc()).limit(1))
    priorities = list(
        db.scalars(
            select(Task)
            .where(Task.status.not_in(DONE_STATES))
            .order_by(Task.priority.desc(), Task.due_at.asc().nulls_last(), Task.id)
            .limit(3)
        )
    )
    overdue = list(
        db.scalars(
            select(Task)
            .where(Task.status.not_in(DONE_STATES), Task.due_at.is_not(None), Task.due_at < now)
            .order_by(Task.due_at, Task.priority.desc())
        )
    )
    decisions = list(
        db.scalars(
            select(Decision)
            .where(Decision.status.in_(("OPEN", "ANALYZED", "REVIEW_DUE")))
            .order_by(Decision.importance.desc(), Decision.created_at)
        )
    )
    alerts = list(
        db.scalars(
            select(Alert).where(Alert.acknowledged_at.is_(None)).order_by(Alert.created_at.desc()).limit(20)
        )
    )
    stalled_cutoff = now - timedelta(days=settings.stalled_project_days)
    stalled = list(
        db.scalars(
            select(Project)
            .where(
                Project.status.in_(("ACTIVE", "VALIDATING")),
                or_(Project.last_progress_at.is_(None), Project.last_progress_at < stalled_cutoff),
            )
            .order_by(Project.strategic_value.desc())
        )
    )
    next_task = db.scalar(
        select(Task)
        .where(Task.status.not_in(DONE_STATES), Task.due_at.is_not(None))
        .order_by(Task.due_at, Task.priority.desc())
        .limit(1)
    )
    return {
        "date": date.today(),
        "main_goal": {
            "id": main_goal.id,
            "title": main_goal.title,
            "current_value": main_goal.current_value,
            "target_value": main_goal.target_value,
            "unit": main_goal.unit,
            "progress_percent": round(100 * (main_goal.current_value or 0) / (main_goal.target_value or 1), 2),
        }
        if main_goal
        else None,
        "financial": {
            "monthly_income": financial.monthly_income,
            "target_income": financial.target_income,
            "gap": max(0, financial.target_income - financial.monthly_income),
            "cash_available": financial.cash_available,
        }
        if financial
        else None,
        "priorities": [_task_dict(task) for task in priorities],
        "priority_rule": "Exatamente três principais; demais tarefas permanecem fora deste bloco.",
        "overdue_tasks": [_task_dict(task) for task in overdue],
        "pending_decisions": [
            {
                "id": item.id,
                "code": item.code,
                "title": item.title,
                "importance": item.importance,
                "status": item.status,
                "review_at": item.review_at,
            }
            for item in decisions
        ],
        "alerts": [
            {
                "id": item.id,
                "type": item.type,
                "severity": item.severity,
                "message": item.message,
                "due_at": item.due_at,
                "created_at": item.created_at,
            }
            for item in alerts
        ],
        "stalled_projects": [
            {
                "id": item.id,
                "name": item.name,
                "status": item.status,
                "next_action": item.next_action,
                "last_progress_at": item.last_progress_at,
            }
            for item in stalled
        ],
        "next_milestone": _task_dict(next_task) if next_task else None,
        "checkin_prompts": [
            "O que você fez?",
            "O que não fez?",
            "O que impediu?",
            "O que aprendeu?",
            "Há alguma informação que muda nossa estratégia?",
        ],
    }


def dashboard_view(db: Session) -> dict[str, Any]:
    snapshot = db.scalar(select(FinancialSnapshot).order_by(FinancialSnapshot.date.desc()).limit(1))
    project_count = db.scalar(
        select(func.count(Project.id)).where(Project.status.in_(("ACTIVE", "VALIDATING")))
    ) or 0
    decision_count = db.scalar(
        select(func.count(Decision.id)).where(Decision.status.in_(("OPEN", "ANALYZED", "REVIEW_DUE")))
    ) or 0
    hypothesis_count = db.scalar(
        select(func.count(Hypothesis.id)).where(Hypothesis.status.in_(("TESTING", "OPEN")))
    ) or 0
    critical_alerts = db.scalar(
        select(func.count(Alert.id)).where(Alert.acknowledged_at.is_(None), Alert.severity == "CRITICAL")
    ) or 0
    snapshots = list(db.scalars(select(FinancialSnapshot).order_by(FinancialSnapshot.date)))
    minutes = dict(
        db.execute(
            select(Task.strategic_category, func.coalesce(func.sum(func.coalesce(Task.actual_minutes, Task.estimated_minutes)), 0))
            .group_by(Task.strategic_category)
        ).all()
    )
    all_categories = ("CASH", "ASSET", "LEARNING", "MAINTENANCE", "DISTRACTION")
    return {
        "cards": {
            "cash_available": snapshot.cash_available if snapshot else 0,
            "monthly_income": snapshot.monthly_income if snapshot else 0,
            "target_income": snapshot.target_income if snapshot else 0,
            "income_gap": max(0, snapshot.target_income - snapshot.monthly_income) if snapshot else 0,
            "experimental_spent": snapshot.experimental_spent if snapshot else 0,
            "pipeline_potential": snapshot.pipeline_potential if snapshot else 0,
            "active_projects": project_count,
            "open_decisions": decision_count,
            "testing_hypotheses": hypothesis_count,
            "critical_alerts": critical_alerts,
        },
        "financial_progress": [
            {
                "date": item.date,
                "monthly_income": item.monthly_income,
                "target_income": item.target_income,
                "cash_available": item.cash_available,
                "pipeline_potential": item.pipeline_potential,
            }
            for item in snapshots
        ],
        "time_distribution": [
            {"category": category, "minutes": int(minutes.get(category, 0) or 0)} for category in all_categories
        ],
        "time_distribution_basis": "actual_minutes quando disponível; caso contrário estimated_minutes.",
    }
