"""Textos interpretativos que acompañan cada gráfico.

Los textos se calculan a partir de los datos filtrados, de modo que cuando el
usuario cambia un filtro la lectura se actualiza con el gráfico. La consigna
de la rúbrica es que cada texto "vaya más allá de leer el número": por eso
cada función compara, dimensiona (tamaño del efecto, puntos porcentuales) o
señala la implicación para la institución.

Las funciones devuelven Markdown sencillo (negritas) listo para mostrar.
"""

from __future__ import annotations

import math

import pandas as pd

from .analysis import (
    GroupGap,
    correlation,
    double_risk_mask,
    group_gap,
    share,
)
from .config import ATTENDANCE_ALERT, DISPLAY_NAMES, PASSING_GRADE, Col, Label
from .formatting import fmt_int, fmt_number, fmt_pct, fmt_points

INSUFFICIENT = (
    "Con los filtros actuales no hay suficientes estudiantes en ambos grupos para "
    "hacer esta comparación. Amplíe la selección en el panel lateral."
)


# --------------------------------------------------------------------------- #
# Vocabulario para dimensionar resultados
# --------------------------------------------------------------------------- #


def effect_size_label(d: float) -> str:
    """Interpretación convencional de la d de Cohen."""
    size = abs(d)
    if math.isnan(size):
        return "no estimable"
    if size < 0.2:
        return "trivial"
    if size < 0.5:
        return "pequeña"
    if size < 0.8:
        return "mediana"
    return "grande"


def correlation_label(r: float) -> str:
    size = abs(r)
    if math.isnan(size):
        return "no estimable"
    if size < 0.1:
        return "prácticamente nula"
    if size < 0.3:
        return "débil"
    if size < 0.5:
        return "moderada"
    return "fuerte"


#: Cómo se lee cada condición dentro de una frase ("IE pública sin Internet").
CONDITION_PHRASES: dict[tuple[str, str], str] = {
    (Col.INTERNET, Label.SI): "con Internet",
    (Col.INTERNET, Label.NO): "sin Internet",
    (Col.UBICACION, Label.URBANA): "en zona urbana",
    (Col.UBICACION, Label.RURAL): "en zona rural",
    (Col.EXTRA, Label.SI): "con extraescolares",
    (Col.EXTRA, Label.NO): "sin extraescolares",
    (Col.GENERO, Label.FEMENINO): "· estudiantes mujeres",
    (Col.GENERO, Label.MASCULINO): "· estudiantes hombres",
}


def _pct_with(df: pd.DataFrame, by: str, label: str, target: str, positive: str) -> float:
    subset = df.loc[df[by] == label]
    return share(subset, target, positive)


# --------------------------------------------------------------------------- #
# Sección: perfil y distribuciones
# --------------------------------------------------------------------------- #


def profile_insight(df: pd.DataFrame) -> str:
    publica = share(df, Col.TIPO, Label.PUBLICA)
    urbana = share(df, Col.UBICACION, Label.URBANA)
    sin_internet = share(df, Col.INTERNET, Label.NO)
    return (
        f"La muestra es mayoritariamente **pública ({fmt_pct(publica)})** y "
        f"**urbana ({fmt_pct(urbana)})**, y **{fmt_pct(sin_internet)} no tiene Internet en "
        "casa**. Cualquier promedio general está dominado por ese perfil: antes de "
        "comparar con otra institución conviene preguntarse si su composición es parecida."
    )


def grades_insight(df: pd.DataFrame) -> str:
    grades = df[Col.PROMEDIO]
    below = int((grades < PASSING_GRADE).sum())
    return (
        f"El promedio es **{fmt_number(grades.mean())}** con una desviación de "
        f"{fmt_number(grades.std())}: la mitad central está entre "
        f"{fmt_number(grades.quantile(0.25))} y {fmt_number(grades.quantile(0.75))}. "
        f"**{fmt_int(below)} estudiantes ({fmt_pct(below / len(df) * 100)}) están por debajo "
        f"de {fmt_number(PASSING_GRADE, 1)}**; son ellos, no el promedio, los que piden "
        "acción pedagógica."
    )


def attendance_insight(df: pd.DataFrame) -> str:
    attendance = df[Col.ASISTENCIA]
    alert = int((attendance < ATTENDANCE_ALERT).sum())
    return (
        f"La asistencia media es **{fmt_pct(attendance.mean(), 1)}**, pero la distribución "
        f"tiene una cola que baja hasta {fmt_pct(attendance.min(), 1)}. "
        f"**{fmt_int(alert)} estudiantes asisten menos del {fmt_pct(ATTENDANCE_ALERT)}**, "
        "el umbral a partir del cual el ausentismo suele anticipar la deserción."
    )


# --------------------------------------------------------------------------- #
# Sección: brecha digital
# --------------------------------------------------------------------------- #


def digital_gap_insight(df: pd.DataFrame) -> str:
    privada = _pct_with(df, Col.TIPO, Label.PRIVADA, Col.INTERNET, Label.SI)
    publica = _pct_with(df, Col.TIPO, Label.PUBLICA, Col.INTERNET, Label.SI)
    if math.isnan(privada) or math.isnan(publica):
        return INSUFFICIENT

    without = df.loc[df[Col.INTERNET] == Label.NO]
    share_public = share(without, Col.TIPO, Label.PUBLICA)
    concentration = (
        f"Los **{fmt_int(len(without))} estudiantes sin Internet** están "
        f"{'todos' if share_public == 100 else f'en un {fmt_pct(share_public)}'} en IE públicas."
        if len(without)
        else "Ningún estudiante de la selección carece de Internet."
    )
    return (
        f"El acceso a Internet no se distribuye de manera uniforme: lo tiene el "
        f"**{fmt_pct(privada)} de los estudiantes de IE privadas** frente al "
        f"**{fmt_pct(publica)} de las públicas**, una brecha de "
        f"{fmt_number(privada - publica, 0)} puntos porcentuales. {concentration} "
        "La línea que separa a quienes tienen conexión es la misma que más segmenta "
        "al sistema educativo colombiano."
    )


def rural_internet_insight(df: pd.DataFrame) -> str:
    urbana = _pct_with(df, Col.UBICACION, Label.URBANA, Col.INTERNET, Label.SI)
    rural = _pct_with(df, Col.UBICACION, Label.RURAL, Col.INTERNET, Label.SI)
    if math.isnan(urbana) or math.isnan(rural):
        return INSUFFICIENT
    gap = urbana - rural
    if abs(gap) < 5:
        reading = (
            "En esta base la ubicación **casi no cambia** el acceso: la brecha digital "
            "pasa por el tipo de escuela, no por la geografía. Es un resultado que "
            "contrasta con las cifras nacionales y merece discutirse."
        )
    else:
        favored = "urbanas" if gap > 0 else "rurales"
        reading = f"Las IE {favored} tienen ventaja de {fmt_number(abs(gap), 0)} puntos porcentuales."
    return (
        f"Tiene Internet el **{fmt_pct(urbana)} en zona urbana** y el "
        f"**{fmt_pct(rural)} en zona rural**. {reading}"
    )


# --------------------------------------------------------------------------- #
# Sección: rendimiento académico
# --------------------------------------------------------------------------- #


def school_type_grades_insight(df: pd.DataFrame, ranking: list[GroupGap]) -> str:
    gap = group_gap(df, Col.TIPO, Col.PROMEDIO)
    if gap is None:
        return INSUFFICIENT
    std = df[Col.PROMEDIO].std()
    in_std = gap.gap / std if std else math.nan
    is_largest = bool(ranking) and ranking[0].variable == Col.TIPO
    comparison = (
        " Es la **brecha más grande de toda la base**, mayor que cualquier diferencia "
        "por género, ubicación o acceso a Internet."
        if is_largest
        else ""
    )
    return (
        f"Las IE {gap.high_label.lower()}s promedian **{fmt_number(gap.high_mean)}** y las "
        f"{gap.low_label.lower()}s **{fmt_number(gap.low_mean)}**: una diferencia de "
        f"**{fmt_points(gap.gap)}**, equivalente a {fmt_number(in_std, 1)} desviaciones "
        f"estándar (efecto {effect_size_label(gap.effect_size)}).{comparison} La pregunta "
        "útil no es «¿cómo subir el promedio?», sino «¿qué hacen las privadas que sea "
        "replicable sin presupuesto adicional?»."
    )


def three_way_insight(df: pd.DataFrame, third: str) -> str:
    table = df.groupby([Col.TIPO, third], observed=True)[Col.PROMEDIO].agg(["mean", "size"])
    table = table.loc[table["size"] >= 1]
    if len(table) < 2:
        return INSUFFICIENT
    best_key, worst_key = table["mean"].idxmax(), table["mean"].idxmin()
    best, worst = table.loc[best_key], table.loc[worst_key]

    def describe(key: tuple[str, str]) -> str:
        school, condition = key
        return f"IE {school.lower()} {CONDITION_PHRASES.get((third, condition), condition)}"

    return (
        f"Cuando se cruzan tres variables aparece lo que ningún gráfico simple muestra: "
        f"la mejor combinación (**{describe(best_key)}**, {fmt_number(best['mean'])}) supera "
        f"a la peor (**{describe(worst_key)}**, {fmt_number(worst['mean'])}) por "
        f"**{fmt_points(best['mean'] - worst['mean'])}**. Las desventajas no se reparten al "
        f"azar: se acumulan en los mismos {fmt_int(int(worst['size']))} estudiantes."
    )


def attendance_grades_insight(df: pd.DataFrame) -> str:
    r = correlation(df, Col.ASISTENCIA, Col.PROMEDIO)
    if math.isnan(r):
        return INSUFFICIENT
    risk = df.loc[double_risk_mask(df)]
    rest = df.loc[~double_risk_mask(df)]
    risk_text = (
        f" El grupo en doble riesgo (IE pública sin Internet, en naranja) asiste en promedio "
        f"**{fmt_pct(risk[Col.ASISTENCIA].mean(), 1)}** y promedia "
        f"**{fmt_number(risk[Col.PROMEDIO].mean())}**, frente a "
        f"{fmt_pct(rest[Col.ASISTENCIA].mean(), 1)} y {fmt_number(rest[Col.PROMEDIO].mean())} "
        "del resto."
        if len(risk) and len(rest)
        else ""
    )
    direction = "positiva" if r > 0 else "negativa"
    return (
        f"La relación entre asistencia y promedio es {direction} y "
        f"**{correlation_label(r)} (r = {fmt_number(r)})**: faltar a clase no explica "
        f"por sí solo el rendimiento, pero tampoco es inocuo.{risk_text}"
    )


def gap_ranking_insight(ranking: list[GroupGap]) -> str:
    if not ranking:
        return INSUFFICIENT
    top, *others = ranking
    smallest = others[-1] if others else top
    return (
        f"De todas las variables binarias, **{DISPLAY_NAMES[Col(top.variable)].lower()}** es "
        f"la que más separa el rendimiento ({fmt_points(top.gap)}, efecto "
        f"{effect_size_label(top.effect_size)}), mientras que "
        f"**{DISPLAY_NAMES[Col(smallest.variable)].lower()}** apenas lo mueve "
        f"({fmt_points(smallest.gap)}). Para focalizar recursos, el orden de esta lista "
        "importa más que cualquier promedio general."
    )
