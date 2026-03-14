"""
Servicio de datos NFL.
Wrappea nflreadpy, maneja caché en disco y expone
los datos ya filtrados por posición con las columnas relevantes.
"""

import logging
import time
import pickle
from pathlib import Path
from typing import Optional

import pandas as pd
import nflreadpy as nfl

from src.backend.config import settings

logger = logging.getLogger(__name__)

# ── Columnas por posición ──────────────────────────────────────────────────────

QB_COLS = [
    "player_id", "player_name", "player_display_name", "position",
    "headshot_url", "season", "week", "season_type",
    "team", "opponent_team",
    # Passing core
    "completions", "attempts", "passing_yards", "passing_tds",
    "passing_interceptions", "passing_first_downs",
    # Passing avanzado
    "passing_air_yards", "passing_yards_after_catch",
    "passing_epa", "passing_cpoe", "pacr",
    "passing_2pt_conversions",
    # Sacks (negativas)
    "sacks_suffered", "sack_yards_lost",
    "sack_fumbles", "sack_fumbles_lost",
    # Rushing QB
    "carries", "rushing_yards", "rushing_tds",
    "rushing_fumbles", "rushing_fumbles_lost",
    "rushing_first_downs", "rushing_epa",
    # Fantasy
    "fantasy_points", "fantasy_points_ppr",
]

RB_COLS = [
    "player_id", "player_name", "player_display_name", "position",
    "headshot_url", "season", "week", "season_type",
    "team", "opponent_team",
    # Rushing core
    "carries", "rushing_yards", "rushing_tds",
    "rushing_fumbles", "rushing_fumbles_lost",
    "rushing_first_downs", "rushing_epa",
    "rushing_2pt_conversions",
    # Receiving RB
    "receptions", "targets", "receiving_yards", "receiving_tds",
    "receiving_fumbles", "receiving_fumbles_lost",
    "receiving_yards_after_catch", "receiving_first_downs",
    "receiving_epa", "target_share",
    # Fantasy
    "fantasy_points", "fantasy_points_ppr",
]

WR_TE_COLS = [
    "player_id", "player_name", "player_display_name", "position",
    "headshot_url", "season", "week", "season_type",
    "team", "opponent_team",
    # Receiving core
    "receptions", "targets", "receiving_yards", "receiving_tds",
    "receiving_fumbles", "receiving_fumbles_lost",
    "receiving_first_downs", "receiving_epa",
    "receiving_2pt_conversions",
    # Receiving avanzado
    "receiving_air_yards", "receiving_yards_after_catch",
    "racr", "target_share", "air_yards_share", "wopr",
    # Fantasy
    "fantasy_points", "fantasy_points_ppr",
]

DEF_COLS = [
    "player_id", "player_name", "player_display_name", "position",
    "headshot_url", "season", "week", "season_type",
    "team", "opponent_team",
    # Tacleadas
    "def_tackles_solo", "def_tackles_with_assist",
    "def_tackle_assists", "def_tackles_for_loss",
    "def_tackles_for_loss_yards",
    # Pass rush
    "def_sacks", "def_sack_yards", "def_qb_hits",
    "def_fumbles_forced",
    # Coverage
    "def_interceptions", "def_interception_yards",
    "def_pass_defended",
    # Extra
    "def_tds", "def_fumbles", "def_safeties",
]

POSITION_COLS = {
    "QB":  QB_COLS,
    "RB":  RB_COLS,
    "FB":  RB_COLS,
    "WR":  WR_TE_COLS,
    "TE":  WR_TE_COLS,
    "DE":  DEF_COLS,
    "DT":  DEF_COLS,
    "LB":  DEF_COLS,
    "OLB": DEF_COLS,
    "ILB": DEF_COLS,
    "CB":  DEF_COLS,
    "S":   DEF_COLS,
    "SS":  DEF_COLS,
    "FS":  DEF_COLS,
}

POSITION_GROUPS = {
    "QB":  ["QB"],
    "RB":  ["RB", "FB"],
    "WR":  ["WR", "TE"],
    "DEF": ["DE", "DT", "LB", "OLB", "ILB", "CB", "S", "SS", "FS"],
}


# ── Caché en disco ─────────────────────────────────────────────────────────────

def _cache_key(season: int) -> Path:
    return settings.cache_path / f"player_stats_{season}.pkl"


def _is_cache_valid(path: Path) -> bool:
    if not path.exists():
        return False
    age = time.time() - path.stat().st_mtime
    return age < settings.cache_duration


def _load_from_cache(season: int) -> Optional[pd.DataFrame]:
    path = _cache_key(season)
    if _is_cache_valid(path):
        logger.info(f"Cache hit: temporada {season}")
        with open(path, "rb") as f:
            return pickle.load(f)
    return None


def _save_to_cache(season: int, df: pd.DataFrame) -> None:
    path = _cache_key(season)
    with open(path, "wb") as f:
        pickle.dump(df, f)
    logger.info(f"Cache guardado: temporada {season} ({len(df)} filas)")


# ── Carga principal ────────────────────────────────────────────────────────────

def load_season(season: int) -> pd.DataFrame:
    """
    Carga estadísticas de una temporada completa.
    Primero busca en caché local; si no existe o expiró, descarga con nflreadpy.
    """
    cached = _load_from_cache(season)
    if cached is not None:
        return cached

    logger.info(f"Descargando temporada {season} desde nflverse...")
    # nflreadpy devuelve un polars DataFrame; convertimos a pandas
    raw = nfl.load_player_stats(seasons=[season])

    if hasattr(raw, "to_pandas"):
        df = raw.to_pandas()
    else:
        df = raw  # ya es pandas

    _save_to_cache(season, df)
    return df


# ── Helpers de filtrado ────────────────────────────────────────────────────────

def _select_available_cols(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Selecciona solo las columnas que existen en el DataFrame."""
    available = [c for c in cols if c in df.columns]
    return df[available]


def get_teams(season: int) -> list[str]:
    df = load_season(season)
    return sorted(df["team"].dropna().unique().tolist())


def get_players(
    season: int,
    team: Optional[str] = None,
    position_group: Optional[str] = None,
    season_type: str = "REG",
) -> list[dict]:
    """
    Devuelve lista de jugadores únicos con nombre, posición y equipo.
    """
    df = load_season(season)

    if season_type:
        df = df[df["season_type"] == season_type]

    if team:
        df = df[df["team"] == team]

    if position_group and position_group in POSITION_GROUPS:
        positions = POSITION_GROUPS[position_group]
        df = df[df["position"].isin(positions)]

    players = (
        df[["player_id", "player_display_name", "position", "team", "headshot_url"]]
        .drop_duplicates("player_id")
        .sort_values("player_display_name")
        .fillna("")
        .to_dict("records")
    )
    return players


def get_player_stats(
    player_id: str,
    season: int,
    season_type: str = "REG",
    week: Optional[int] = None,
) -> dict:
    """
    Devuelve estadísticas de un jugador.
    Si week=None devuelve el acumulado de la temporada.
    Si week=N devuelve los datos de esa semana.
    Retorna tanto el acumulado como el detalle por semana para el chart.
    """
    df = load_season(season)
    df = df[(df["player_id"] == player_id) & (df["season_type"] == season_type)]

    if df.empty:
        return {}

    # Posición del jugador
    position = df["position"].iloc[0]
    cols = POSITION_COLS.get(position, QB_COLS)
    df = _select_available_cols(df, cols)

    # Detalle semanal (para el chart de tendencia)
    weekly = (
        df.sort_values("week")
        .fillna(0)
        .to_dict("records")
    )

    # Acumulado de temporada
    meta_cols = [
        "player_id", "player_name", "player_display_name",
        "position", "headshot_url", "team", "season",
    ]
    num_cols = [c for c in df.columns if c not in meta_cols + ["week", "season_type", "opponent_team", "game_id"]]

    season_totals = df[num_cols].sum().to_dict()

    # Algunos campos son promedios, no sumas
    avg_cols = [
        "passing_epa", "passing_cpoe", "pacr",
        "rushing_epa", "receiving_epa",
        "racr", "target_share", "air_yards_share", "wopr",
        "fantasy_points", "fantasy_points_ppr",
    ]
    for col in avg_cols:
        if col in df.columns:
            season_totals[col] = round(df[col].mean(), 2)

    # Completion %
    if "completions" in season_totals and "attempts" in season_totals:
        attempts = season_totals["attempts"]
        season_totals["completion_pct"] = (
            round(season_totals["completions"] / attempts * 100, 1)
            if attempts > 0 else 0.0
        )

    # Yards per carry
    if "rushing_yards" in season_totals and "carries" in season_totals:
        carries = season_totals["carries"]
        season_totals["yards_per_carry"] = (
            round(season_totals["rushing_yards"] / carries, 1)
            if carries > 0 else 0.0
        )

    # Yards per reception
    if "receiving_yards" in season_totals and "receptions" in season_totals:
        rec = season_totals["receptions"]
        season_totals["yards_per_reception"] = (
            round(season_totals["receiving_yards"] / rec, 1)
            if rec > 0 else 0.0
        )

    meta = df[meta_cols].iloc[0].fillna("").to_dict()

    return {
        "meta": meta,
        "season_totals": season_totals,
        "weekly": weekly,
    }


def get_compare_stats(
    player_a_id: str,
    player_b_id: str,
    season: int,
    season_type: str = "REG",
) -> dict:
    """Devuelve stats de dos jugadores para la vista de comparación."""
    a = get_player_stats(player_a_id, season, season_type)
    b = get_player_stats(player_b_id, season, season_type)
    return {"player_a": a, "player_b": b}