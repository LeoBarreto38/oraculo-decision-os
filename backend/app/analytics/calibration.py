from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Prediction


INSUFFICIENT_MESSAGE = "DADOS INSUFICIENTES PARA CALIBRAÇÃO."
BANDS = ((0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0))


def brier_score(probability: float, outcome: float) -> float:
    if not 0 <= probability <= 1 or not 0 <= outcome <= 1:
        raise ValueError("Probabilidade e resultado devem estar entre 0 e 1.")
    return round((probability - outcome) ** 2, 6)


def resolve_prediction(prediction: Prediction, outcome: float) -> float:
    from app.models.entities import utcnow

    prediction.outcome = outcome
    prediction.resolved_at = utcnow()
    prediction.brier_score = brier_score(prediction.probability, outcome)
    return prediction.brier_score


def calibration_report(db: Session, minimum_per_band: int = 3) -> dict[str, Any]:
    predictions = list(
        db.scalars(
            select(Prediction)
            .where(Prediction.outcome.is_not(None), Prediction.brier_score.is_not(None))
            .order_by(Prediction.resolved_at)
        )
    )
    if not predictions:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": INSUFFICIENT_MESSAGE,
            "resolved_predictions": 0,
            "mean_brier_score": None,
            "mean_absolute_error": None,
            "accuracy_by_category": {},
            "bands": _empty_bands(),
            "statistical_significance": None,
        }

    categories: dict[str, list[bool]] = defaultdict(list)
    bands: list[dict[str, Any]] = []
    for lower, upper in BANDS:
        if upper == 1:
            members = [p for p in predictions if lower <= p.probability <= upper]
        else:
            members = [p for p in predictions if lower <= p.probability < upper]
        bands.append(
            {
                "range": f"{int(lower * 100)}–{int(upper * 100)}%",
                "count": len(members),
                "mean_forecast": round(sum(p.probability for p in members) / len(members), 4) if members else None,
                "observed_frequency": round(sum(float(p.outcome or 0) for p in members) / len(members), 4)
                if members
                else None,
                "sufficient": len(members) >= minimum_per_band,
            }
        )
    for prediction in predictions:
        categories[prediction.category or "UNCATEGORIZED"].append(
            (prediction.probability >= 0.5) == (float(prediction.outcome or 0) >= 0.5)
        )
    accuracy = {
        category: {"count": len(values), "accuracy": round(sum(values) / len(values), 4)}
        for category, values in categories.items()
    }
    sufficiently_calibrated = len(predictions) >= 10 and any(item["sufficient"] for item in bands)
    return {
        "status": "AVAILABLE" if sufficiently_calibrated else "INSUFFICIENT_DATA",
        "message": None if sufficiently_calibrated else INSUFFICIENT_MESSAGE,
        "resolved_predictions": len(predictions),
        "mean_brier_score": round(sum(float(p.brier_score or 0) for p in predictions) / len(predictions), 6),
        "mean_absolute_error": round(
            sum(abs(p.probability - float(p.outcome or 0)) for p in predictions) / len(predictions), 6
        ),
        "accuracy_by_category": accuracy,
        "bands": bands,
        "statistical_significance": None,
        "note": "A v0 descreve o histórico; não infere significância estatística.",
    }


def _empty_bands() -> list[dict[str, Any]]:
    return [
        {
            "range": f"{int(lower * 100)}–{int(upper * 100)}%",
            "count": 0,
            "mean_forecast": None,
            "observed_frequency": None,
            "sufficient": False,
        }
        for lower, upper in BANDS
    ]


class FutureAnalytics:
    """Stable v0 interface for future numerical modules; methods intentionally unimplemented."""

    def monte_carlo(self, *_args: object, **_kwargs: object) -> None:
        raise NotImplementedError("Planejado após a v0.")

    def bayesian_update(self, *_args: object, **_kwargs: object) -> None:
        raise NotImplementedError("Planejado após a v0.")

    def sensitivity_analysis(self, *_args: object, **_kwargs: object) -> None:
        raise NotImplementedError("Planejado após a v0.")
