"""Secciones del tablero.

Cada sección responde una pregunta concreta y sigue la misma estructura que
el ejemplo resuelto de la guía: título con voz propia, pregunta, gráfico,
texto interpretativo y, cuando aplica, un KPI que dimensiona el problema.

``SECTIONS`` define el orden de lectura; agregar o quitar una sección es
cuestión de editar esa tupla.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from .. import charts, narrative
from ..analysis import GroupGap, Kpis, compute_kpis, rank_gaps
from ..config import ATTENDANCE_ALERT, DISPLAY_NAMES, PASSING_GRADE, TEAM, Col
from ..findings import build_findings
from ..formatting import fmt_int, fmt_number, fmt_pct
from . import components as ui

#: Variables binarias que se comparan en el ranking de brechas.
GAP_VARIABLES: tuple[Col, ...] = (Col.TIPO, Col.INTERNET, Col.UBICACION, Col.EXTRA, Col.GENERO)

#: Variables que el usuario puede cruzar con el tipo de escuela.
THIRD_VARIABLE_OPTIONS: tuple[Col, ...] = (Col.INTERNET, Col.UBICACION, Col.EXTRA, Col.GENERO)


@dataclass(frozen=True)
class DashboardData:
    """Insumos compartidos por todas las secciones."""

    full: pd.DataFrame
    view: pd.DataFrame
    kpis: Kpis
    ranking: list[GroupGap]

    @classmethod
    def build(cls, full: pd.DataFrame, view: pd.DataFrame) -> DashboardData:
        return cls(
            full=full,
            view=view,
            kpis=compute_kpis(view),
            ranking=rank_gaps(view, Col.PROMEDIO, GAP_VARIABLES),
        )


# --------------------------------------------------------------------------- #
# Secciones
# --------------------------------------------------------------------------- #


def overview(data: DashboardData) -> None:
    k = data.kpis
    ui.section_header(
        "1 · Panorama general",
        f"Panorama general de los {fmt_int(k.total)} estudiantes",
        "¿Qué números necesita conocer un rector si tiene 30 segundos?",
    )
    ui.kpi_row(
        [
            ui.KpiCard("Estudiantes", fmt_int(k.total), f"{fmt_pct(k.pct_publica)} en IE pública"),
            ui.KpiCard("Promedio académico", fmt_number(k.promedio), "Escala 0 a 10"),
            ui.KpiCard(
                "Asistencia promedio",
                fmt_pct(k.asistencia, 1),
                f"{fmt_int(k.asistencia_baja)} bajo el {fmt_pct(ATTENDANCE_ALERT)}",
            ),
            ui.KpiCard(
                "Con Internet en casa",
                fmt_pct(k.pct_internet),
                f"{fmt_int(k.sin_internet)} estudiantes sin conexión",
            ),
            ui.KpiCard("En doble riesgo", fmt_int(k.doble_riesgo), "IE pública y sin Internet", alert=True),
        ]
    )


def distributions(data: DashboardData) -> None:
    df = data.view
    ui.section_header(
        "2 · Análisis univariado",
        "¿Cómo es el grupo que tenemos?",
        "Antes de comparar, conviene saber quiénes componen la muestra y cómo se reparten "
        "las notas y la asistencia.",
    )
    ui.chart("Perfil de la muestra (% de estudiantes)", charts.sample_profile(df))
    ui.insight(narrative.profile_insight(df))

    left, right = st.columns(2, gap="large")
    with left:
        ui.chart(
            "Distribución del promedio de calificaciones",
            charts.histogram(
                df,
                Col.PROMEDIO,
                bin_size=0.5,
                reference=(PASSING_GRADE, f"Aprobación {fmt_number(PASSING_GRADE, 1)}"),
            ),
        )
        ui.insight(narrative.grades_insight(df))
    with right:
        ui.chart(
            "Distribución de la asistencia",
            charts.histogram(
                df,
                Col.ASISTENCIA,
                bin_size=2.5,
                reference=(ATTENDANCE_ALERT, f"Alerta {fmt_pct(ATTENDANCE_ALERT)}"),
            ),
        )
        ui.insight(narrative.attendance_insight(df), alert=True)


def digital_gap(data: DashboardData) -> None:
    df = data.view
    ui.section_header(
        "3 · Brecha digital",
        "La brecha digital empieza en la matrícula",
        "¿Cuántos estudiantes acceden a Internet en casa según la escuela en la que están?",
    )
    left, right = st.columns(2, gap="large")
    with left:
        ui.chart("Internet en casa según tipo de escuela", charts.stacked_share(df, Col.TIPO, Col.INTERNET))
        ui.insight(narrative.digital_gap_insight(df))
    with right:
        ui.chart(
            "Internet en casa según ubicación de la escuela",
            charts.stacked_share(df, Col.UBICACION, Col.INTERNET),
        )
        ui.insight(narrative.rural_internet_insight(df))


def school_type_performance(data: DashboardData) -> None:
    df = data.view
    ui.section_header(
        "4 · Rendimiento académico",
        "Dónde se estudia pesa en el promedio",
        "¿Cuánto cambia el promedio de calificaciones entre IE públicas y privadas?",
    )
    left, right = st.columns([3, 2], gap="large")
    with left:
        ui.chart("Promedio de calificaciones por tipo de escuela", charts.box_by(df, Col.TIPO, Col.PROMEDIO))
    with right:
        st.write("")
        ui.insight(narrative.school_type_grades_insight(df, data.ranking))
        st.caption("La caja muestra el 50 % central; la línea punteada interior, la media.")


def combined_disadvantage(data: DashboardData) -> None:
    df = data.view
    ui.section_header(
        "5 · Cruce de tres variables",
        "Cuando dos desventajas se suman",
        "¿Cómo depende el promedio, a la vez, del tipo de escuela y de una segunda condición?",
    )
    third = st.radio(
        "Cruzar el tipo de escuela con:",
        options=THIRD_VARIABLE_OPTIONS,
        format_func=lambda col: DISPLAY_NAMES[col],
        horizontal=True,
        key="third_variable",
    )
    ui.chart(
        f"Promedio por tipo de escuela y {DISPLAY_NAMES[third].lower()}",
        charts.grouped_means(df, Col.TIPO, third, Col.PROMEDIO),
    )
    ui.insight(narrative.three_way_insight(df, third), alert=True)


def attendance_and_grades(data: DashboardData) -> None:
    df = data.view
    ui.section_header(
        "6 · Asistencia y rendimiento",
        "Faltar también cuenta",
        "¿Los estudiantes que más faltan son los que menos rinden? ¿Dónde está el grupo en riesgo?",
    )
    ui.chart("Asistencia frente a promedio (cada punto es un estudiante)", charts.attendance_vs_grades(df))
    ui.insight(narrative.attendance_grades_insight(df))


def gap_ranking(data: DashboardData) -> None:
    ui.section_header(
        "7 · Síntesis",
        "¿Qué variable separa más a los estudiantes?",
        "Si hubiera que focalizar recursos, ¿por dónde empezar?",
    )
    if not data.ranking:
        ui.insight(narrative.INSUFFICIENT)
        return
    ui.chart("Brecha de promedio que genera cada variable", charts.gap_ranking(data.ranking))
    ui.insight(narrative.gap_ranking_insight(data.ranking))


def findings_and_decisions(data: DashboardData) -> None:
    ui.section_header(
        "8 · Hallazgos y decisiones",
        "De los datos a las decisiones",
        "Cada hallazgo se traduce en una decisión con población, indicador y riesgos explícitos. "
        "Se calculan sobre la base completa, independientemente de los filtros.",
    )
    for index, finding in enumerate(build_findings(data.full), start=1):
        ui.finding_card(index, finding)


def data_table(data: DashboardData) -> None:
    with st.expander(f"Ver los datos de la vista actual ({fmt_int(len(data.view))} registros)"):
        st.dataframe(data.view, width="stretch", hide_index=True)
        st.download_button(
            "Descargar vista en CSV",
            data=data.view.to_csv(index=False).encode("utf-8-sig"),
            file_name="vista_filtrada.csv",
            mime="text/csv",
        )
    ui.footer(TEAM)


Section = Callable[[DashboardData], None]

SECTIONS: tuple[Section, ...] = (
    overview,
    distributions,
    digital_gap,
    school_type_performance,
    combined_disadvantage,
    attendance_and_grades,
    gap_ranking,
    findings_and_decisions,
    data_table,
)
