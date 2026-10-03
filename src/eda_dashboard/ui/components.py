"""Componentes visuales reutilizables (HTML ligero sobre Streamlit).

Todo texto dinámico pasa por ``html.escape`` antes de inyectarse, y el único
marcado que se admite desde la capa de narrativa es la negrita ``**así**``.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

import plotly.graph_objects as go
import streamlit as st

from ..config import TeamInfo
from ..findings import Finding

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_PLOTLY_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}


def rich_text(text: str) -> str:
    """Escapa HTML y convierte ``**negrita**`` en ``<strong>``."""
    return _BOLD.sub(r"<strong>\1</strong>", html.escape(text))


def _html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Bloques
# --------------------------------------------------------------------------- #


def hero(team: TeamInfo, total: int) -> None:
    members = " · ".join(html.escape(m.split("·")[0].strip()) for m in team.members)
    _html(
        f"""
        <div class="hero">
          <div class="eyebrow">{html.escape(team.program)} · {html.escape(team.module)}</div>
          <h1>{html.escape(team.title)}</h1>
          <p>{html.escape(team.subtitle)} Pensado para {html.escape(team.audience)}.</p>
          <div class="meta">
            {html.escape(team.team_name)} · {members} · {html.escape(team.teaching_level)}
            · {html.escape(team.analysis_date)} · Base: {total} estudiantes
          </div>
        </div>
        """
    )


@dataclass(frozen=True)
class KpiCard:
    label: str
    value: str
    hint: str = ""
    alert: bool = False


def kpi_row(cards: list[KpiCard]) -> None:
    items = "".join(
        f'<div class="kpi{" alert" if c.alert else ""}">'
        f'<div class="label">{html.escape(c.label)}</div>'
        f'<div class="value">{html.escape(c.value)}</div>'
        f'<div class="hint">{html.escape(c.hint)}</div></div>'
        for c in cards
    )
    _html(f'<div class="kpi-grid">{items}</div>')


def section_header(eyebrow: str, title: str, question: str) -> None:
    _html(
        f"""
        <div class="section">
          <div class="eyebrow">{html.escape(eyebrow)}</div>
          <h2>{html.escape(title)}</h2>
          <p class="question">{html.escape(question)}</p>
        </div>
        """
    )


def chart(title: str, figure: go.Figure) -> None:
    _html(f'<div class="chart-title">{html.escape(title)}</div>')
    st.plotly_chart(figure, width="stretch", config=_PLOTLY_CONFIG, theme=None)


def insight(text: str, *, alert: bool = False) -> None:
    _html(f'<div class="insight{" alert" if alert else ""}">{rich_text(text)}</div>')


def finding_card(index: int, finding: Finding) -> None:
    rows = (
        ("Hallazgo", finding.hallazgo),
        ("Población impactada", finding.poblacion),
        ("Indicador de éxito", finding.indicador),
        ("Riesgos y supuestos", finding.riesgo),
    )
    details = "".join(f"<dt>{label}</dt><dd>{html.escape(value)}</dd>" for label, value in rows)
    _html(
        f"""
        <div class="finding">
          <span class="tag">Decisión {index} · {html.escape(finding.section)}</span>
          <h3>{html.escape(finding.title)}</h3>
          <div class="decision"><strong>Decisión:</strong> {html.escape(finding.decision)}</div>
          <dl>{details}</dl>
        </div>
        """
    )


def footer(team: TeamInfo) -> None:
    members = "<br>".join(html.escape(m) for m in team.members)
    _html(
        f"""
        <div class="footer">
          <strong>{html.escape(team.team_name)}</strong><br>{members}<br><br>
          Análisis basado en datos simulados con fines pedagógicos. Módulo
          «{html.escape(team.module)}», {html.escape(team.program)}.
        </div>
        """
    )
