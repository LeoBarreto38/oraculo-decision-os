from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import DATA_DIR, Settings, get_settings
from app.llm.context_builder import BuiltContext
from app.llm.contracts import ChatAnswer, DecisionAnalysis, RedTeamAnalysis
from app.llm.prompts import MASTER_PROMPT, RED_TEAM_PROMPT
from app.models.entities import AIUsage, Evidence, LLMContextAudit, ResearchRecord


T = TypeVar("T", bound=BaseModel)


class AIUnavailable(RuntimeError):
    pass


class BudgetAuthorizationRequired(RuntimeError):
    def __init__(self, spent: float, hard_limit: float) -> None:
        self.spent = spent
        self.hard_limit = hard_limit
        super().__init__("O limite rígido mensal de IA foi atingido; autorização explícita é necessária.")


def _month_start(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def usage_summary(db: Session, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = _month_start(now)

    def total(since: datetime) -> float:
        return float(
            db.scalar(
                select(func.coalesce(func.sum(AIUsage.estimated_cost_usd), 0)).where(AIUsage.created_at >= since)
            )
            or 0
        )

    month = total(month_start)
    recent = list(db.scalars(select(AIUsage).order_by(AIUsage.created_at.desc()).limit(50)))
    return {
        "today": round(total(today_start), 6),
        "week": round(total(week_start), 6),
        "month": round(month, 6),
        "budget": settings.monthly_ai_budget_usd,
        "soft_warning": settings.soft_warning_usd,
        "hard_limit": settings.hard_limit_usd,
        "warning_active": month >= settings.soft_warning_usd,
        "hard_limit_reached": month >= settings.hard_limit_usd,
        "remaining_before_hard_limit": round(max(0, settings.hard_limit_usd - month), 6),
        "pricing_note": "Estimativa configurável em data/model_pricing.json; não é fatura da OpenAI.",
        "recent": [
            {
                "id": item.id,
                "model": item.model,
                "input_tokens": item.input_tokens,
                "cached_tokens": item.cached_tokens,
                "output_tokens": item.output_tokens,
                "web_search_calls": item.web_search_calls,
                "estimated_cost_usd": item.estimated_cost_usd,
                "request_type": item.request_type,
                "decision_id": item.decision_id,
                "created_at": item.created_at,
            }
            for item in recent
        ],
    }


class ModelRouter:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def model_for(self, importance: str) -> str:
        if importance == "CRITICAL":
            return self.settings.model_critical
        if importance == "LIGHT":
            return self.settings.model_light
        return self.settings.model_standard

    def ensure_budget(self, db: Session, explicitly_authorized: bool = False) -> dict[str, Any]:
        summary = usage_summary(db, self.settings)
        if summary["hard_limit_reached"] and not explicitly_authorized:
            raise BudgetAuthorizationRequired(summary["month"], summary["hard_limit"])
        return summary

    def analyze_decision(
        self,
        db: Session,
        *,
        decision_id: int,
        importance: str,
        context: BuiltContext,
        web_mode: str,
        research_query: str | None = None,
        explicitly_authorized_over_budget: bool = False,
    ) -> dict[str, Any]:
        self.ensure_budget(db, explicitly_authorized_over_budget)
        use_web_search = web_mode != "OFF"
        if use_web_search and not self.settings.web_search_enabled:
            raise AIUnavailable(
                "A decisão exige dados atuais, mas ORACULO_WEB_SEARCH_ENABLED está desativado. "
                "Nenhuma pesquisa foi executada."
            )
        if not self.settings.openai_api_key:
            raise AIUnavailable("OPENAI_API_KEY não está disponível no backend.")
        model = self.model_for(importance)
        prompt = (
            "Analise a decisão usando somente o contexto auditado abaixo. O score quantitativo é comparativo, "
            "não probabilidade científica. Se usar a web, rotule cada evidência WEB e preserve URLs. "
            + ("A pesquisa web é obrigatória nesta análise. " if web_mode == "REQUIRED" else "")
            + "\n\n"
            f"CONTEXTO AUDITADO (sha256={context.sha256}):\n{context.text}"
        )
        analysis, raw_response = self._structured_response(
            db,
            model=model,
            request_type="decision_analysis",
            decision_id=decision_id,
            context=context,
            system_prompt=MASTER_PROMPT,
            user_prompt=prompt,
            response_format=DecisionAnalysis,
            web_mode=web_mode,
        )
        sources = _extract_sources(raw_response)
        web_search_calls = _count_web_search_calls(raw_response)
        research = None
        research_warning = None
        if use_web_search and web_search_calls and sources:
            captured_at = datetime.now(timezone.utc)
            sources = [
                {**source, "captured_at": captured_at.isoformat(), "source_date": None}
                for source in sources
            ]
            research = ResearchRecord(
                decision_id=decision_id,
                query=research_query or prompt[:500],
                searched_at=captured_at,
                sources=sources,
                relevant_excerpts=[item.get("excerpt", "") for item in sources if item.get("excerpt")],
                response_id=getattr(raw_response, "id", None),
            )
            db.add(research)
            for source in sources:
                url = source.get("url")
                if not url:
                    continue
                existing = db.scalar(
                    select(Evidence).where(Evidence.decision_id == decision_id, Evidence.source_url == url)
                )
                if existing is None:
                    db.add(
                        Evidence(
                            decision_id=decision_id,
                            type="MARKET_DATA",
                            title=source.get("title") or "Fonte web consultada",
                            content=source.get("excerpt") or "Fonte consultada pela ferramenta web_search.",
                            source_url=url,
                            # Publication date is unknown unless the source itself
                            # provides one. captured_at already records retrieval.
                            source_date=None,
                            reliability=0.6,
                            freshness=1.0,
                        )
                    )
        elif use_web_search:
            research_warning = (
                "A pesquisa web era relevante, mas a resposta não trouxe uma chamada com fontes auditáveis; "
                "nenhuma pesquisa foi registrada ou fingida."
            )

        red_team: RedTeamAnalysis | None = None
        red_team_warning = None
        if importance == "CRITICAL":
            try:
                self.ensure_budget(db, explicitly_authorized_over_budget)
            except BudgetAuthorizationRequired as exc:
                red_team_warning = (
                    f"A análise principal foi concluída, mas o red team não foi chamado porque o limite rígido "
                    f"foi atingido ({exc.spent:.4f}/{exc.hard_limit:.2f} USD). Autorize explicitamente para continuar."
                )
            else:
                red_prompt = (
                    f"{RED_TEAM_PROMPT}\n\nANÁLISE PRINCIPAL:\n{analysis.model_dump_json()}\n\n"
                    f"CONTEXTO ORIGINAL (sha256={context.sha256}):\n{context.text}"
                )
                red_team, _ = self._structured_response(
                    db,
                    model=self.settings.model_critical,
                    request_type="red_team",
                    decision_id=decision_id,
                    context=context,
                    system_prompt=MASTER_PROMPT,
                    user_prompt=red_prompt,
                    response_format=RedTeamAnalysis,
                    web_mode="OFF",
                )
        db.commit()
        return {
            "model": model,
            "analysis": analysis.model_dump(mode="json"),
            "red_team": red_team.model_dump(mode="json") if red_team else None,
            "research": {
                "id": research.id,
                "sources": sources,
                "searched_at": research.searched_at,
            }
            if research
            else None,
            "research_warning": research_warning,
            "red_team_warning": red_team_warning,
        }

    def resume_red_team(
        self,
        db: Session,
        *,
        decision_id: int,
        context: BuiltContext,
        primary_analysis: dict[str, Any],
        explicitly_authorized_over_budget: bool = False,
    ) -> dict[str, Any]:
        """Run only the pending CRITICAL red-team stage; never repeat the primary call."""
        self.ensure_budget(db, explicitly_authorized_over_budget)
        if not self.settings.openai_api_key:
            raise AIUnavailable("OPENAI_API_KEY não está disponível no backend.")
        red_prompt = (
            f"{RED_TEAM_PROMPT}\n\nANÁLISE PRINCIPAL JÁ CONCLUÍDA (não repita):\n"
            f"{json.dumps(primary_analysis, ensure_ascii=False)}\n\n"
            f"CONTEXTO ATUAL AUDITADO (sha256={context.sha256}):\n{context.text}"
        )
        red_team, _ = self._structured_response(
            db,
            model=self.settings.model_critical,
            request_type="red_team_resume",
            decision_id=decision_id,
            context=context,
            system_prompt=MASTER_PROMPT,
            user_prompt=red_prompt,
            response_format=RedTeamAnalysis,
            web_mode="OFF",
        )
        db.commit()
        return red_team.model_dump(mode="json")

    def answer_chat(
        self,
        db: Session,
        *,
        context: BuiltContext,
        use_web_search: bool = False,
        explicitly_authorized_over_budget: bool = False,
    ) -> ChatAnswer:
        self.ensure_budget(db, explicitly_authorized_over_budget)
        if use_web_search and not self.settings.web_search_enabled:
            raise AIUnavailable("Pesquisa web solicitada no chat, mas está desativada; nenhuma pesquisa foi executada.")
        if not self.settings.openai_api_key:
            raise AIUnavailable("OPENAI_API_KEY não está disponível no backend.")
        prompt = (
            "Responda à mensagem com base somente no contexto operacional auditado. Seja direto. "
            "Se uma mudança de dados ajudar, apenas proponha uma ação estruturada; ela dependerá de confirmação. "
            f"\n\nCONTEXTO AUDITADO (sha256={context.sha256}):\n{context.text}"
        )
        answer, _ = self._structured_response(
            db,
            model=self.settings.model_standard,
            request_type="chat",
            decision_id=None,
            context=context,
            system_prompt=MASTER_PROMPT,
            user_prompt=prompt,
            response_format=ChatAnswer,
            web_mode="AUTO" if use_web_search else "OFF",
        )
        db.commit()
        return answer

    def _structured_response(
        self,
        db: Session,
        *,
        model: str,
        request_type: str,
        decision_id: int | None,
        context: BuiltContext,
        system_prompt: str,
        user_prompt: str,
        response_format: type[T],
        web_mode: str,
    ) -> tuple[T, Any]:
        self._audit_context(db, decision_id, request_type, model, context)
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.settings.openai_api_key)
            kwargs: dict[str, Any] = {
                "model": model,
                "input": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "text_format": response_format,
                "store": False,
            }
            if web_mode != "OFF":
                kwargs["tools"] = [{"type": "web_search"}]
                kwargs["tool_choice"] = "required" if web_mode == "REQUIRED" else "auto"
                kwargs["include"] = ["web_search_call.action.sources"]
            response = client.responses.parse(**kwargs)
            parsed = response.output_parsed
            if parsed is None:
                raise AIUnavailable("A API não devolveu a análise estruturada esperada.")
            self._record_usage(db, response, model, request_type, decision_id)
            db.flush()
            return parsed, response
        except (AIUnavailable, BudgetAuthorizationRequired):
            raise
        except Exception as exc:
            # No response text or secret is included in this application-level error.
            raise AIUnavailable(f"A chamada OpenAI falhou ({type(exc).__name__}).") from exc

    def _audit_context(
        self,
        db: Session,
        decision_id: int | None,
        request_type: str,
        model: str,
        context: BuiltContext,
    ) -> None:
        db.add(
            LLMContextAudit(
                decision_id=decision_id,
                request_type=request_type,
                model=model,
                record_refs=context.record_refs,
                context_sha256=context.sha256,
                estimated_chars=len(context.text),
            )
        )
        db.flush()

    def _record_usage(
        self, db: Session, response: Any, model: str, request_type: str, decision_id: int | None
    ) -> None:
        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        details = getattr(usage, "input_tokens_details", None)
        cached_tokens = int(getattr(details, "cached_tokens", 0) or 0)
        web_search_calls = _count_web_search_calls(response)
        estimated = estimate_cost_usd(model, input_tokens, cached_tokens, output_tokens, web_search_calls)
        db.add(
            AIUsage(
                model=model,
                input_tokens=input_tokens,
                cached_tokens=cached_tokens,
                output_tokens=output_tokens,
                web_search_calls=web_search_calls,
                estimated_cost_usd=estimated,
                request_type=request_type,
                decision_id=decision_id,
                response_id=getattr(response, "id", None),
            )
        )


def estimate_cost_usd(
    model: str, input_tokens: int, cached_tokens: int, output_tokens: int, web_search_calls: int = 0
) -> float:
    path = DATA_DIR / "model_pricing.json"
    try:
        with path.open("r", encoding="utf-8") as handle:
            pricing = json.load(handle)
            models = pricing["models"]
            web_search_price = float(pricing.get("tools", {}).get("web_search_call", 0.01))
        rates = models.get(model)
        if rates is None:
            if "sol" in model:
                rates = models["gpt-5.6-sol"]
            elif "luna" in model:
                rates = models["gpt-5.6-luna"]
            else:
                rates = models["gpt-5.6-terra"]
    except (OSError, KeyError, ValueError, TypeError):
        rates = {"input": 5.0, "cached_input": 0.5, "output": 30.0}
        web_search_price = 0.01
    uncached_tokens = max(0, input_tokens - cached_tokens)
    cost = (
        uncached_tokens * float(rates["input"])
        + cached_tokens * float(rates.get("cached_input", rates["input"]))
        + output_tokens * float(rates["output"])
    ) / 1_000_000 + web_search_calls * web_search_price
    return round(cost, 8)


def _extract_sources(response: Any) -> list[dict[str, str]]:
    """Extract only tool-returned sources/citations, never model-authored JSON URLs."""
    try:
        payload = response.model_dump(mode="json")
    except Exception:
        return []
    found: dict[str, dict[str, str]] = {}

    def add_source(value: Any) -> None:
        if not isinstance(value, dict):
            return
        url = value.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            return
        found[url] = {
            "url": url,
            "title": str(value.get("title") or value.get("name") or url),
            "excerpt": str(value.get("text") or value.get("snippet") or "")[:1000],
            "origin": "WEB",
        }

    output = payload.get("output", []) if isinstance(payload, dict) else []
    has_web_call = any(isinstance(item, dict) and item.get("type") == "web_search_call" for item in output)
    for item in output:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "web_search_call":
            action = item.get("action") or {}
            if isinstance(action, dict):
                for source in action.get("sources") or []:
                    add_source(source)
        elif has_web_call and item.get("type") == "message":
            for content in item.get("content") or []:
                if not isinstance(content, dict):
                    continue
                for annotation in content.get("annotations") or []:
                    if isinstance(annotation, dict) and annotation.get("type") == "url_citation":
                        add_source(annotation)
    return list(found.values())


def _count_web_search_calls(response: Any) -> int:
    try:
        payload = response.model_dump(mode="json")
    except Exception:
        return 0
    output = payload.get("output", []) if isinstance(payload, dict) else []
    return sum(1 for item in output if isinstance(item, dict) and item.get("type") == "web_search_call")
