from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Alert, Decision, Hypothesis, Project, ProjectActivity, Task


def _fingerprint(rule: str, entity: str, period: str = "") -> str:
    return hashlib.sha256(f"{rule}:{entity}:{period}".encode()).hexdigest()[:48]


def _ensure_alert(
    db: Session,
    *,
    type_: str,
    severity: str,
    message: str,
    fingerprint: str,
    due_at: datetime | None = None,
    metadata: dict[str, object] | None = None,
) -> bool:
    if db.scalar(select(Alert).where(Alert.fingerprint == fingerprint)):
        return False
    db.add(
        Alert(
            type=type_,
            severity=severity,
            message=message,
            fingerprint=fingerprint,
            due_at=due_at,
            metadata_json=metadata,
        )
    )
    return True


def run_alert_rules(db: Session, now: datetime | None = None) -> dict[str, int]:
    now = now or datetime.now(timezone.utc)
    settings = get_settings()
    created = {name: 0 for name in (
        "FRONTEIRA_COMERCIAL", "NOVO_PROJETO", "CAIXA", "HIPOTESE_VENCIDA", "DECISAO_SEM_REVISAO"
    )}

    inactivity_cutoff = now - timedelta(days=settings.external_inactivity_days)
    validating = list(db.scalars(select(Project).where(Project.status == "VALIDATING")))
    for project in validating:
        last_external = db.scalar(
            select(func.max(ProjectActivity.occurred_at)).where(
                ProjectActivity.project_id == project.id, ProjectActivity.is_external.is_(True)
            )
        )
        technical_count = db.scalar(
            select(func.count(ProjectActivity.id)).where(
                ProjectActivity.project_id == project.id, ProjectActivity.type == "TECHNICAL"
            )
        ) or 0
        completed_technical = db.scalar(
            select(func.count(Task.id)).where(
                Task.project_id == project.id,
                Task.status.in_(("DONE", "COMPLETED")),
                Task.is_external_interaction.is_(False),
            )
        ) or 0
        no_recent_external = last_external is None or _as_aware(last_external) < inactivity_cutoff
        if no_recent_external and technical_count + completed_technical >= 3:
            if _ensure_alert(
                db,
                type_="FRONTEIRA_COMERCIAL",
                severity="HIGH",
                message=(
                    f"Possível perfeccionismo defensivo em {project.name}: desenvolvimento avança sem validação externa. "
                    "Trate isto como hipótese comportamental e faça uma interação comercial observável."
                ),
                fingerprint=_fingerprint("frontier", str(project.id), now.strftime("%Y-%m")),
                metadata={"project_id": project.id},
            ):
                created["FRONTEIRA_COMERCIAL"] += 1

    for project in db.scalars(select(Project).where(Project.created_at >= now - timedelta(days=1))):
        older_validating = [item for item in validating if item.id != project.id and item.created_at < project.created_at]
        if not older_validating:
            continue
        formal_decision = db.scalar(
            select(Decision).where(
                Decision.created_at >= project.created_at - timedelta(days=1),
                Decision.title.ilike("%projeto%"),
                Decision.status.in_(("DECIDED", "CLOSED")),
            )
        )
        if formal_decision is None and _ensure_alert(
            db,
            type_="NOVO_PROJETO",
            severity="HIGH",
            message=(
                f"Novo projeto {project.name} criado enquanto {older_validating[0].name} permanece em validação, "
                "sem decisão formal registrada."
            ),
            fingerprint=_fingerprint("new-project", str(project.id)),
            metadata={"project_id": project.id, "validating_project_id": older_validating[0].id},
        ):
            created["NOVO_PROJETO"] += 1

    for task in db.scalars(
        select(Task).where(
            Task.status.not_in(("DONE", "COMPLETED", "CANCELLED", "ARCHIVED")),
            Task.estimated_minutes >= 240,
            Task.strategic_category.not_in(("CASH", "ASSET")),
        )
    ):
        if _ensure_alert(
            db,
            type_="CAIXA",
            severity="MEDIUM",
            message=(
                f"A tarefa '{task.title}' consome tempo relevante sem contribuição declarada para CASH ou ASSET validado."
            ),
            fingerprint=_fingerprint("cash", str(task.id)),
            due_at=task.due_at,
            metadata={"task_id": task.id},
        ):
            created["CAIXA"] += 1

    for hypothesis in db.scalars(
        select(Hypothesis).where(
            Hypothesis.status.in_(("TESTING", "OPEN")),
            Hypothesis.test_due_at.is_not(None),
            Hypothesis.test_due_at <= now,
        )
    ):
        due = _as_aware(hypothesis.test_due_at)
        if _ensure_alert(
            db,
            type_="HIPOTESE_VENCIDA",
            severity="HIGH",
            message=f"A hipótese '{hypothesis.title}' passou da data de teste sem resultado.",
            fingerprint=_fingerprint("hypothesis", str(hypothesis.id), due.date().isoformat()),
            due_at=hypothesis.test_due_at,
            metadata={"hypothesis_id": hypothesis.id},
        ):
            created["HIPOTESE_VENCIDA"] += 1

    for decision in db.scalars(
        select(Decision).where(
            Decision.status.not_in(("CLOSED", "ARCHIVED")),
            Decision.review_at.is_not(None),
            Decision.review_at <= now,
        )
    ):
        due = _as_aware(decision.review_at)
        decision.status = "REVIEW_DUE"
        if _ensure_alert(
            db,
            type_="DECISAO_SEM_REVISAO",
            severity="HIGH" if decision.importance in ("HIGH", "CRITICAL") else "MEDIUM",
            message=f"A decisão '{decision.title}' chegou à data de revisão.",
            fingerprint=_fingerprint("decision-review", str(decision.id), due.date().isoformat()),
            due_at=decision.review_at,
            metadata={"decision_id": decision.id},
        ):
            created["DECISAO_SEM_REVISAO"] += 1

    db.commit()
    return created


def create_internal_event(db: Session, event_type: str, message: str, severity: str = "INFO") -> bool:
    now = datetime.now(timezone.utc)
    created = _ensure_alert(
        db,
        type_=event_type,
        severity=severity,
        message=message,
        fingerprint=_fingerprint(event_type, now.date().isoformat()),
        due_at=now,
    )
    db.commit()
    return created


def _as_aware(value: datetime | None) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
