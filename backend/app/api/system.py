from __future__ import annotations

import json
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.analytics.calibration import calibration_report
from app.core.config import ENV_FILE, get_settings
from app.core.database import get_db
from app.decision_engine.scoring import load_weights, save_weights
from app.llm.router import usage_summary
from app.models.entities import (
    Alert,
    DailyCheckin,
    Decision,
    EntityEdge,
    EntityNode,
    FinancialSnapshot,
    Goal,
    JournalEntry,
    Project,
    ScoreWeightChange,
    SystemSetting,
)
from app.scheduler.alerts import run_alert_rules
from app.scheduler.jobs import scheduler_status
from app.schemas.api import (
    DailyCheckinCreate,
    DailyCheckinOut,
    FinancialSnapshotCreate,
    JournalCreate,
    JournalOut,
    JournalUpdate,
    ScoreWeightsUpdate,
)
from app.services.backup import create_backup
from app.services.dashboard import dashboard_view, today_view


router = APIRouter(tags=["system"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "service": "oraculo-backend", "version": "0.1.0"}


@router.get("/today")
def today(db: Session = Depends(get_db)):
    return today_view(db)


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return dashboard_view(db)


@router.get("/state-zero")
def state_zero(db: Session = Depends(get_db)):
    settings = list(db.scalars(select(SystemSetting).order_by(SystemSetting.key)))
    goals = list(db.scalars(select(Goal).order_by(Goal.priority.desc())))
    projects = list(db.scalars(select(Project).order_by(Project.strategic_value.desc())))
    return {
        "settings": {item.key: item.value for item in settings},
        "goals": [
            {
                "id": item.id,
                "title": item.title,
                "target_value": item.target_value,
                "current_value": item.current_value,
                "unit": item.unit,
                "status": item.status,
            }
            for item in goals
        ],
        "projects": [
            {
                "id": item.id,
                "name": item.name,
                "type": item.type,
                "status": item.status,
                "description": item.description,
                "next_action": item.next_action,
            }
            for item in projects
        ],
    }


@router.get("/ai-usage")
def ai_usage(db: Session = Depends(get_db)):
    return usage_summary(db)


@router.get("/analytics/calibration")
def analytics_calibration(db: Session = Depends(get_db)):
    return calibration_report(db)


@router.get("/alerts")
def list_alerts(include_acknowledged: bool = False, db: Session = Depends(get_db)):
    query = select(Alert)
    if not include_acknowledged:
        query = query.where(Alert.acknowledged_at.is_(None))
    rows = list(db.scalars(query.order_by(Alert.created_at.desc())))
    return [
        {
            "id": item.id,
            "type": item.type,
            "severity": item.severity,
            "message": item.message,
            "metadata": item.metadata_json,
            "created_at": item.created_at,
            "due_at": item.due_at,
            "acknowledged_at": item.acknowledged_at,
        }
        for item in rows
    ]


@router.post("/alerts/run")
def run_alerts(db: Session = Depends(get_db)):
    return {"created": run_alert_rules(db)}


@router.post("/alerts/{alert_id}/ack")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    item = db.get(Alert, alert_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Alerta não encontrado.")
    item.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": item.id, "acknowledged_at": item.acknowledged_at}


@router.get("/map")
def knowledge_map(db: Session = Depends(get_db)):
    nodes = list(db.scalars(select(EntityNode).order_by(EntityNode.id)))
    edges = list(db.scalars(select(EntityEdge).order_by(EntityEdge.id)))
    return {
        "nodes": [
            {
                "id": str(item.id),
                "type": item.type,
                "position": {"x": ((item.id - 1) % 3) * 280, "y": ((item.id - 1) // 3) * 160},
                "data": {
                    "label": item.label,
                    "entity_type": item.type,
                    "reference_type": item.reference_type,
                    "reference_id": item.reference_id,
                    "metadata": item.metadata_json,
                },
            }
            for item in nodes
        ],
        "edges": [
            {
                "id": str(item.id),
                "source": str(item.source_node_id),
                "target": str(item.target_node_id),
                "label": item.relation,
                "data": {"weight": item.weight},
            }
            for item in edges
        ],
    }


@router.get("/checkins", response_model=list[DailyCheckinOut])
def list_checkins(limit: int = 30, db: Session = Depends(get_db)):
    return list(db.scalars(select(DailyCheckin).order_by(DailyCheckin.date.desc()).limit(min(limit, 365))))


@router.post("/checkins", response_model=DailyCheckinOut)
def save_checkin(payload: DailyCheckinCreate, response: Response, db: Session = Depends(get_db)):
    item = db.scalar(select(DailyCheckin).where(DailyCheckin.date == payload.date))
    if item is None:
        item = DailyCheckin(**payload.model_dump())
        db.add(item)
        response.status_code = status.HTTP_201_CREATED
    else:
        for key, value in payload.model_dump(exclude={"date"}).items():
            setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.get("/journal", response_model=list[JournalOut])
def list_journal(limit: int = 100, db: Session = Depends(get_db)):
    return list(db.scalars(select(JournalEntry).order_by(JournalEntry.date.desc(), JournalEntry.id.desc()).limit(limit)))


@router.post("/journal", response_model=JournalOut, status_code=status.HTTP_201_CREATED)
def create_journal(payload: JournalCreate, db: Session = Depends(get_db)):
    item = JournalEntry(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/journal/{entry_id}", response_model=JournalOut)
def update_journal(entry_id: int, payload: JournalUpdate, db: Session = Depends(get_db)):
    item = db.get(JournalEntry, entry_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Entrada não encontrada.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    return item


@router.delete("/journal/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_journal(entry_id: int, db: Session = Depends(get_db)):
    item = db.get(JournalEntry, entry_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Entrada não encontrada.")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/settings")
def public_settings():
    settings = get_settings()
    return {
        "models": {
            "critical": settings.model_critical,
            "standard": settings.model_standard,
            "light": settings.model_light,
        },
        "budgets": {
            "monthly": settings.monthly_ai_budget_usd,
            "soft_warning": settings.soft_warning_usd,
            "hard_limit": settings.hard_limit_usd,
        },
        "openai_configured": bool(settings.openai_api_key),
        "web_search_enabled": settings.web_search_enabled,
        "timezone": settings.timezone,
        "morning_briefing_time": settings.morning_briefing_time,
        "evening_checkin_time": settings.evening_checkin_time,
        "backup_retention": settings.backup_retention,
        "scheduler": scheduler_status(),
        "env_file": str(ENV_FILE),
        "secret_values_exposed": False,
    }


@router.get("/settings/score-weights")
def get_score_weights():
    return load_weights()


@router.patch("/settings/score-weights")
def update_score_weights(payload: ScoreWeightsUpdate, db: Session = Depends(get_db)):
    previous = load_weights()
    now = datetime.now(timezone.utc)
    audit_decision = Decision(
        code=f"WEIGHTS-{now.strftime('%Y%m%d-%H%M%S-%f')}",
        title="Alteração explícita dos pesos do score",
        question="Devemos aplicar a nova configuração de pesos fornecida pelo usuário?",
        context=json.dumps({"previous": previous, "requested": payload.model_dump()}, ensure_ascii=False),
        status="DECIDED",
        importance="HIGH",
        current_data="NAO",
        selected_option="Aplicar os pesos confirmados pelo usuário",
        human_rationale=payload.reason,
        decided_at=now,
    )
    db.add(audit_decision)
    db.flush()
    try:
        updated = save_weights(payload.benefits, payload.penalties)
        db.add(
            ScoreWeightChange(
                decision_id=audit_decision.id,
                previous_weights=previous,
                new_weights=updated,
                reason=payload.reason,
            )
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"weights": updated, "audit_decision_id": audit_decision.id}


@router.post("/financial-snapshots", status_code=status.HTTP_201_CREATED)
def create_financial_snapshot(payload: FinancialSnapshotCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(FinancialSnapshot).where(FinancialSnapshot.date == payload.date))
    if existing:
        for key, value in payload.model_dump(exclude={"date"}).items():
            setattr(existing, key, value)
        item = existing
    else:
        item = FinancialSnapshot(**payload.model_dump())
        db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "date": item.date,
        "cash_available": item.cash_available,
        "monthly_income": item.monthly_income,
        "target_income": item.target_income,
        "experimental_spent": item.experimental_spent,
        "pipeline_potential": item.pipeline_potential,
    }


@router.post("/backup/export")
def export_backup():
    try:
        archive = create_backup()
    except (RuntimeError, FileNotFoundError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return FileResponse(
        path=archive,
        media_type="application/zip",
        filename=archive.name,
        headers={"X-Oraculo-Secret-Content": "none"},
    )
