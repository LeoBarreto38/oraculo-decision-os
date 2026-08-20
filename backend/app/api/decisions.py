from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.llm.router import AIUnavailable, BudgetAuthorizationRequired
from app.models.entities import AnalysisRun, Decision, DecisionOption, Evidence, Prediction, ResearchRecord
from app.schemas.api import (
    DecisionAnalyzeRequest,
    DecisionConfirmRequest,
    DecisionCreate,
    DecisionOptionCreate,
    DecisionOptionOut,
    DecisionOut,
    DecisionOutcomeRequest,
    DecisionUpdate,
    EvidenceCreate,
    EvidenceOut,
    PredictionCreate,
    PredictionOut,
    RedTeamResumeRequest,
)
from app.services.decisions import (
    analyze_decision,
    confirm_decision,
    get_decision,
    record_outcome,
    resume_red_team as resume_red_team_service,
)


router = APIRouter(prefix="/decisions", tags=["decisions"])


def _decision_or_404(db: Session, decision_id: int) -> Decision:
    try:
        return get_decision(db, decision_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=list[DecisionOut])
def list_decisions(db: Session = Depends(get_db)):
    return list(
        db.scalars(
            select(Decision)
            .options(
                selectinload(Decision.options),
                selectinload(Decision.evidence),
                selectinload(Decision.predictions),
            )
            .order_by(Decision.created_at.desc())
        )
    )


@router.post("", response_model=DecisionOut, status_code=status.HTTP_201_CREATED)
def create_decision(payload: DecisionCreate, db: Session = Depends(get_db)):
    decision = Decision(
        **payload.model_dump(exclude={"options", "evidence", "predictions"}),
        status="OPEN",
    )
    db.add(decision)
    try:
        db.flush()
        for option in payload.options:
            db.add(DecisionOption(decision_id=decision.id, **option.model_dump()))
        db.flush()
        for evidence in payload.evidence:
            _validate_option_refs(decision, evidence, db)
            db.add(Evidence(decision_id=decision.id, **evidence.model_dump()))
        for prediction in payload.predictions:
            db.add(Prediction(decision_id=decision.id, **prediction.model_dump()))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Código de decisão já existe ou referência inválida.") from exc
    return _decision_or_404(db, decision.id)


@router.get("/{decision_id}", response_model=DecisionOut)
def read_decision(decision_id: int, db: Session = Depends(get_db)):
    return _decision_or_404(db, decision_id)


@router.patch("/{decision_id}", response_model=DecisionOut)
def update_decision(decision_id: int, payload: DecisionUpdate, db: Session = Depends(get_db)):
    decision = _decision_or_404(db, decision_id)
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("status") in ("DECIDED", "CLOSED"):
        raise HTTPException(
            status_code=422,
            detail="Use os endpoints de confirmação humana e resultado para estes estados.",
        )
    for key, value in updates.items():
        setattr(decision, key, value)
    db.commit()
    return _decision_or_404(db, decision_id)


@router.delete("/{decision_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_decision(decision_id: int, db: Session = Depends(get_db)):
    db.delete(_decision_or_404(db, decision_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{decision_id}/options", response_model=DecisionOptionOut, status_code=status.HTTP_201_CREATED)
def add_option(decision_id: int, payload: DecisionOptionCreate, db: Session = Depends(get_db)):
    decision = _decision_or_404(db, decision_id)
    if decision.status in ("DECIDED", "CLOSED"):
        raise HTTPException(status_code=409, detail="Reabra formalmente a decisão antes de alterar opções.")
    option = DecisionOption(decision_id=decision.id, **payload.model_dump())
    db.add(option)
    db.commit()
    db.refresh(option)
    return option


@router.post("/{decision_id}/evidence", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
def add_evidence(decision_id: int, payload: EvidenceCreate, db: Session = Depends(get_db)):
    decision = _decision_or_404(db, decision_id)
    _validate_option_refs(decision, payload, db)
    evidence = Evidence(decision_id=decision.id, **payload.model_dump())
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


@router.post("/{decision_id}/predictions", response_model=PredictionOut, status_code=status.HTTP_201_CREATED)
def add_prediction(decision_id: int, payload: PredictionCreate, db: Session = Depends(get_db)):
    decision = _decision_or_404(db, decision_id)
    prediction = Prediction(decision_id=decision.id, **payload.model_dump())
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


@router.post("/{decision_id}/analyze")
def analyze(decision_id: int, payload: DecisionAnalyzeRequest, db: Session = Depends(get_db)):
    try:
        return analyze_decision(
            db,
            decision_id,
            use_ai=payload.use_ai,
            current_data=payload.current_data,
            explicitly_authorized_over_budget=payload.explicitly_authorized_over_budget,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{decision_id}/confirm", response_model=DecisionOut)
def confirm(decision_id: int, payload: DecisionConfirmRequest, db: Session = Depends(get_db)):
    try:
        confirm_decision(db, decision_id, payload.selected_option_id, payload.rationale, payload.review_at)
        return _decision_or_404(db, decision_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{decision_id}/red-team")
def resume_red_team(decision_id: int, payload: RedTeamResumeRequest, db: Session = Depends(get_db)):
    try:
        return resume_red_team_service(
            db,
            decision_id,
            payload.analysis_run_id,
            payload.explicitly_authorized_over_budget,
        )
    except BudgetAuthorizationRequired as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "RED_TEAM_BUDGET_AUTHORIZATION_REQUIRED",
                "message": str(exc),
                "spent_usd": exc.spent,
                "hard_limit_usd": exc.hard_limit,
                "primary_analysis_will_not_be_repeated": True,
            },
        ) from exc
    except AIUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{decision_id}/outcome", response_model=DecisionOut)
def outcome(decision_id: int, payload: DecisionOutcomeRequest, db: Session = Depends(get_db)):
    try:
        record_outcome(
            db,
            decision_id,
            payload.actual_outcome,
            [(item.prediction_id, item.outcome) for item in payload.prediction_outcomes],
        )
        return _decision_or_404(db, decision_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{decision_id}/analyses")
def list_analyses(decision_id: int, db: Session = Depends(get_db)):
    decision = _decision_or_404(db, decision_id)
    rows = list(
        db.scalars(
            select(AnalysisRun).where(AnalysisRun.decision_id == decision_id).order_by(AnalysisRun.created_at.desc())
        )
    )
    research_rows = list(
        db.scalars(
            select(ResearchRecord)
            .where(ResearchRecord.decision_id == decision_id)
            .order_by(ResearchRecord.searched_at.desc())
        )
    )
    output = []
    for row in rows:
        analysis = row.analysis or {}
        red_team_warning = next(
            (
                str(item)
                for item in analysis.get("missing_data", [])
                if str(item).startswith("A análise principal foi concluída, mas o red team")
            ),
            None,
        )
        if row.mode == "ai" and decision.importance == "CRITICAL" and row.red_team is None:
            blocked = bool(analysis.get("budget_authorization_required"))
            stage = (
                "PRIMARY_COMPLETE_RED_TEAM_BUDGET_AUTHORIZATION_REQUIRED"
                if blocked
                else "PRIMARY_COMPLETE_RED_TEAM_PENDING"
            )
            budget_blocked_stage = "RED_TEAM" if blocked else None
            resume_red_team = {
                "method": "POST",
                "path": f"/api/decisions/{decision.id}/red-team",
                "payload": {"analysis_run_id": row.id, "explicitly_authorized_over_budget": blocked},
            }
        elif row.mode == "ai":
            stage = "ANALYSIS_COMPLETE_AWAITING_HUMAN_CONFIRMATION"
            budget_blocked_stage = None
            resume_red_team = None
        elif analysis.get("budget_authorization_required"):
            stage = "PRIMARY_BUDGET_AUTHORIZATION_REQUIRED"
            budget_blocked_stage = "PRIMARY"
            resume_red_team = None
        else:
            stage = "DETERMINISTIC_FALLBACK_AWAITING_HUMAN_CONFIRMATION"
            budget_blocked_stage = None
            resume_red_team = None
        related_research = next(
            (
                research
                for research in research_rows
                if _aware_datetime(research.searched_at) <= _aware_datetime(row.created_at)
            ),
            None,
        )
        output.append({
            "id": row.id,
            "analysis_run_id": row.id,
            "mode": row.mode,
            "stage": stage,
            "budget_blocked_stage": budget_blocked_stage,
            "model": row.model,
            "scorecards": row.scorecards,
            "analysis": analysis,
            "red_team": row.red_team,
            "red_team_warning": red_team_warning,
            "resume_red_team": resume_red_team,
            "research": (
                {
                    "id": related_research.id,
                    "query": related_research.query,
                    "searched_at": related_research.searched_at,
                    "sources": related_research.sources,
                }
                if related_research
                else None
            ),
            "fallback_reason": row.fallback_reason,
            "created_at": row.created_at,
        })
    return output


def _aware_datetime(value):
    from datetime import timezone

    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _validate_option_refs(decision: Decision, payload: EvidenceCreate, db: Session) -> None:
    valid_ids = {option.id for option in decision.options}
    for option_id in (payload.supports_option_id, payload.contradicts_option_id):
        if option_id is not None and option_id not in valid_ids:
            raise HTTPException(status_code=422, detail="A opção referenciada não pertence à decisão.")
