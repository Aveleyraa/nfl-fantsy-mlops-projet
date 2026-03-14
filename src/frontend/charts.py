"""
Componentes de gráficas reutilizables con Plotly.
Cada función recibe datos limpios y devuelve un fig listo para st.plotly_chart().
"""

from typing import Any

import plotly.graph_objects as go

BLUE = "#378ADD"
GREEN = "#639922"
RED = "#E24B4A"
AMBER = "#BA7517"
GRAY = "#888780"

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="sans-serif", size=12, color="#444441"),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(showgrid=True, gridcolor="rgba(180,178,169,0.2)", zeroline=False),
)


def weekly_trend_chart(
    weekly_a: list[dict],
    metric: str,
    name_a: str,
    weekly_b: list[dict[Any, Any]] | None = None,
    name_b: str | None = None,
)-> go.Figure:
    """
    Línea de tendencia semanal para 1 o 2 jugadores.
    Si se pasan weekly_b y name_b, dibuja ambas líneas para comparar.
    """
    fig = go.Figure()

    weeks_a = [r.get("week", i + 1) for i, r in enumerate(weekly_a)]
    vals_a = [r.get(metric, 0) or 0 for r in weekly_a]

    fig.add_trace(go.Scatter(
        x=weeks_a, y=vals_a,
        mode="lines+markers",
        name=name_a,
        line=dict(color=BLUE, width=2),
        marker=dict(size=5),
        fill="tozeroy",
        fillcolor="rgba(55,138,221,0.08)",
    ))

    if weekly_b and name_b:
        weeks_b = [r.get("week", i + 1) for i, r in enumerate(weekly_b)]
        vals_b = [r.get(metric, 0) or 0 for r in weekly_b]
        fig.add_trace(go.Scatter(
            x=weeks_b, y=vals_b,
            mode="lines+markers",
            name=name_b,
            line=dict(color=GREEN, width=2),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor="rgba(99,153,34,0.08)",
        ))

    fig.update_layout(
        **_LAYOUT,
        height=220,
        xaxis_title="Semana",
        yaxis_title=metric,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def season_bar_chart(weekly: list[dict], metric: str, player_name: str)-> go.Figure:
    """
    Barras por semana con línea de promedio.
    Útil para ver consistencia de un jugador individual.
    """
    weeks = [r.get("week", i + 1) for i, r in enumerate(weekly)]
    vals = [r.get(metric, 0) or 0 for r in weekly]
    avg = sum(vals) / len(vals) if vals else 0

    fig = go.Figure(go.Bar(
        x=weeks, y=vals,
        name=player_name,
        marker_color=BLUE,
        marker_line_width=0,
    ))

    fig.add_hline(
        y=avg,
        line_dash="dash",
        line_color=RED,
        annotation_text=f"Prom: {avg:.0f}",
        annotation_position="top right",
    )

    fig.update_layout(
        **_LAYOUT,
        height=220,
        xaxis_title="Semana",
        yaxis_title=metric,
    )
    return fig


def radar_chart(
    stats_a: dict,
    stats_b: dict,
    name_a: str,
    name_b: str,
    categories: list[str],
    labels: list[str] | None = None,
)-> go.Figure:
    """
    Radar chart para comparar dos jugadores en múltiples dimensiones.
    Normaliza 0-1 tomando el máximo entre los dos jugadores por métrica.
    """
    if labels is None:
        labels = categories

    def norm(key: str) -> tuple[float, float]:
        va = float(stats_a.get(key, 0) or 0)
        vb = float(stats_b.get(key, 0) or 0)
        mx = max(va, vb, 1e-9)
        return va / mx, vb / mx

    pairs = [norm(k) for k in categories]
    vals_a = [p[0] for p in pairs]
    vals_b = [p[1] for p in pairs]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_a + [vals_a[0]],
        theta=labels + [labels[0]],
        fill="toself",
        name=name_a,
        line=dict(color=BLUE),
        fillcolor="rgba(55,138,221,0.15)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=vals_b + [vals_b[0]],
        theta=labels + [labels[0]],
        fill="toself",
        name=name_b,
        line=dict(color=GREEN),
        fillcolor="rgba(99,153,34,0.15)",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 1]),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        margin=dict(l=30, r=30, t=30, b=50),
        height=320,
    )
    return fig


def prediction_gauge(predicted: float, low: float, high: float, label: str)-> go.Figure:
    """
    Gauge para mostrar la predicción ML con intervalo de confianza.
    """
    fig = go.Figure(go.Indicator(
        mode="number+gauge",
        value=predicted,
        title=dict(text=label, font=dict(size=13)),
        gauge=dict(
            axis=dict(range=[0, high * 1.25]),
            bar=dict(color=BLUE),
            steps=[
                dict(range=[0, low], color="rgba(180,178,169,0.15)"),
                dict(range=[low, high], color="rgba(55,138,221,0.12)"),
            ],
            threshold=dict(
                line=dict(color=RED, width=2),
                thickness=0.75,
                value=predicted,
            ),
        ),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        height=220,
    )
    return fig