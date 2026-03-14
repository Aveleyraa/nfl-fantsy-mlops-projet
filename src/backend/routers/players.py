from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from backend.services.nfl_service import get_teams, get_players, get_player_stats

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/teams")
def list_teams(
    season: int = Query(2025, ge=2000, le=2030),
)-> list[dict]:
    """Lista todos los equipos disponibles en la temporada."""
    return get_teams(season)


@router.get("/")
def list_players(
    season: int = Query(2025, ge=2000, le=2030),
    team: Optional[str] = Query(None, description="Ej: KC, SF, DAL"),
    position_group: Optional[str] = Query(None, description="QB | RB | WR | DEF"),
    season_type: str = Query("REG", description="REG | POST"),
)-> list[dict]:
    """
    Lista jugadores con filtros opcionales por equipo y grupo de posición.
    Devuelve player_id, nombre, posición, equipo y headshot_url.
    """
    players = get_players(season, team, position_group, season_type)
    if not players:
        raise HTTPException(status_code=404, detail="No se encontraron jugadores con esos filtros")
    return players


@router.get("/{player_id}")
def player_stats(
    player_id: str,
    season: int = Query(2025, ge=2000, le=2030),
    season_type: str = Query("REG", description="REG | POST"),
)-> dict:
    """
    Estadísticas completas de un jugador para la temporada indicada.
    Devuelve:
    - meta: nombre, posición, equipo, headshot
    - season_totals: acumulado de toda la temporada
    - weekly: desglose semana a semana para gráficas de tendencia
    """
    data = get_player_stats(player_id, season, season_type)
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"Jugador {player_id} no encontrado en temporada {season}"
        )
    return data