"""
Cliente HTTP para consumir la FastAPI desde Streamlit.
Centraliza todas las llamadas para que la UI no sepa nada de requests.
"""

import os
import requests
from typing import Any
from typing import Optional

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
TIMEOUT = 15


def _get(path: str, params: dict[Any, Any] | None = None) -> dict[Any, Any] | list[Any] | None:
    try:
        resp = requests.get(f"{API_BASE}{path}", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"error": "No se puede conectar con la API. ¿Está corriendo el backend?"}
    except requests.exceptions.HTTPError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def get_teams(season: int) -> list[str]:
    result = _get("/players/teams", {"season": season})
    return result if isinstance(result, list) else []


def get_players(
    season: int,
    team: Optional[str] = None,
    position_group: Optional[str] = None,
    season_type: str = "REG",
) -> list[dict]:
    params = {"season": season, "season_type": season_type}
    if team:
        params["team"] = team
    if position_group:
        params["position_group"] = position_group
    result = _get("/players/", params)
    return result if isinstance(result, list) else []


def get_player_stats(
    player_id: str,
    season: int,
    season_type: str = "REG",
) -> dict[Any, Any]:
    result = _get(f"/players/{player_id}", {"season": season, "season_type": season_type})
    # Validamos explícitamente que sea un diccionario
    if isinstance(result, dict):
        return result
        
    # Si es una lista o None, devolvemos un dict vacío para no romper el contrato
    return {}


def get_compare(
    player_a_id: str,
    player_b_id: str,
    season: int,
    season_type: str = "REG",
) -> dict[Any, Any]:
    result = _get("/stats/compare", {
        "player_a": player_a_id,
        "player_b": player_b_id,
        "season": season,
        "season_type": season_type,
    })
    # Validamos explícitamente que sea un diccionario
    if isinstance(result, dict):
        return result
        
    # Si es una lista o None, devolvemos un dict vacío para no romper el contrato
    return {}


def get_prediction(
    player_id: str,
    season: int,
    target_season: int,
) -> dict[Any, Any]:
    result = _get(f"/predict/{player_id}/yards", {
        "season": season,
        "target_season": target_season,
    })
    # Validamos explícitamente que sea un diccionario
    if isinstance(result, dict):
        return result
        
    # Si es una lista o None, devolvemos un dict vacío para no romper el contrato
    return {}