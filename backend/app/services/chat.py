from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.llm.context_builder import build_chat_context
from app.llm.router import AIUnavailable, BudgetAuthorizationRequired, ModelRouter
from app.models.entities import ChatMessage, Decision, DecisionOption, Evidence, Hypothesis, Task
from app.schemas.api import DecisionCreate, EvidenceCreate, HypothesisCreate, TaskCreate
from app.services.dashboard import today_view


def answer_chat(db: Session, message: str, use_ai: bool) -> dict[str, Any]:
    context = build_chat_context(db, message)
    mode = "deterministic_fallback"
    fallback_reason: str | None = None
    if use_ai:
        try:
            answer = ModelRouter().answer_chat(db, context=context, use_web_search=_chat_needs_web(message))
            answer_text = answer.answer
            proposed_actions = [item.model_dump(mode="json") for item in answer.proposed_actions]
            evidence_basis = answer.evidence_basis
            uncertainty = answer.uncertainty
            mode = "ai"
        except BudgetAuthorizationRequired as exc:
            fallback_reason = (
                f"HARD_LIMIT_USD atingido ({exc.spent:.4f}/{exc.hard_limit:.2f} USD); nenhuma chamada foi feita."
            )
            answer_text, proposed_actions, evidence_basis, uncertainty = _fallback(db, message, fallback_reason)
        except AIUnavailable as exc:
            fallback_reason = str(exc)
            answer_text, proposed_actions, evidence_basis, uncertainty = _fallback(db, message, fallback_reason)
    else:
        fallback_reason = "IA desativada explicitamente; nenhuma chamada foi feita."
        answer_text, proposed_actions, evidence_basis, uncertainty = _fallback(db, message, fallback_reason)
    row = ChatMessage(
        user_message=message,
        assistant_answer=answer_text,
        mode=mode,
        proposed_actions=proposed_actions,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "message_id": row.id,
        "mode": mode,
        "fallback_reason": fallback_reason,
        "answer": answer_text,
        "evidence_basis": evidence_basis,
        "uncertainty": uncertainty,
        "proposed_actions": proposed_actions,
        "confirmation_required": bool(proposed_actions),
    }


def confirm_chat_actions(db: Session, message_id: int, action_indexes: list[int]) -> dict[str, Any]:
    message = db.get(ChatMessage, message_id)
    if message is None:
        raise LookupError("Mensagem não encontrada.")
    if message.confirmed_at is not None:
        raise ValueError("As ações desta mensagem já foram confirmadas.")
    unique_indexes = sorted(set(action_indexes))
    if any(index < 0 or index >= len(message.proposed_actions) for index in unique_indexes):
        raise ValueError("Índice de ação inválido.")
    created: list[dict[str, Any]] = []
    try:
        for index in unique_indexes:
            action = message.proposed_actions[index]
            created.append(_execute_action(db, action))
        message.confirmed_actions = unique_indexes
        message.confirmed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message_id": message.id, "executed": created, "confirmed_at": message.confirmed_at}


def _execute_action(db: Session, action: dict[str, Any]) -> dict[str, Any]:
    type_ = action.get("type")
    payload = action.get("payload") or {}
    if type_ == "CREATE_TASK":
        valid = TaskCreate.model_validate(payload)
        item = Task(**valid.model_dump())
        db.add(item)
    elif type_ == "CREATE_HYPOTHESIS":
        valid = HypothesisCreate.model_validate(payload)
        item = Hypothesis(**valid.model_dump())
        db.add(item)
    elif type_ == "CREATE_DECISION":
        valid = DecisionCreate.model_validate(payload)
        data = valid.model_dump(exclude={"options", "evidence", "predictions"})
        item = Decision(**data, status="OPEN")
        db.add(item)
        db.flush()
        for option in valid.options:
            db.add(DecisionOption(decision_id=item.id, **option.model_dump()))
    elif type_ == "CREATE_EVIDENCE":
        decision_id = int(payload.get("decision_id"))
        valid = EvidenceCreate.model_validate({key: value for key, value in payload.items() if key != "decision_id"})
        if db.get(Decision, decision_id) is None:
            raise ValueError("Decisão da evidência não existe.")
        valid_option_ids = set(
            db.scalars(select(DecisionOption.id).where(DecisionOption.decision_id == decision_id))
        )
        for option_id in (valid.supports_option_id, valid.contradicts_option_id):
            if option_id is not None and option_id not in valid_option_ids:
                raise ValueError("A opção referenciada não pertence à decisão da evidência.")
        item = Evidence(decision_id=decision_id, **valid.model_dump())
        db.add(item)
    else:
        raise ValueError(f"Tipo de ação não permitido: {type_}")
    db.flush()
    return {"type": type_, "id": item.id}


def _fallback(
    db: Session, message: str, reason: str
) -> tuple[str, list[dict[str, Any]], list[str], str]:
    lowered = message.casefold()
    today = today_view(db)
    evidence = ["Estado Zero", "registros locais selecionados", "motor determinístico"]
    proposed: list[dict[str, Any]] = []
    if "hoje" in lowered or "agora" in lowered:
        tasks = today["priorities"]
        lines = [f"{index + 1}. {task['title']}" for index, task in enumerate(tasks)]
        answer = "As três prioridades registradas para hoje são:\n" + "\n".join(lines)
    elif "hipótese" in lowered:
        from app.models.entities import Hypothesis

        hypothesis = db.scalar(
            select(Hypothesis)
            .where(Hypothesis.status.in_(("TESTING", "OPEN")))
            .order_by(Hypothesis.test_due_at.asc().nulls_last(), Hypothesis.current_probability)
            .limit(1)
        )
        answer = (
            f"A hipótese que merece teste primeiro é '{hypothesis.title}': {hypothesis.test_definition}"
            if hypothesis
            else "Não há hipótese ativa registrada."
        )
    elif "padrão" in lowered or "repetindo" in lowered:
        alerts = today["alerts"]
        frontier = next((item for item in alerts if item["type"] == "FRONTEIRA_COMERCIAL"), None)
        answer = (
            frontier["message"]
            if frontier
            else "Não há evidência registrada suficiente para afirmar repetição do padrão neste momento."
        )
    elif any(term in lowered for term in ("vale a pena", "gastar", "compare", "comparar")):
        answer = (
            "Isto merece uma decisão auditável. O fallback não inventará opções ou evidências; proponho registrar "
            "a pergunta e você poderá completar opções antes da análise."
        )
        proposed.append(
            {
                "type": "CREATE_DECISION",
                "reason": "Transformar a pergunta em pipeline auditável, após confirmação humana.",
                "payload": {
                    "title": message[:160],
                    "question": message,
                    "context": "Criada a partir do chat; opções e evidências ainda precisam ser registradas.",
                    "importance": "STANDARD",
                    "current_data": "AUTO",
                    "options": [],
                },
            }
        )
    else:
        answer = (
            "O modo determinístico não possui evidência suficiente para responder com segurança. "
            "Abra uma decisão ou registre dados observáveis antes de concluir."
        )
    return answer, proposed, evidence, reason


def _chat_needs_web(message: str) -> bool:
    lowered = message.casefold()
    return any(
        term in lowered
        for term in ("mercado", "concorr", "preço", "regulação", "notícia", "plataforma", "tecnologia atual")
    )
