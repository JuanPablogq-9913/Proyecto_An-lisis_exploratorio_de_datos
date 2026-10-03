"""Hallazgos y decisiones informadas.

Cada decisión sigue la ficha de cinco componentes que exige la rúbrica
(criterio 7): hallazgo, decisión, población impactada, indicador de éxito y
riesgos/supuestos. Las cifras se calculan con los datos; la redacción de la
decisión es un **borrador del equipo** que debe ajustarse a la realidad de
cada institución antes de publicar.

Los hallazgos se calculan siempre sobre la base completa (no sobre la vista
filtrada) porque representan las conclusiones institucionales del análisis.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from .analysis import correlation, double_risk_mask, group_gap, share
from .config import ATTENDANCE_ALERT, Col, Label
from .formatting import fmt_int, fmt_number, fmt_pct, fmt_points


@dataclass(frozen=True)
class Finding:
    """Un hallazgo del tablero convertido en decisión operacionalizable."""

    title: str
    section: str
    hallazgo: str
    decision: str
    poblacion: str
    indicador: str
    riesgo: str


FindingBuilder = Callable[[pd.DataFrame], Finding | None]


def _digital_gap(df: pd.DataFrame) -> Finding | None:
    without = df.loc[df[Col.INTERNET] == Label.NO]
    if without.empty:
        return None
    public_share = share(without, Col.TIPO, Label.PUBLICA)
    return Finding(
        title="La brecha digital empieza en la matrícula",
        section="Brecha digital",
        hallazgo=(
            f"{fmt_int(len(without))} estudiantes ({fmt_pct(len(without) / len(df) * 100)}) no "
            f"tienen Internet en casa; el {fmt_pct(public_share)} de ellos está en IE públicas."
        ),
        decision=(
            "Identificar nominalmente a los estudiantes sin conexión en cada curso y "
            "rediseñar las tareas para que el componente que requiere Internet se haga "
            "en horario escolar (sala de informática, biblioteca, jornada extendida)."
        ),
        poblacion=f"{fmt_int(len(without))} estudiantes de la muestra.",
        indicador=(
            "Brecha en tasa de entrega de tareas con conexión entre estudiantes con y sin "
            "Internet: menos de 10 puntos porcentuales al cierre del semestre."
        ),
        riesgo=(
            "Supone una sala de informática funcional y coordinación docente para no "
            "saturarla. Si no existe, escalar a la secretaría de educación."
        ),
    )


def _school_type_gap(df: pd.DataFrame) -> Finding | None:
    gap = group_gap(df, Col.TIPO, Col.PROMEDIO)
    if gap is None:
        return None
    n_low = int((df[Col.TIPO] == gap.low_label).sum())
    return Finding(
        title="Dónde se estudia pesa en el promedio",
        section="Rendimiento por tipo de escuela",
        hallazgo=(
            f"Las IE {gap.high_label.lower()}s promedian {fmt_number(gap.high_mean)} y las "
            f"{gap.low_label.lower()}s {fmt_number(gap.low_mean)}: {fmt_points(gap.gap)} de diferencia."
        ),
        decision=(
            "Llevar al consejo académico un análisis de prácticas: qué hacen las IE con mejor "
            "promedio (seguimiento, tareas, retroalimentación) que pueda replicarse sin "
            "presupuesto adicional, y pilotear dos de esas prácticas en un grado."
        ),
        poblacion=f"{fmt_int(n_low)} estudiantes de IE {gap.low_label.lower()}s.",
        indicador=(
            "Variación del promedio del grado piloto frente a un grado comparable al "
            "finalizar el periodo académico."
        ),
        riesgo=(
            "Parte de la brecha refleja el estrato socioeconómico, ausente de la base; "
            "no toda la diferencia es atribuible a prácticas pedagógicas."
        ),
    )


def _double_risk(df: pd.DataFrame) -> Finding | None:
    risk = df.loc[double_risk_mask(df)]
    best = df.loc[(df[Col.TIPO] == Label.PRIVADA) & (df[Col.INTERNET] == Label.SI)]
    if risk.empty or best.empty:
        return None
    gap = best[Col.PROMEDIO].mean() - risk[Col.PROMEDIO].mean()
    return Finding(
        title="Cuando dos desventajas se suman",
        section="Cruce de tres variables",
        hallazgo=(
            f"Los {fmt_int(len(risk))} estudiantes de IE pública sin Internet promedian "
            f"{fmt_number(risk[Col.PROMEDIO].mean())}, {fmt_points(gap)} por debajo de quienes "
            "están en IE privada con Internet."
        ),
        decision=(
            "Priorizar la identificación temprana de quienes combinan ambos factores y "
            "ofrecerles acompañamiento académico focalizado durante el primer mes de cada periodo."
        ),
        poblacion=f"{fmt_int(len(risk))} estudiantes en doble riesgo.",
        indicador=(
            "Promedio del subgrupo al cierre del primer periodo frente a la línea base; "
            "meta: reducir la brecha en 0,5 puntos en un año."
        ),
        riesgo=(
            "Requiere tiempo docente asignado al acompañamiento y cuidar que la "
            "focalización no estigmatice al grupo."
        ),
    )


def _attendance(df: pd.DataFrame) -> Finding | None:
    low = df.loc[df[Col.ASISTENCIA] < ATTENDANCE_ALERT]
    r = correlation(df, Col.ASISTENCIA, Col.PROMEDIO)
    if low.empty:
        return None
    rural_share = share(low, Col.UBICACION, Label.RURAL)
    return Finding(
        title="Faltar también cuenta",
        section="Asistencia y rendimiento",
        hallazgo=(
            f"{fmt_int(len(low))} estudiantes asisten menos del {fmt_pct(ATTENDANCE_ALERT)} "
            f"({fmt_pct(rural_share)} de ellos en zona rural); la correlación entre "
            f"asistencia y promedio es r = {fmt_number(r)}."
        ),
        decision=(
            f"Instaurar un protocolo de alerta temprana: todo estudiante que baje del "
            f"{fmt_pct(ATTENDANCE_ALERT)} de asistencia en un mes activa contacto con la "
            "familia en la semana siguiente."
        ),
        poblacion=f"{fmt_int(len(low))} estudiantes con asistencia bajo el umbral.",
        indicador=(
            "Porcentaje de estudiantes en alerta que recuperan asistencia superior al "
            f"{fmt_pct(ATTENDANCE_ALERT)} en los dos meses siguientes."
        ),
        riesgo=(
            "Depende de un registro de asistencia diario y confiable; en zona rural las "
            "ausencias por cosecha requieren flexibilizar el calendario, no sancionar."
        ),
    )


def _rural_connectivity(df: pd.DataFrame) -> Finding | None:
    rural = df.loc[df[Col.UBICACION] == Label.RURAL]
    urban = df.loc[df[Col.UBICACION] == Label.URBANA]
    if rural.empty or urban.empty:
        return None
    rural_pct = share(rural, Col.INTERNET, Label.SI)
    urban_pct = share(urban, Col.INTERNET, Label.SI)
    rural_without = int((rural[Col.INTERNET] == Label.NO).sum())
    return Finding(
        title="La ruralidad no es una sola",
        section="Brecha digital",
        hallazgo=(
            f"Tiene Internet el {fmt_pct(rural_pct)} de los estudiantes rurales y el "
            f"{fmt_pct(urban_pct)} de los urbanos; {fmt_int(rural_without)} estudiantes rurales "
            "no tienen conexión."
        ),
        decision=(
            "Incluir la pregunta sobre acceso a Internet en el formulario de matrícula para "
            "conocer el dato desde el inicio del año y planear materiales offline "
            "(guías impresas, contenidos descargables) para quienes lo necesiten."
        ),
        poblacion=f"{fmt_int(len(rural))} estudiantes de zona rural.",
        indicador=(
            "Campo de conectividad diligenciado para el 100 % de los matriculados en la "
            "primera semana del año escolar."
        ),
        riesgo=(
            "El dato autorreportado puede sobreestimar la conectividad real (datos móviles "
            "intermitentes); conviene validarlo con el docente director de grupo."
        ),
    )


BUILDERS: tuple[FindingBuilder, ...] = (
    _digital_gap,
    _school_type_gap,
    _double_risk,
    _attendance,
    _rural_connectivity,
)


def build_findings(df: pd.DataFrame, limit: int = 5) -> list[Finding]:
    """Genera entre tres y cinco hallazgos con su ficha de decisión."""
    if df.empty:
        return []
    findings = [finding for build in BUILDERS if (finding := build(df)) is not None]
    return findings[:limit]
