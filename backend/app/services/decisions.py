from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.analytics.calibration import resolve_prediction
from app.decision_engine.scoring import score_decision_options
from app.llm.context_builder import build_decision_context
from app.llm.router import AIUnavailable, BudgetAuthorizationRequired, ModelRouter
from app.models.entities import AnalysisRun, Decision, DecisionOption, Prediction


WEB_KEYWORDS = {
    "mercado",
    "concorrência",
    "concorrente",
    "preço",
    "precificação",
    "regulação",
    "tecnologia",
    "oportunidade",
    "notícia",
    "contratação",
    "plataforma",
}


def get_decision(db: Session, decision_id: int) -> Decision:
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
    return decision


def analyze_decision(
    db: Session,
    decision_id: int,
    *,
    use_ai: bool,
    current_data: str | None,
    explicitly_authorized_over_budget: bool,
) -> dict[str, Any]:
    decision = get_decision(db, decision_id)
    if len(decision.options) < 2:
        raise ValueError("Adicione ao menos duas opções reais antes de analisar.")
    scorecards = score_decision_options(decision.options)
    db.flush()
    research_mode = current_data or decision.current_data
    web_mode = _web_mode(decision, research_mode)
    use_web = web_mode != "OFF"
    mode = "deterministic_fallback"
    fallback_reason: str | None = None
    research = None
    research_warning = None
    red_team = None
    red_team_warning = None

    if use_ai:
        try:
            built_context = build_decision_context(db, decision.id)
            result = ModelRouter().analyze_decision(
                db,
                decision_id=decision.id,
                importance=decision.importance,
                context=built_context,
                web_mode=web_mode,
                research_query=decision.question,
                explicitly_authorized_over_budget=explicitly_authorized_over_budget,
            )
            analysis = result["analysis"]
            red_team = result["red_team"]
            red_team_warning = result.get("red_team_warning")
            research = result["research"]
            research_warning = result.get("research_warning")
            mode = "ai"
        except BudgetAuthorizationRequired as exc:
            fallback_reason = (
                f"HARD_LIMIT_USD atingido ({exc.spent:.4f}/{exc.hard_limit:.2f} USD). "
                "Nenhuma chamada foi feita. Reenvie com autorização explícita se desejar exceder o limite."
            )
            analysis = deterministic_analysis(decision, scorecards, fallback_reason, use_web)
            analysis["budget_authorization_required"] = True
        except AIUnavailable as exc:
            fallback_reason = str(exc)
            analysis = deterministic_analysis(decision, scorecards, fallback_reason, use_web)
    else:
        fallback_reason = "IA desativada explicitamente nesta análise; nenhuma chamada foi feita."
        analysis = deterministic_analysis(decision, scorecards, fallback_reason, use_web)

    if red_team:
        analysis["red_team_synthesis"] = red_team.get("synthesis")
        analysis["red_team_final_position"] = red_team.get("final_position")
    if mode == "ai" and research_warning:
        analysis.setdefault("missing_data", []).append(research_warning)
    if mode == "ai" and red_team_warning:
        analysis.setdefault("missing_data", []).append(red_team_warning)
        analysis["budget_authorization_required"] = True
    decision.recommendation = analysis
    decision.analysis_mode = mode
    decision.status = "ANALYZED"
    run = AnalysisRun(
        decision_id=decision.id,
        mode=mode,
        model=ModelRouter().model_for(decision.importance) if mode == "ai" else None,
        scorecards=scorecards,
        analysis=analysis,
        red_team=red_team,
        fallback_reason=fallback_reason,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    if mode == "ai" and red_team_warning:
        stage = "PRIMARY_COMPLETE_RED_TEAM_BUDGET_AUTHORIZATION_REQUIRED"
        budget_blocked_stage = "RED_TEAM"
    elif mode == "ai":
        stage = "ANALYSIS_COMPLETE_AWAITING_HUMAN_CONFIRMATION"
        budget_blocked_stage = None
    elif analysis.get("budget_authorization_required"):
        stage = "PRIMARY_BUDGET_AUTHORIZATION_REQUIRED"
        budget_blocked_stage = "PRIMARY"
    else:
        stage = "DETERMINISTIC_FALLBACK_AWAITING_HUMAN_CONFIRMATION"
        budget_blocked_stage = None
    return {
        "analysis_run_id": run.id,
        "decision_id": decision.id,
        "mode": mode,
        "stage": stage,
        "budget_blocked_stage": budget_blocked_stage,
        "fallback_reason": fallback_reason,
        "analysis": analysis,
        "red_team": red_team,
        "red_team_warning": red_team_warning,
        "scorecards": scorecards,
        "requires_human_confirmation": True,
        "research_requested": use_web,
        "research_mode": web_mode,
        "research": research,
        "resume_red_team": (
            {
                "method": "POST",
                "path": f"/api/decisions/{decision.id}/red-team",
                "payload": {"analysis_run_id": run.id, "explicitly_authorized_over_budget": True},
            }
            if budget_blocked_stage == "RED_TEAM"
            else None
        ),
    }


def resume_red_team(
    db: Session,
    decision_id: int,
    analysis_run_id: int,
    explicitly_authorized_over_budget: bool,
) -> dict[str, Any]:
    decision = get_decision(db, decision_id)
    if decision.importance != "CRITICAL":
        raise ValueError("Somente decisões CRITICAL possuem etapa obrigatória de red team.")
    run = db.get(AnalysisRun, analysis_run_id)
    if run is None or run.decision_id != decision.id:
        raise LookupError("Execução de análise não encontrada para esta decisão.")
    if run.mode != "ai":
        raise ValueError("O red team só pode retomar uma análise primária produzida pela IA.")
    if run.red_team is not None:
        return {
            "analysis_run_id": run.id,
            "decision_id": decision.id,
            "stage": "ANALYSIS_COMPLETE_AWAITING_HUMAN_CONFIRMATION",
            "budget_blocked_stage": None,
            "analysis": run.analysis,
            "red_team": run.red_team,
            "requires_human_confirmation": True,
            "already_completed": True,
        }
    built_context = build_decision_context(db, decision.id)
    red_team = ModelRouter().resume_red_team(
        db,
        decision_id=decision.id,
        context=built_context,
        primary_analysis=run.analysis,
        explicitly_authorized_over_budget=explicitly_authorized_over_budget,
    )
    updated_analysis = dict(run.analysis)
    updated_analysis["red_team_synthesis"] = red_team.get("synthesis")
    updated_analysis["red_team_final_position"] = red_team.get("final_position")
    updated_analysis.pop("budget_authorization_required", None)
    updated_analysis["missing_data"] = [
        item
        for item in updated_analysis.get("missing_data", [])
        if not str(item).startswith("A análise principal foi concluída, mas o red team")
    ]
    run.red_team = red_team
    run.analysis = updated_analysis
    decision.recommendation = updated_analysis
    db.commit()
    return {
        "analysis_run_id": run.id,
        "decision_id": decision.id,
        "stage": "ANALYSIS_COMPLETE_AWAITING_HUMAN_CONFIRMATION",
        "budget_blocked_stage": None,
        "analysis": updated_analysis,
        "red_team": red_team,
        "requires_human_confirmation": True,
        "already_completed": False,
    }


def deterministic_analysis(
    decision: Decision, scorecards: list[dict[str, Any]], reason: str, research_was_relevant: bool
) -> dict[str, Any]:
    top = scorecards[0]
    selected = next(option for option in decision.options if option.id == top["option_id"])
    evidence = [
        {
            "origin": item.type,
            "title": item.title,
            "content": item.content,
            "url": item.source_url,
            "reliability": item.reliability,
        }
        for item in decision.evidence
    ]
    largest_penalty = max(
        top["penalty_contributions"].items(), key=lambda item: item[1], default=("uncertainty", 0)
    )[0]
    change_conditions = [
        "Nova evidência observada alterar materialmente força da evidência, custo ou velocidade.",
        "O experimento mais barato falsificar a hipótese central da opção recomendada.",
        "O risco de ruína ou o uso do capital protegido aumentar.",
    ]
    missing = []
    if not evidence:
        missing.append("Não há evidências registradas para a decisão.")
    if research_was_relevant:
        missing.append("Dados atuais foram considerados relevantes, mas não foram pesquisados no fallback determinístico.")
    return {
        "source": "DETERMINISTIC_ENGINE",
        "ai_generated": False,
        "fallback_reason": reason,
        "recommendation_option_id": selected.id,
        "recommendation": (
            f"A opção '{selected.title}' lidera pelo score comparativo ({top['score']:.2f}/100). "
            "Isto não substitui julgamento humano nem representa probabilidade objetiva."
        ),
        "why": [
            f"Índice de benefícios: {top['benefit_index']:.2f}/100.",
            f"Índice de penalidades: {top['penalty_index']:.2f}/100.",
            "A ordenação usa pesos editáveis e versionados, sem intervenção silenciosa da IA.",
        ],
        "evidence": evidence,
        "assumptions": [
            "As notas 0–10 fornecidas nas opções refletem o julgamento humano atual.",
            "Os pesos da configuração vigente são adequados apenas para comparação inicial.",
            "Dados ausentes não foram inferidos.",
        ],
        "principal_risk": f"Maior penalidade ponderada atual: {largest_penalty}.",
        "change_conditions": change_conditions,
        "evidence_confidence": _evidence_confidence(decision),
        "next_action": _next_action(selected, largest_penalty),
        "review_date": (date.today() + timedelta(days=7)).isoformat(),
        "missing_data": missing,
        "human_confirmation_required": True,
    }


def confirm_decision(
    db: Session, decision_id: int, selected_option_id: int, rationale: str, review_at: datetime | None
) -> Decision:
    decision = get_decision(db, decision_id)
    option = next((item for item in decision.options if item.id == selected_option_id), None)
    if option is None:
        raise ValueError("A opção selecionada não pertence a esta decisão.")
    decision.selected_option_id = option.id
    decision.selected_option = option.title
    decision.human_rationale = rationale
    decision.decided_at = datetime.now(timezone.utc)
    decision.review_at = review_at or decision.review_at
    decision.status = "DECIDED"
    db.commit()
    return decision


def record_outcome(
    db: Session, decision_id: int, actual_outcome: str, prediction_outcomes: list[tuple[int, float]]
) -> Decision:
    decision = get_decision(db, decision_id)
    if decision.status not in ("DECIDED", "REVIEW_DUE", "CLOSED"):
        raise ValueError("Registre primeiro a decisão humana.")
    predictions_by_id = {item.id: item for item in decision.predictions}
    for prediction_id, outcome in prediction_outcomes:
        prediction = predictions_by_id.get(prediction_id)
        if prediction is None:
            raise ValueError(f"Previsão {prediction_id} não pertence a esta decisão.")
        resolve_prediction(prediction, outcome)
    decision.actual_outcome = actual_outcome
    decision.status = "CLOSED"
    db.commit()
    return decision


def _web_mode(decision: Decision, mode: str) -> str:
    if mode == "SIM":
        return "REQUIRED"
    if mode == "NAO":
        return "OFF"
    text = f"{decision.title} {decision.question} {decision.context or ''}".casefold()
    return "AUTO" if any(keyword in text for keyword in WEB_KEYWORDS) else "OFF"


def _evidence_confidence(decision: Decision) -> float:
    if not decision.evidence:
        return 0.1
    values = [item.reliability * item.freshness for item in decision.evidence]
    coverage = min(1, len(values) / max(2, len(decision.options)))
    return round(min(0.95, (sum(values) / len(values)) * coverage), 3)


def _next_action(option: DecisionOption, largest_penalty: str) -> str:
    return (
        f"Antes de comprometer recursos, execute em até 48 horas um teste observável da opção '{option.title}' "
        f"que reduza a incerteza sobre {largest_penalty}."
    )
