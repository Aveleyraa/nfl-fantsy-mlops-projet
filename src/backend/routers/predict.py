"""
Router de predicciones ML.
Cuando el modelo esté entrenado, solo hay que guardar el .pkl en ml_models/
y este router lo detecta automáticamente sin cambiar nada más.
"""

import logging
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Protocol, Any, runtime_checkable, cast
from backend.services.nfl_service import get_player_stats
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predict", tags=["ml"])


# ── Esquema de respuesta ───────────────────────────────────────────────────────

class PredictionResponse(BaseModel):
    player_id: str
    player_name: str
    season_target: int
    position: str
    predicted_season_total: float
    predicted_per_game: float
    confidence_interval_low: float
    confidence_interval_high: float
    top_features: list[dict]
    model_version: str
    note: str


# ── Feature builders por posición ─────────────────────────────────────────────

QB_FEATURES = [
    "passing_yards", "passing_epa", "passing_cpoe", "pacr",
    "passing_air_yards", "sacks_suffered", "attempts",
    "completion_pct", "rushing_yards", "rushing_epa",
]

RB_FEATURES = [
    "rushing_yards", "carries", "yards_per_carry", "rushing_epa",
    "rushing_tds", "rushing_fumbles_lost",
    "receiving_yards", "targets", "target_share",
]

WR_TE_FEATURES = [
    "receiving_yards", "targets", "receptions", "receiving_epa",
    "receiving_air_yards", "target_share", "air_yards_share", "wopr", "racr",
]

FEATURE_MAP: dict[str, list[str]] = {
    "QB": QB_FEATURES,
    "RB": RB_FEATURES,
    "FB": RB_FEATURES,
    "WR": WR_TE_FEATURES,
    "TE": WR_TE_FEATURES,
}

TARGET_COL: dict[str, str] = {
    "QB": "passing_yards",
    "RB": "rushing_yards",
    "FB": "rushing_yards",
    "WR": "receiving_yards",
    "TE": "receiving_yards",
}


# ── Carga de modelo ────────────────────────────────────────────────────────────

def _load_model(position: str) -> object | None:
    """Carga el .pkl si existe. Retorna None si aún no está entrenado."""
    try:
        import joblib
        path = settings.models_path / f"model_{position.lower()}_yards.pkl"
        if path.exists():
            logger.info(f"Modelo cargado: {path}")
            return joblib.load(path)
    except Exception as e:
        logger.warning(f"No se pudo cargar el modelo para {position}: {e}")
    return None

@runtime_checkable
class MLModel(Protocol):
    def predict(self, X: Any) -> Any: ...
    feature_importances_: Any  # Opcional, para que Mypy sepa que existe
# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.get("/{player_id}/yards", response_model=PredictionResponse)
def predict_yards(
    player_id: str,
    season: int = Query(2025, ge=2000, le=2030),
    target_season: int = Query(2025, ge=2001, le=2031),
) -> PredictionResponse:
    """
    Predice yardas para la siguiente temporada.
    - Si existe ml_models/model_{position}_yards.pkl → usa el modelo entrenado.
    - Si no existe → devuelve estimación heurística (97% del valor anterior).
    La estructura de respuesta es idéntica en ambos casos.
    """
    data = get_player_stats(player_id, season)
    if not data:
        raise HTTPException(status_code=404, detail=f"Jugador {player_id} no encontrado")

    meta = data["meta"]
    totals = data["season_totals"]
    position = meta.get("position", "QB")
    player_name = meta.get("player_display_name", "")

    features = FEATURE_MAP.get(position, QB_FEATURES)
    target_col = TARGET_COL.get(position, "passing_yards")
    raw_model = _load_model(position)

    if raw_model is not None:
        model = cast(MLModel, raw_model)
        # ── Inferencia con modelo entrenado ───────────────────────────────────
        X = [[totals.get(f, 0) or 0 for f in features]]
        prediction = float(model.predict(X)[0])

        top_features = []
        if hasattr(model, "feature_importances_"):
            pairs = sorted(
                zip(features, model.feature_importances_),
                key=lambda x: -x[1]
            )
            top_features = [
                {"feature": n, "importance": round(float(i), 4)}
                for n, i in pairs[:5]
            ]

        model_version = "ml-v1.0"
        note = "Predicción con modelo entrenado."

    else:
        # ── Estimación heurística (placeholder) ───────────────────────────────
        base = totals.get(target_col, 0) or 0
        prediction = round(base * 0.97, 1)  # leve decay por regresión a la media

        top_features = [
            {"feature": f, "importance": round(1 / len(features), 4)}
            for f in features[:5]
        ]
        model_version = "heuristic-v0"
        note = (
            f"Modelo no entrenado aún. Estimación = 97% de {target_col} temporada anterior. "
            f"Guarda tu modelo en ml_models/model_{position.lower()}_yards.pkl para activarlo."
        )

    games_played = max(len(data.get("weekly", [])), 1)
    per_game = round(prediction / games_played, 1)
    margin = prediction * 0.12  # ±12% intervalo simple

    return PredictionResponse(
        player_id=player_id,
        player_name=player_name,
        season_target=target_season,
        position=position,
        predicted_season_total=round(prediction, 1),
        predicted_per_game=per_game,
        confidence_interval_low=round(prediction - margin, 1),
        confidence_interval_high=round(prediction + margin, 1),
        top_features=top_features,
        model_version=model_version,
        note=note,
    )