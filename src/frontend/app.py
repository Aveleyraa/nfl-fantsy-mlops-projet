"""
NFL Stats Dashboard · Streamlit
Consume la FastAPI para mostrar estadísticas por posición
y comparativa lado a lado entre dos jugadores.
"""

import streamlit as st
from typing import Any
from src.frontend import api_client as api
from src.frontend.charts import (
    weekly_trend_chart, season_bar_chart, radar_chart, prediction_gauge
)

# ── Configuración de página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="NFL Stats",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos mínimos ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stat-card {
        background: #f8f8f7;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 8px;
    }
    .stat-label { font-size: 11px; color: #888780; margin-bottom: 2px; }
    .stat-value { font-size: 24px; font-weight: 500; color: #2c2c2a; }
    .stat-value.positive { color: #185fa5; }
    .stat-value.negative { color: #e24b4a; }
    .section-header {
        font-size: 11px; font-weight: 500; color: #888780;
        text-transform: uppercase; letter-spacing: 0.08em;
        margin: 18px 0 10px;
    }
    [data-testid="stMetricValue"] { font-size: 22px !important; }
</style>
""", unsafe_allow_html=True)

# ── Columnas relevantes por posición para el chart de tendencia ────────────────
TREND_METRICS = {
    "QB":  ["passing_yards", "passing_epa", "rushing_yards", "fantasy_points"],
    "RB":  ["rushing_yards", "rushing_epa", "receiving_yards", "fantasy_points"],
    "WR":  ["receiving_yards", "receiving_epa", "targets", "fantasy_points"],
    "TE":  ["receiving_yards", "receiving_epa", "targets", "fantasy_points"],
    "DEF": ["def_tackles_solo", "def_sacks", "def_qb_hits", "def_interceptions"],
}

RADAR_METRICS = {
    "QB": {
        "keys":   ["passing_yards", "passing_tds", "completion_pct", "passing_epa", "rushing_yards"],
        "labels": ["Pass yds", "Pass TDs", "Comp%", "EPA", "Rush yds"],
    },
    "RB": {
        "keys":   ["rushing_yards", "rushing_tds", "yards_per_carry", "receiving_yards", "rushing_epa"],
        "labels": ["Rush yds", "Rush TDs", "Yds/carry", "Rec yds", "EPA"],
    },
    "WR": {
        "keys":   ["receiving_yards", "receiving_tds", "receptions", "target_share", "receiving_epa"],
        "labels": ["Rec yds", "Rec TDs", "Rec", "Target%", "EPA"],
    },
    "TE": {
        "keys":   ["receiving_yards", "receiving_tds", "receptions", "target_share", "receiving_epa"],
        "labels": ["Rec yds", "Rec TDs", "Rec", "Target%", "EPA"],
    },
}

NEGATIVE_COLS = {
    "passing_interceptions", "sacks_suffered", "sack_yards_lost",
    "sack_fumbles_lost", "rushing_fumbles_lost", "receiving_fumbles_lost",
    "penalties", "penalty_yards",
}

STAT_SECTIONS = {
    "QB": {
        "Passing": [
            ("passing_yards",              "Passing yards"),
            ("passing_tds",                "Touchdowns"),
            ("passing_interceptions",      "Intercepciones"),
            ("completion_pct",             "Completion %"),
            ("attempts",                   "Intentos"),
            ("completions",                "Compleciones"),
            ("passing_first_downs",        "1st downs"),
            ("passing_air_yards",          "Air yards"),
            ("passing_yards_after_catch",  "YAC"),
            ("passing_epa",                "Passing EPA"),
            ("passing_cpoe",               "CPOE"),
            ("pacr",                       "PACR"),
        ],
        "Rushing (QB)": [
            ("rushing_yards",   "Rush yards"),
            ("rushing_tds",     "Rush TDs"),
            ("carries",         "Carreras"),
            ("rushing_epa",     "Rush EPA"),
        ],
        "Negativas": [
            ("sacks_suffered",     "Sacks recibidos"),
            ("sack_yards_lost",    "Yards perdidas"),
            ("sack_fumbles_lost",  "Fumbles perdidos"),
        ],
        "Fantasy": [
            ("fantasy_points",     "Fantasy pts"),
            ("fantasy_points_ppr", "Fantasy pts PPR"),
        ],
    },
    "RB": {
        "Rushing": [
            ("rushing_yards",        "Rushing yards"),
            ("rushing_tds",          "Touchdowns"),
            ("carries",              "Carreras"),
            ("yards_per_carry",      "Yards/carrera"),
            ("rushing_first_downs",  "1st downs"),
            ("rushing_epa",          "Rush EPA"),
        ],
        "Receiving": [
            ("receiving_yards",       "Receiving yards"),
            ("receptions",            "Recepciones"),
            ("targets",               "Targets"),
            ("receiving_tds",         "Rec TDs"),
            ("yards_per_reception",   "Yards/recepción"),
            ("target_share",          "Target share"),
        ],
        "Negativas": [
            ("rushing_fumbles_lost",   "Fumbles rush"),
            ("receiving_fumbles_lost", "Fumbles recepción"),
        ],
        "Fantasy": [
            ("fantasy_points",     "Fantasy pts"),
            ("fantasy_points_ppr", "Fantasy pts PPR"),
        ],
    },
    "WR": {
        "Receiving": [
            ("receiving_yards",       "Receiving yards"),
            ("receiving_tds",         "Touchdowns"),
            ("receptions",            "Recepciones"),
            ("targets",               "Targets"),
            ("yards_per_reception",   "Yards/recepción"),
            ("receiving_air_yards",   "Air yards"),
            ("receiving_epa",         "Rec EPA"),
            ("racr",                  "RACR"),
            ("target_share",          "Target share"),
            ("air_yards_share",       "Air yards share"),
            ("wopr",                  "WOPR"),
        ],
        "Negativas": [
            ("receiving_fumbles_lost", "Fumbles"),
        ],
        "Fantasy": [
            ("fantasy_points",     "Fantasy pts"),
            ("fantasy_points_ppr", "Fantasy pts PPR"),
        ],
    },
    "TE": None,  # mismo que WR, se asigna abajo
    "DEF": {
        "Tacleadas": [
            ("def_tackles_solo",         "Solo tackles"),
            ("def_tackles_with_assist",  "Tackles c/asistencia"),
            ("def_tackle_assists",       "Asistencias"),
            ("def_tackles_for_loss",     "TFL"),
        ],
        "Pass rush": [
            ("def_sacks",      "Sacks"),
            ("def_sack_yards", "Sack yards"),
            ("def_qb_hits",    "QB hits"),
            ("def_fumbles_forced", "Fumbles forzados"),
        ],
        "Coverage": [
            ("def_interceptions",      "Intercepciones"),
            ("def_interception_yards", "INT yards"),
            ("def_pass_defended",      "Pases defendidos"),
        ],
        "Extras": [
            ("def_tds",     "Defensive TDs"),
            ("def_safeties","Safeties"),
        ],
    },
}
STAT_SECTIONS["TE"] = STAT_SECTIONS["WR"]
STAT_SECTIONS["FB"] = STAT_SECTIONS["RB"]


# ── Helpers de UI ──────────────────────────────────────────────────────────────

def fmt(val: Any, decimals: int = 1)-> str:
    if val is None:
        return "—"
    if isinstance(val, float):
        return f"{val:,.{decimals}f}"
    if isinstance(val, int):
        return f"{val:,}"
    return str(val)


def render_stat_card(label: str, value: Any, negative: bool = False)-> None:
    cls = "negative" if negative else "positive"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">{label}</div>
        <div class="stat-value {cls}">{fmt(value)}</div>
    </div>
    """, unsafe_allow_html=True)


def render_player_stats(data: dict, position: str)-> None:
    """Renderiza el panel de stats para UN jugador."""
    totals = data.get("season_totals", {})
    sections = STAT_SECTIONS.get(position) or STAT_SECTIONS.get("QB") or {}

    for section_name, fields in sections.items():
        st.markdown(f'<div class="section-header">{section_name}</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, (key, label) in enumerate(fields):
            val = totals.get(key)
            if val is not None:
                with cols[i % 3]:
                    is_neg = key in NEGATIVE_COLS
                    render_stat_card(label, val, negative=is_neg)


def render_player_header(meta: dict, color: str = "#378ADD")-> None:
    headshot = meta.get("headshot_url", "")
    name = meta.get("player_display_name", "—")
    position = meta.get("position", "")
    team = meta.get("team", "")

    col1, col2 = st.columns([1, 4])
    with col1:
        if headshot:
            st.image(headshot, width=72)
    with col2:
        st.markdown(f"### {name}")
        st.caption(f"{position} · {team}")


# ── Vistas principales ─────────────────────────────────────────────────────────

def view_single(season: int, season_type: str)-> None:
    st.subheader("Jugador individual")

    col_team, col_pos, col_player = st.columns([2, 2, 3])

    with col_team:
        teams = ["(todos)"] + api.get_teams(season)
        team = st.selectbox("Equipo", teams, key="single_team")
        team = None if team == "(todos)" else team

    with col_pos:
        pos_options = ["(todos)", "QB", "RB", "WR", "DEF"]
        pos_group = st.selectbox("Posición", pos_options, key="single_pos")
        pos_group = None if pos_group == "(todos)" else pos_group

    with col_player:
        players = api.get_players(season, team, pos_group, season_type)
        if not players:
            st.warning("No hay jugadores con esos filtros.")
            return
        player_map = {p["player_display_name"]: p["player_id"] for p in players}
        selected_name = st.selectbox("Jugador", list(player_map.keys()), key="single_player")

    player_id = player_map[selected_name]
    data = api.get_player_stats(player_id, season, season_type)

    if "error" in data:
        st.error(data["error"])
        return

    meta = data.get("meta", {})
    position = meta.get("position", "QB")
    weekly = data.get("weekly", [])

    render_player_header(meta)
    st.divider()

    # Stats
    render_player_stats(data, position)

    # Chart de tendencia
    if weekly:
        st.divider()
        st.markdown('<div class="section-header">Tendencia semanal</div>', unsafe_allow_html=True)
        metrics_available = TREND_METRICS.get(position, TREND_METRICS["QB"])
        metric = st.selectbox("Métrica", metrics_available, key="single_metric")
        fig = season_bar_chart(weekly, metric, selected_name)
        st.plotly_chart(fig, width='stretch')

    # Predicción ML
    st.divider()
    with st.expander("Predicción ML · próxima temporada", expanded=False):
        pred = api.get_prediction(player_id, season, season + 1)
        if "error" in pred:
            st.warning(pred["error"])
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Yardas proyectadas", f"{pred['predicted_season_total']:,.0f}")
            c2.metric("Por partido", f"{pred['predicted_per_game']:,.1f}")
            c3.metric("Intervalo ±", f"{pred['confidence_interval_low']:,.0f} – {pred['confidence_interval_high']:,.0f}")
            st.caption(f"Modelo: `{pred['model_version']}` · {pred['note']}")

            if pred.get("top_features"):
                st.markdown('<div class="section-header">Features más importantes</div>', unsafe_allow_html=True)
                for feat in pred["top_features"]:
                    st.progress(feat["importance"], text=f"`{feat['feature']}` — {feat['importance']:.2%}")


def view_compare(season: int, season_type: str)-> None:
    st.subheader("Comparar dos jugadores")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Jugador A**")
        teams_a = ["(todos)"] + api.get_teams(season)
        team_a = st.selectbox("Equipo A", teams_a, key="ca_team")
        team_a = None if team_a == "(todos)" else team_a
        pos_a = st.selectbox("Posición A", ["QB", "RB", "WR", "DEF"], key="ca_pos")
        players_a = api.get_players(season, team_a, pos_a, season_type)
        map_a = {p["player_display_name"]: p["player_id"] for p in players_a}
        name_a = st.selectbox("Jugador A", list(map_a.keys()), key="ca_player")

    with c2:
        st.markdown("**Jugador B**")
        teams_b = ["(todos)"] + api.get_teams(season)
        team_b = st.selectbox("Equipo B", teams_b, key="cb_team")
        team_b = None if team_b == "(todos)" else team_b
        pos_b = st.selectbox("Posición B", ["QB", "RB", "WR", "DEF"], key="cb_pos")
        players_b = api.get_players(season, team_b, pos_b, season_type)
        map_b = {p["player_display_name"]: p["player_id"] for p in players_b}
        name_b = st.selectbox("Jugador B", list(map_b.keys()), key="cb_player")

    if not map_a or not map_b:
        st.warning("Selecciona jugadores válidos en ambos lados.")
        return

    id_a, id_b = map_a[name_a], map_b[name_b]

    data = api.get_compare(id_a, id_b, season, season_type)
    if "error" in data:
        st.error(data["error"])
        return
    if data.get("warning"):
        st.warning(data["warning"])

    pa = data.get("player_a", {})
    pb = data.get("player_b", {})
    meta_a = pa.get("meta", {})
    meta_b = pb.get("meta", {})
    pos = meta_a.get("position", "QB")

    # Headers
    ha, hb = st.columns(2)
    with ha:
        render_player_header(meta_a)
    with hb:
        render_player_header(meta_b, color="#639922")

    st.divider()

    # Stats lado a lado
    sections = STAT_SECTIONS.get(pos) or STAT_SECTIONS.get("QB") or {}
    totals_a = pa.get("season_totals", {})
    totals_b = pb.get("season_totals", {})

    for section_name, fields in sections.items():
        st.markdown(f'<div class="section-header">{section_name}</div>', unsafe_allow_html=True)
        for key, label in fields:
            va = totals_a.get(key)
            vb = totals_b.get(key)
            if va is None and vb is None:
                continue
            va = va or 0
            vb = vb or 0
            is_neg = key in NEGATIVE_COLS
            col_a, col_mid, col_b = st.columns([3, 2, 3])
            with col_a:
                win_a = (va > vb and not is_neg) or (va < vb and is_neg)
                st.metric(label, fmt(va), delta=None,
                          label_visibility="visible")
            with col_mid:
                st.markdown(f"<div style='text-align:center;padding-top:28px;font-size:11px;color:#b4b2a9'>{label}</div>",
                            unsafe_allow_html=True)
            with col_b:
                st.metric(label, fmt(vb), label_visibility="hidden")

    # Radar
    st.divider()
    radar_cfg = RADAR_METRICS.get(pos)
    if radar_cfg:
        st.markdown('<div class="section-header">Perfil comparativo</div>', unsafe_allow_html=True)
        fig = radar_chart(totals_a, totals_b, name_a, name_b,
                          radar_cfg["keys"], radar_cfg["labels"])
        st.plotly_chart(fig, width='stretch')

    # Chart de tendencia comparado
    st.divider()
    st.markdown('<div class="section-header">Tendencia semanal</div>', unsafe_allow_html=True)
    metrics_available = TREND_METRICS.get(pos, TREND_METRICS["QB"])
    metric = st.selectbox("Métrica", metrics_available, key="compare_metric")
    fig = weekly_trend_chart(
        pa.get("weekly", []), metric, name_a,
        pb.get("weekly", []), name_b,
    )
    st.plotly_chart(fig, width='stretch')


# ── Layout principal ───────────────────────────────────────────────────────────

def main()-> None:
    # Sidebar
    with st.sidebar:
        st.title("🏈 NFL Stats")
        st.divider()

        season = st.selectbox("Temporada", [2025,2024, 2023, 2022, 2021, 2020], index=0)
        season_type = st.radio("Tipo", ["REG", "POST"], index=0,
                               format_func=lambda x: "Regular" if x == "REG" else "Playoffs")
        st.divider()
        view = st.radio("Vista", ["Individual", "Comparar 2 jugadores"])

        st.divider()
        st.caption("Datos: [nflverse](https://nflverse.nflverse.com)")
        st.caption("Backend: FastAPI · Frontend: Streamlit")

    # Main content
    if view == "Individual":
        view_single(season, season_type)
    else:
        view_compare(season, season_type)


if __name__ == "__main__":
    main()