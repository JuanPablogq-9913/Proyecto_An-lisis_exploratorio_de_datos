"""Constructores de gráficos (Plotly).

Convenciones visuales, aplicadas en todos los gráficos:

* Azul para los datos principales; naranja solo para el grupo en desventaja.
* Un único eje Y por gráfico, rejilla tenue y sin bordes de caja.
* Etiquetas directas en las barras y tooltip en español en cada marca.
* El tipo de gráfico sigue al tipo de variable: histogramas para numéricas,
  barras horizontales para proporciones, barras apiladas al 100 % para
  cruces de proporciones, cajas para categórica × numérica y dispersión para
  numérica × numérica.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .analysis import GroupGap, double_risk_mask, proportion_by, share
from .config import (
    ATTENDANCE_ALERT,
    CATEGORIES,
    COLOR_BY_LABEL,
    DISPLAY_NAMES,
    PALETTE,
    PASSING_GRADE,
    Col,
    Label,
)
from .formatting import fmt_number, fmt_pct

FONT_FAMILY = "Inter, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
DEFAULT_HEIGHT = 360


# --------------------------------------------------------------------------- #
# Estilo base
# --------------------------------------------------------------------------- #


def _style(fig: go.Figure, *, height: int = DEFAULT_HEIGHT, show_legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height,
        font=dict(family=FONT_FAMILY, size=13, color=PALETTE.ink),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=12, r=24, t=40 if show_legend else 16, b=12),
        showlegend=show_legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            title_text="",
            font_size=12,
            traceorder="normal",
        ),
        hoverlabel=dict(bgcolor=PALETTE.surface, bordercolor=PALETTE.grid, font_color=PALETTE.ink),
        barcornerradius=4,
        bargap=0.35,
    )
    axis = dict(
        title_font=dict(size=12, color=PALETTE.ink_muted),
        tickfont=dict(size=12, color=PALETTE.ink_muted),
        zeroline=False,
        linecolor=PALETTE.grid,
        automargin=True,
        title_standoff=12,
    )
    fig.update_xaxes(showgrid=False, **axis)
    fig.update_yaxes(gridcolor=PALETTE.grid, **axis)
    return fig


def _color(label: str) -> str:
    return COLOR_BY_LABEL.get(label, PALETTE.primary)


def _reference_line(fig: go.Figure, x: float, text: str) -> None:
    fig.add_vline(
        x=x,
        line=dict(color=PALETTE.ink_muted, width=1.5, dash="dot"),
        annotation=dict(text=text, font=dict(size=11, color=PALETTE.ink_muted), yanchor="top"),
        annotation_position="top right",
    )


# --------------------------------------------------------------------------- #
# Univariado
# --------------------------------------------------------------------------- #


def sample_profile(df: pd.DataFrame) -> go.Figure:
    """Barras horizontales con el porcentaje de cada característica binaria."""
    rows = [
        ("Con Internet en casa", share(df, Col.INTERNET, Label.SI)),
        ("En IE pública", share(df, Col.TIPO, Label.PUBLICA)),
        ("En zona rural", share(df, Col.UBICACION, Label.RURAL)),
        ("Participa en extraescolares", share(df, Col.EXTRA, Label.SI)),
        ("Género femenino", share(df, Col.GENERO, Label.FEMENINO)),
    ]
    data = pd.DataFrame(rows, columns=["rasgo", "pct"]).sort_values("pct")
    fig = go.Figure(
        go.Bar(
            x=data["pct"],
            y=data["rasgo"],
            orientation="h",
            marker=dict(color=PALETTE.primary, line=dict(color=PALETTE.surface, width=2)),
            text=[fmt_pct(v) for v in data["pct"]],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x:.1f} %<extra></extra>",
        )
    )
    fig.update_xaxes(range=[0, 110], ticksuffix=" %", showticklabels=False)
    fig.update_yaxes(showgrid=False)
    return _style(fig, height=300, show_legend=False)


def histogram(
    df: pd.DataFrame,
    column: str,
    *,
    bin_size: float,
    reference: tuple[float, str] | None = None,
) -> go.Figure:
    """Histograma de una variable numérica con línea de referencia opcional."""
    fig = go.Figure(
        go.Histogram(
            x=df[column],
            xbins=dict(size=bin_size),
            marker=dict(color=PALETTE.primary, line=dict(color=PALETTE.surface, width=2)),
            hovertemplate="%{x}<br>%{y} estudiantes<extra></extra>",
        )
    )
    mean = df[column].mean()
    _reference_line(fig, mean, f"Media {fmt_number(mean, 1)}")
    if reference is not None:
        value, text = reference
        fig.add_vline(
            x=value,
            line=dict(color=PALETTE.accent, width=2),
            annotation=dict(text=text, font=dict(size=11, color=PALETTE.accent), yanchor="top"),
            annotation_position="top left",
        )
    fig.update_xaxes(title_text=DISPLAY_NAMES[Col(column)])
    fig.update_yaxes(title_text="Estudiantes")
    return _style(fig, show_legend=False)


# --------------------------------------------------------------------------- #
# Bivariado
# --------------------------------------------------------------------------- #


def stacked_share(df: pd.DataFrame, by: str, target: str) -> go.Figure:
    """Barras apiladas al 100 %: composición de ``target`` dentro de cada grupo de ``by``."""
    table = proportion_by(df, by, target)
    fig = go.Figure()
    for label in CATEGORIES[Col(target)]:
        part = table.loc[table[target] == label]
        fig.add_bar(
            name=f"{DISPLAY_NAMES[Col(target)]}: {label}",
            y=part[by].astype(str),
            x=part["pct"],
            customdata=part["n"],
            orientation="h",
            marker=dict(color=_color(label), line=dict(color=PALETTE.surface, width=2)),
            text=[fmt_pct(v) if v >= 6 else "" for v in part["pct"]],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color=PALETTE.surface, size=13),
            hovertemplate=("%{y} · " + label + "<br>%{x:.1f} % (%{customdata} estudiantes)<extra></extra>"),
        )
    fig.update_layout(barmode="stack")
    fig.update_xaxes(range=[0, 100], ticksuffix=" %", title_text="Porcentaje de estudiantes")
    fig.update_yaxes(showgrid=False, title_text="", autorange="reversed")
    return _style(fig, height=260)


def box_by(df: pd.DataFrame, by: str, value: str) -> go.Figure:
    """Diagrama de caja de una variable numérica por grupo."""
    fig = go.Figure()
    for label in CATEGORIES[Col(by)]:
        values = df.loc[df[by] == label, value]
        if values.empty:
            continue
        fig.add_box(
            y=values,
            name=label,
            marker=dict(color=_color(label), size=5),
            line=dict(width=2),
            fillcolor=PALETTE.accent_soft if _color(label) == PALETTE.accent else PALETTE.primary_soft,
            boxmean=True,
            boxpoints="outliers",
            hovertemplate=f"{label}<br>%{{y:.2f}}<extra></extra>",
        )
    fig.add_hline(
        y=PASSING_GRADE,
        line=dict(color=PALETTE.ink_muted, width=1, dash="dot"),
        annotation=dict(text=f"Aprobación {fmt_number(PASSING_GRADE, 1)}", font_size=11),
        annotation_position="bottom right",
    )
    fig.update_yaxes(title_text=DISPLAY_NAMES[Col(value)], range=[0, 10.5])
    fig.update_xaxes(title_text=DISPLAY_NAMES[Col(by)])
    return _style(fig, show_legend=False)


def grouped_means(df: pd.DataFrame, by: str, color_by: str, value: str) -> go.Figure:
    """Cruce de tres variables: media de ``value`` por ``by`` y ``color_by``."""
    table = df.groupby([by, color_by], observed=True)[value].agg(["mean", "size"]).reset_index()
    fig = go.Figure()
    for label in CATEGORIES[Col(color_by)]:
        part = table.loc[table[color_by] == label]
        if part.empty:
            continue
        fig.add_bar(
            name=f"{DISPLAY_NAMES[Col(color_by)]}: {label}",
            x=part[by].astype(str),
            y=part["mean"],
            customdata=part["size"],
            marker=dict(color=_color(label), line=dict(color=PALETTE.surface, width=2)),
            text=[fmt_number(v) for v in part["mean"]],
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "%{x} · " + label + "<br>Promedio %{y:.2f}<br>%{customdata} estudiantes<extra></extra>"
            ),
        )
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08)
    fig.update_yaxes(title_text=DISPLAY_NAMES[Col(value)], range=[0, 10.5])
    fig.update_xaxes(title_text=DISPLAY_NAMES[Col(by)])
    return _style(fig)


def attendance_vs_grades(df: pd.DataFrame) -> go.Figure:
    """Dispersión asistencia × promedio, resaltando el grupo en doble riesgo."""
    risk = double_risk_mask(df)
    groups = (
        ("Resto de estudiantes", df.loc[~risk], PALETTE.primary, 0.55),
        ("IE pública sin Internet", df.loc[risk], PALETTE.accent, 0.9),
    )
    fig = go.Figure()
    for name, part, color, opacity in groups:
        if part.empty:
            continue
        fig.add_scatter(
            x=part[Col.ASISTENCIA],
            y=part[Col.PROMEDIO],
            mode="markers",
            name=name,
            marker=dict(color=color, size=9, opacity=opacity, line=dict(color=PALETTE.surface, width=1)),
            customdata=part[[Col.ID, Col.GRADO]],
            hovertemplate=(
                "Estudiante %{customdata[0]} · grado %{customdata[1]}<br>"
                "Asistencia %{x:.1f} %<br>Promedio %{y:.2f}<extra>" + name + "</extra>"
            ),
        )
    _reference_line(fig, ATTENDANCE_ALERT, f"Alerta {fmt_pct(ATTENDANCE_ALERT)}")
    fig.update_xaxes(
        title_text=DISPLAY_NAMES[Col.ASISTENCIA], ticksuffix=" %", showgrid=True, gridcolor=PALETTE.grid
    )
    fig.update_yaxes(title_text=DISPLAY_NAMES[Col.PROMEDIO])
    return _style(fig, height=400)


def gap_ranking(ranking: list[GroupGap]) -> go.Figure:
    """Ranking de variables según la brecha de promedio que generan entre sus categorías."""
    data = pd.DataFrame(
        {
            "variable": [DISPLAY_NAMES[Col(g.variable)] for g in ranking],
            "gap": [g.gap for g in ranking],
            "detalle": [
                f"{g.high_label} {fmt_number(g.high_mean)} vs {g.low_label} {fmt_number(g.low_mean)}"
                for g in ranking
            ],
        }
    ).iloc[::-1]
    fig = go.Figure(
        go.Bar(
            x=data["gap"],
            y=data["variable"],
            orientation="h",
            marker=dict(color=PALETTE.primary, line=dict(color=PALETTE.surface, width=2)),
            text=[f"{fmt_number(v)} pts" for v in data["gap"]],
            textposition="outside",
            cliponaxis=False,
            customdata=data["detalle"],
            hovertemplate="%{y}<br>%{customdata}<br>Brecha: %{x:.2f} puntos<extra></extra>",
        )
    )
    fig.update_xaxes(
        title_text="Diferencia de promedio entre categorías (puntos)",
        range=[0, max(data["gap"].max() * 1.25, 0.5)],
    )
    fig.update_yaxes(showgrid=False)
    return _style(fig, height=300, show_legend=False)
