from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.core.database import SessionLocal
from app.decision_engine.scoring import load_weights, score_option
from app.llm.context_builder import build_decision_context
from app.llm.context_builder import BuiltContext
from app.llm.contracts import AnalysisEvidence, DecisionAnalysis
from app.llm.router import ModelRouter, _count_web_search_calls, _extract_sources, estimate_cost_usd
from app.models.entities import AIUsage, AnalysisRun, Decision, Goal, Project, SchemaMigration
from app.services.backup import create_backup
from app.services.seed import seed_estado_zero


def test_health_seed_and_today(client):
    assert client.get("/api/health").json()["status"] == "ok"
    state = client.get("/api/state-zero").json()
    finance = state["settings"]["financial_state"]
    assert finance["cash_available"] == 0
    assert finance["monthly_income"] == 0
    assert finance["target_monthly_income"] == 0
    assert {project["name"] for project in state["projects"]} == {"DEMO: Example Project"}
    today = client.get("/api/today").json()
    assert today["financial"]["gap"] == 0
    assert len(today["priorities"]) == 1
    decisions = client.get("/api/decisions").json()
    assert any(item["code"] == "DEMO-DECISION-001" and item["importance"] == "STANDARD" for item in decisions)
    with SessionLocal() as db:
        migration = db.scalar(select(SchemaMigration).where(SchemaMigration.version == "0001_initial"))
        assert migration is not None
        assert len(migration.checksum_sha256) == 64


def test_seed_never_changes_an_existing_database(client):
    client.get("/api/health")
    with SessionLocal() as db:
        before = (
            len(list(db.scalars(select(Goal)))),
            len(list(db.scalars(select(Project)))),
            len(list(db.scalars(select(Decision)))),
        )
        assert seed_estado_zero(db) is False
        after = (
            len(list(db.scalars(select(Goal)))),
            len(list(db.scalars(select(Project)))),
            len(list(db.scalars(select(Decision)))),
        )
        assert after == before


def test_score_is_deterministic_and_auditable():
    option = {
        "impact_financial": 9,
        "speed_to_result": 8,
        "strategic_alignment": 10,
        "asset_value": 4,
        "useful_learning": 6,
        "reversibility": 9,
        "evidence_strength": 7,
        "cash_cost": 1,
        "time_cost": 6,
        "execution_risk": 4,
        "opportunity_cost": 3,
        "personal_pattern_risk": 7,
        "uncertainty": 4,
        "estimated_probability": 0.6,
        "expected_upside": 3000,
        "expected_downside": -300,
    }
    first = score_option(option, load_weights())
    second = score_option(option, load_weights())
    assert first == second
    assert 0 <= first["score"] <= 100
    assert first["expected_value"] == 1680
    assert first["weights_version"] >= 1
    assert "não probabilidade objetiva" in first["disclaimer"]


def test_decision_fallback_human_confirmation_outcome_and_brier(client):
    decision = client.post(
        "/api/decisions",
        json={
            "title": "Teste auditável",
            "question": "Executar a oferta piloto?",
            "importance": "STANDARD",
            "current_data": "NAO",
            "options": [
                {
                    "title": "Executar",
                    "impact_financial": 8,
                    "speed_to_result": 8,
                    "strategic_alignment": 9,
                    "evidence_strength": 6,
                    "reversibility": 9,
                    "cash_cost": 1,
                    "time_cost": 4,
                    "execution_risk": 4,
                    "personal_pattern_risk": 3,
                    "opportunity_cost": 2,
                    "uncertainty": 4,
                },
                {
                    "title": "Não executar",
                    "impact_financial": 1,
                    "speed_to_result": 1,
                    "strategic_alignment": 2,
                    "evidence_strength": 4,
                    "reversibility": 10,
                    "cash_cost": 0,
                    "time_cost": 0,
                    "execution_risk": 1,
                    "personal_pattern_risk": 8,
                    "opportunity_cost": 9,
                    "uncertainty": 6,
                },
            ],
            "predictions": [
                {
                    "description": "Haverá resposta comercial",
                    "probability": 0.8,
                    "target_date": (date.today() + timedelta(days=7)).isoformat(),
                    "category": "SALES",
                }
            ],
        },
    )
    assert decision.status_code == 201, decision.text
    body = decision.json()
    analyzed = client.post(f"/api/decisions/{body['id']}/analyze", json={"use_ai": False})
    assert analyzed.status_code == 200, analyzed.text
    analysis = analyzed.json()
    assert analysis["mode"] == "deterministic_fallback"
    assert analysis["analysis"]["ai_generated"] is False
    assert analysis["requires_human_confirmation"] is True
    selected_id = analysis["analysis"]["recommendation_option_id"]
    confirmed = client.post(
        f"/api/decisions/{body['id']}/confirm",
        json={"selected_option_id": selected_id, "rationale": "Teste pequeno e reversível."},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "DECIDED"
    prediction_id = confirmed.json()["predictions"][0]["id"]
    outcome = client.post(
        f"/api/decisions/{body['id']}/outcome",
        json={
            "actual_outcome": "Uma resposta comercial recebida.",
            "prediction_outcomes": [{"prediction_id": prediction_id, "outcome": 1}],
        },
    )
    assert outcome.status_code == 200
    assert outcome.json()["predictions"][0]["brier_score"] == pytest.approx(0.04)
    calibration = client.get("/api/analytics/calibration").json()
    assert calibration["mean_brier_score"] == pytest.approx(0.04)
    assert calibration["message"] == "DADOS INSUFICIENTES PARA CALIBRAÇÃO."


def test_hard_budget_limit_never_calls_and_returns_labeled_fallback(client):
    with SessionLocal() as db:
        db.add(
            AIUsage(
                model="test",
                input_tokens=0,
                cached_tokens=0,
                output_tokens=0,
                estimated_cost_usd=5.0,
                request_type="test-budget",
            )
        )
        db.commit()
    seeded = next(item for item in client.get("/api/decisions").json() if item["code"] == "DEMO-DECISION-001")
    response = client.post(f"/api/decisions/{seeded['id']}/analyze", json={"use_ai": True})
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "deterministic_fallback"
    assert body["stage"] == "PRIMARY_BUDGET_AUTHORIZATION_REQUIRED"
    assert body["budget_blocked_stage"] == "PRIMARY"
    assert body["analysis"]["budget_authorization_required"] is True
    assert "Nenhuma chamada foi feita" in body["fallback_reason"]


def test_context_is_minimal_and_auditable(client):
    with SessionLocal() as db:
        decision = db.scalar(select(Decision).where(Decision.code == "DEMO-DECISION-001"))
        context = build_decision_context(db, decision.id)
    assert len(context.sha256) == 64
    assert any(item["type"] == "Decision" and item["id"] == decision.id for item in context.record_refs)
    assert "JournalEntry" not in {item["type"] for item in context.record_refs}
    assert "DATA_BOUNDARY" in context.text


def test_alert_and_backup(client, tmp_path: Path):
    hypothesis = client.post(
        "/api/hypotheses",
        json={
            "title": "Hipótese vencida de teste",
            "test_definition": "Teste observável",
            "test_due_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        },
    )
    assert hypothesis.status_code == 201
    assert client.post("/api/alerts/run").status_code == 200
    alerts = client.get("/api/alerts").json()
    assert any(item["type"] == "HIPOTESE_VENCIDA" for item in alerts)
    archive = create_backup(tmp_path)
    assert archive.is_file()
    import zipfile

    with zipfile.ZipFile(archive) as bundle:
        names = set(bundle.namelist())
    assert {"oraculo.db", "estado-oraculo.json", "config/score_weights.json"} <= names
    assert all("env" not in name.casefold() for name in names)


def test_chat_mutations_require_confirmation(client):
    reply = client.post("/api/chat", json={"message": "Como comparar duas estratégias?", "use_ai": False})
    assert reply.status_code == 200
    body = reply.json()
    assert body["confirmation_required"] is True
    title = body["proposed_actions"][0]["payload"]["title"]
    assert not any(item["title"] == title for item in client.get("/api/decisions").json())
    confirmed = client.post(f"/api/chat/{body['message_id']}/confirm", json={"action_indexes": [0]})
    assert confirmed.status_code == 200, confirmed.text
    assert any(item["title"] == title for item in client.get("/api/decisions").json())


def test_web_sources_only_accept_tool_provenance():
    class FakeResponse:
        def model_dump(self, mode="json"):
            return {
                "output": [
                    {
                        "type": "web_search_call",
                        "action": {
                            "sources": [
                                {"url": "https://source.example/real", "title": "Fonte real"}
                            ]
                        },
                    },
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "annotations": [
                                    {
                                        "type": "url_citation",
                                        "url": "https://citation.example/real",
                                        "title": "Citação real",
                                    }
                                ],
                                "structured_model_output": {"url": "https://invented.example/not-evidence"},
                            }
                        ],
                    },
                ]
            }

    response = FakeResponse()
    urls = {item["url"] for item in _extract_sources(response)}
    assert urls == {"https://source.example/real", "https://citation.example/real"}
    assert _count_web_search_calls(response) == 1
    assert estimate_cost_usd("gpt-5.6-luna", 0, 0, 0, web_search_calls=1) == pytest.approx(0.01)


def test_analysis_evidence_uses_canonical_provenance_vocabulary():
    canonical = (
        "PERSONAL_DATA",
        "USER_STATEMENT",
        "MARKET_DATA",
        "WEB",
        "EXPERIMENT",
        "OBSERVATION",
        "MODEL_INFERENCE",
    )
    for origin in canonical:
        assert AnalysisEvidence(origin=origin, title="t", content="c").origin == origin
    with pytest.raises(ValidationError):
        AnalysisEvidence(origin="MODEL", title="t", content="c")


def test_primary_analysis_is_preserved_when_red_team_hits_hard_limit():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.core.config import get_settings
    from app.core.database import Base

    isolated_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(isolated_engine)
    settings = get_settings().model_copy(
        update={"openai_api_key": "test-only", "hard_limit_usd": 0.005, "soft_warning_usd": 0.004}
    )
    router = ModelRouter(settings)
    calls: list[str] = []

    def fake_structured(db, **kwargs):
        calls.append(kwargs["request_type"])
        assert kwargs["request_type"] == "decision_analysis"
        db.add(
            AIUsage(
                model="test",
                input_tokens=0,
                cached_tokens=0,
                output_tokens=0,
                estimated_cost_usd=0.006,
                request_type="decision_analysis",
            )
        )
        db.flush()
        parsed = DecisionAnalysis(
            recommendation="Teste pequeno",
            why=["Reversível"],
            evidence=[],
            assumptions=[],
            principal_risk="Incerteza",
            change_conditions=["Nova evidência"],
            evidence_confidence=0.5,
            next_action="Executar teste",
            review_date=date.today(),
            missing_data=[],
        )

        class EmptyResponse:
            id = "response-test"

            def model_dump(self, mode="json"):
                return {"output": []}

        return parsed, EmptyResponse()

    router._structured_response = fake_structured  # type: ignore[method-assign]
    with Session(isolated_engine) as db:
        result = router.analyze_decision(
            db,
            decision_id=1,
            importance="CRITICAL",
            context=BuiltContext(text="{}", record_refs=[], sha256="0" * 64),
            web_mode="OFF",
        )
    assert calls == ["decision_analysis"]
    assert result["analysis"]["recommendation"] == "Teste pequeno"
    assert result["red_team"] is None
    assert "red team não foi chamado" in result["red_team_warning"]


def test_red_team_resume_endpoint_does_not_repeat_primary(client):
    with SessionLocal() as db:
        decision = db.scalar(select(Decision).where(Decision.code == "DEMO-DECISION-001"))
        decision.importance = "CRITICAL"
        run = AnalysisRun(
            decision_id=decision.id,
            mode="ai",
            model="test-primary",
            scorecards=[],
            analysis={
                "recommendation": "Análise primária já paga",
                "missing_data": [
                    "A análise principal foi concluída, mas o red team não foi chamado porque o limite rígido foi atingido."
                ],
                "budget_authorization_required": True,
            },
            red_team=None,
        )
        db.add(run)
        db.commit()
        run_id = run.id
        decision_id = decision.id
    history = client.get(f"/api/decisions/{decision_id}/analyses")
    assert history.status_code == 200
    persisted = next(item for item in history.json() if item["id"] == run_id)
    assert persisted["analysis_run_id"] == run_id
    assert persisted["stage"] == "PRIMARY_COMPLETE_RED_TEAM_BUDGET_AUTHORIZATION_REQUIRED"
    assert persisted["budget_blocked_stage"] == "RED_TEAM"
    assert persisted["red_team_warning"].startswith("A análise principal foi concluída")
    assert persisted["resume_red_team"]["payload"]["analysis_run_id"] == run_id
    assert persisted["resume_red_team"]["payload"]["explicitly_authorized_over_budget"] is True
    response = client.post(
        f"/api/decisions/{decision_id}/red-team",
        json={"analysis_run_id": run_id, "explicitly_authorized_over_budget": False},
    )
    assert response.status_code == 402
    detail = response.json()["detail"]
    assert detail["code"] == "RED_TEAM_BUDGET_AUTHORIZATION_REQUIRED"
    assert detail["primary_analysis_will_not_be_repeated"] is True


def test_public_settings_exposes_backup_retention(client):
    settings = client.get("/api/settings")
    assert settings.status_code == 200
    assert settings.json()["backup_retention"] >= 1
