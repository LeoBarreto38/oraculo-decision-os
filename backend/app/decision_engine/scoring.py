from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from app.core.config import DATA_DIR


WEIGHTS_PATH = DATA_DIR / "score_weights.json"
BENEFIT_FIELDS = (
    "impact_financial",
    "speed_to_result",
    "strategic_alignment",
    "asset_value",
    "useful_learning",
    "reversibility",
    "evidence_strength",
)
PENALTY_FIELDS = (
    "cash_cost",
    "time_cost",
    "execution_risk",
    "opportunity_cost",
    "personal_pattern_risk",
    "uncertainty",
)


def load_weights(path: Path = WEIGHTS_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        weights = json.load(handle)
    validate_weights(weights)
    return weights


def validate_weights(weights: Mapping[str, Any]) -> None:
    benefits = weights.get("benefits", {})
    penalties = weights.get("penalties", {})
    if set(benefits) != set(BENEFIT_FIELDS) or set(penalties) != set(PENALTY_FIELDS):
        raise ValueError("Os pesos devem conter exatamente os critérios oficiais da v0.")
    for group in (benefits, penalties):
        for name, value in group.items():
            if not isinstance(value, (int, float)) or value < 0 or value > 10:
                raise ValueError(f"Peso inválido para {name}; use valor entre 0 e 10.")
    if sum(benefits.values()) <= 0 or sum(penalties.values()) <= 0:
        raise ValueError("Cada grupo precisa ter ao menos um peso positivo.")


def save_weights(benefits: dict[str, float], penalties: dict[str, float], path: Path = WEIGHTS_PATH) -> dict[str, Any]:
    previous = load_weights(path)
    updated = deepcopy(previous)
    updated["version"] = int(previous.get("version", 0)) + 1
    updated["benefits"] = benefits
    updated["penalties"] = penalties
    validate_weights(updated)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(updated, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, path)
    return updated


def _value(option: object | Mapping[str, Any], field: str) -> float:
    raw = option.get(field, 0) if isinstance(option, Mapping) else getattr(option, field, 0)
    return min(10.0, max(0.0, float(raw or 0)))


def score_option(option: object | Mapping[str, Any], weights: Mapping[str, Any] | None = None) -> dict[str, Any]:
    weights = weights or load_weights()
    benefits: Mapping[str, float] = weights["benefits"]
    penalties: Mapping[str, float] = weights["penalties"]
    benefit_contributions = {name: _value(option, name) * weight for name, weight in benefits.items()}
    penalty_contributions = {name: _value(option, name) * weight for name, weight in penalties.items()}
    benefit_max = 10 * sum(benefits.values())
    penalty_max = 10 * sum(penalties.values())
    benefit_index = 100 * sum(benefit_contributions.values()) / benefit_max
    penalty_index = 100 * sum(penalty_contributions.values()) / penalty_max
    score = min(100.0, max(0.0, 50 + 0.5 * benefit_index - 0.5 * penalty_index))
    probability = option.get("estimated_probability") if isinstance(option, Mapping) else getattr(option, "estimated_probability", None)
    upside = option.get("expected_upside") if isinstance(option, Mapping) else getattr(option, "expected_upside", None)
    downside = option.get("expected_downside") if isinstance(option, Mapping) else getattr(option, "expected_downside", None)
    expected_value = None
    if probability is not None and upside is not None and downside is not None:
        expected_value = float(probability) * float(upside) + (1 - float(probability)) * float(downside)
    return {
        "score": round(score, 2),
        "benefit_index": round(benefit_index, 2),
        "penalty_index": round(penalty_index, 2),
        "benefit_contributions": {key: round(value, 3) for key, value in benefit_contributions.items()},
        "penalty_contributions": {key: round(value, 3) for key, value in penalty_contributions.items()},
        "expected_value": round(expected_value, 2) if expected_value is not None else None,
        "weights_version": weights.get("version", 1),
        "disclaimer": "Score comparativo, não probabilidade objetiva nem precisão científica.",
    }


def score_decision_options(options: list[object]) -> list[dict[str, Any]]:
    weights = load_weights()
    cards: list[dict[str, Any]] = []
    for option in options:
        breakdown = score_option(option, weights)
        setattr(option, "score", breakdown["score"])
        setattr(option, "score_breakdown", breakdown)
        cards.append(
            {
                "option_id": getattr(option, "id", None),
                "title": getattr(option, "title", ""),
                **breakdown,
            }
        )
    cards.sort(key=lambda item: (-item["score"], item.get("option_id") or 0))
    return cards
