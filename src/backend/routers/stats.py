from fastapi import APIRouter, Query, HTTPException

from backend.services.nfl_service import get_compare_stats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/compare")
def compare_players(
    player_a: str = Query(..., description="player_id del jugador A"),
    player_b: str = Query(..., description="player_id del jugador B"),
    season: int = Query(2025, ge=2000, le=2030),
    season_type: str = Query("REG", description="REG | POST"),
)-> dict:
    """
    Comparativa lado a lado de dos jugadores.
    Devuelve player_a y player_b con la misma estructura que /players/{id}.
    Incluye warning si los jugadores son de posiciones distintas.
    """
    if player_a == player_b:
        raise HTTPException(status_code=400, detail="Los dos jugadores deben ser distintos")

    data = get_compare_stats(player_a, player_b, season, season_type)

    if not data["player_a"]:
        raise HTTPException(status_code=404, detail=f"Jugador A ({player_a}) no encontrado")
    if not data["player_b"]:
        raise HTTPException(status_code=404, detail=f"Jugador B ({player_b}) no encontrado")

    # Aviso si comparan posiciones distintas
    pos_a = data["player_a"].get("meta", {}).get("position", "")
    pos_b = data["player_b"].get("meta", {}).get("position", "")
    data["warning"] = (
        f"Comparando posiciones distintas: {pos_a} vs {pos_b}"
        if pos_a != pos_b else None
    )

    return data