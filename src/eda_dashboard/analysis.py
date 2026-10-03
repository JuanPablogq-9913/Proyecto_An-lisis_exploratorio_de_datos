"""Cálculos del análisis exploratorio.

Funciones puras sobre ``pandas.DataFrame``: no dependen de Streamlit ni de
Plotly, de modo que se pueden probar de forma aislada y reutilizar desde un
notebook. Cuando un cálculo no es posible con los datos disponibles (por
ejemplo, un filtro dejó un solo grupo), se devuelve ``NaN`` o ``None`` en vez
de lanzar una excepción; la capa de narrativa decide cómo comunicarlo.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd

from .config import ATTENDANCE_ALERT, CATEGORIES, Col, Label

# --------------------------------------------------------------------------- #
# Filtros
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class FilterSelection:
    """Selección activa de los filtros del tablero."""

    ubicacion: tuple[str, ...]
    tipo: tuple[str, ...]
    genero: tuple[str, ...]
    grados: tuple[int, int]

    @classmethod
    def everything(cls, df: pd.DataFrame) -> FilterSelection:
        """Selección que no excluye a ningún estudiante."""
        return cls(
            ubicacion=CATEGORIES[Col.UBICACION],
            tipo=CATEGORIES[Col.TIPO],
            genero=CATEGORIES[Col.GENERO],
            grados=(int(df[Col.GRADO].min()), int(df[Col.GRADO].max())),
        )

    def is_everything(self, df: pd.DataFrame) -> bool:
        return self == FilterSelection.everything(df)


def apply_filters(df: pd.DataFrame, selection: FilterSelection) -> pd.DataFrame:
    """Devuelve el subconjunto de estudiantes que cumple la selección."""
    low, high = selection.grados
    mask = (
        df[Col.UBICACION].isin(selection.ubicacion)
        & df[Col.TIPO].isin(selection.tipo)
        & df[Col.GENERO].isin(selection.genero)
        & df[Col.GRADO].between(low, high)
    )
    return df.loc[mask]


# --------------------------------------------------------------------------- #
# Indicadores clave (KPI)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Kpis:
    total: int
    promedio: float
    asistencia: float
    pct_internet: float
    sin_internet: int
    pct_publica: float
    pct_rural: float
    doble_riesgo: int
    asistencia_baja: int


def compute_kpis(df: pd.DataFrame) -> Kpis:
    """Resume la base en los indicadores que van en las tarjetas superiores."""
    return Kpis(
        total=len(df),
        promedio=_safe_mean(df[Col.PROMEDIO]),
        asistencia=_safe_mean(df[Col.ASISTENCIA]),
        pct_internet=share(df, Col.INTERNET, Label.SI),
        sin_internet=int((df[Col.INTERNET] == Label.NO).sum()),
        pct_publica=share(df, Col.TIPO, Label.PUBLICA),
        pct_rural=share(df, Col.UBICACION, Label.RURAL),
        doble_riesgo=int(double_risk_mask(df).sum()),
        asistencia_baja=int((df[Col.ASISTENCIA] < ATTENDANCE_ALERT).sum()),
    )


def double_risk_mask(df: pd.DataFrame) -> pd.Series:
    """Estudiantes que combinan los dos factores de riesgo: IE pública y sin Internet."""
    return (df[Col.TIPO] == Label.PUBLICA) & (df[Col.INTERNET] == Label.NO)


# --------------------------------------------------------------------------- #
# Univariado
# --------------------------------------------------------------------------- #


def share(df: pd.DataFrame, column: str, label: str) -> float:
    """Porcentaje (0–100) de estudiantes con ``label`` en ``column``."""
    if df.empty:
        return math.nan
    return float((df[column] == label).mean() * 100)


def describe_numeric(df: pd.DataFrame, column: str) -> pd.Series:
    """Estadísticos descriptivos de una variable numérica."""
    return df[column].describe(percentiles=[0.25, 0.5, 0.75])


# --------------------------------------------------------------------------- #
# Bivariado y multivariado
# --------------------------------------------------------------------------- #


def proportion_by(df: pd.DataFrame, by: str, target: str) -> pd.DataFrame:
    """Distribución porcentual de ``target`` dentro de cada grupo de ``by``.

    Devuelve un formato largo con columnas ``[by, target, n, pct]`` donde
    ``pct`` suma 100 dentro de cada grupo. Los grupos vacíos se omiten.
    """
    counts = df.groupby([by, target], observed=False).size().rename("n").reset_index()
    totals = counts.groupby(by, observed=False)["n"].transform("sum")
    counts["pct"] = counts["n"] / totals.where(totals > 0) * 100
    return counts.loc[totals > 0].reset_index(drop=True)


def mean_by(df: pd.DataFrame, by: str | list[str], value: str) -> pd.DataFrame:
    """Media, desviación estándar, mediana y tamaño de ``value`` por grupo."""
    grouped = df.groupby(by, observed=True)[value]
    return grouped.agg(n="size", media="mean", desviacion="std", mediana="median").reset_index()


def mean_gap(df: pd.DataFrame, by: str, value: str, high: str, low: str) -> float:
    """Diferencia de medias ``value[high] − value[low]`` (``NaN`` si falta un grupo)."""
    means = df.groupby(by, observed=True)[value].mean()
    if high not in means or low not in means:
        return math.nan
    return float(means[high] - means[low])


def cohens_d(a: pd.Series, b: pd.Series) -> float:
    """Tamaño del efecto (d de Cohen con desviación combinada)."""
    n_a, n_b = len(a), len(b)
    if n_a < 2 or n_b < 2:
        return math.nan
    pooled_var = ((n_a - 1) * a.var() + (n_b - 1) * b.var()) / (n_a + n_b - 2)
    if pooled_var <= 0:
        return math.nan
    return float((a.mean() - b.mean()) / math.sqrt(pooled_var))


@dataclass(frozen=True)
class GroupGap:
    """Brecha de una variable numérica entre las dos categorías de una variable binaria."""

    variable: str
    high_label: str
    low_label: str
    high_mean: float
    low_mean: float
    gap: float
    effect_size: float


def group_gap(df: pd.DataFrame, by: str, value: str) -> GroupGap | None:
    """Compara las dos categorías de ``by`` en ``value`` (``None`` si falta un grupo)."""
    means = df.groupby(by, observed=True)[value].mean()
    if len(means) < 2:
        return None
    high_label, low_label = means.idxmax(), means.idxmin()
    high = df.loc[df[by] == high_label, value]
    low = df.loc[df[by] == low_label, value]
    return GroupGap(
        variable=by,
        high_label=str(high_label),
        low_label=str(low_label),
        high_mean=float(high.mean()),
        low_mean=float(low.mean()),
        gap=float(high.mean() - low.mean()),
        effect_size=cohens_d(high, low),
    )


def rank_gaps(df: pd.DataFrame, value: str, variables: Iterable[str]) -> list[GroupGap]:
    """Ordena las variables binarias según cuánto separan a los estudiantes en ``value``."""
    gaps = [gap for var in variables if (gap := group_gap(df, var, value)) is not None]
    return sorted(gaps, key=lambda g: abs(g.gap), reverse=True)


def correlation(df: pd.DataFrame, x: str, y: str) -> float:
    """Correlación de Pearson entre dos variables numéricas."""
    if len(df) < 3 or df[x].nunique() < 2 or df[y].nunique() < 2:
        return math.nan
    return float(df[x].corr(df[y]))


def _safe_mean(series: pd.Series) -> float:
    return float(series.mean()) if not series.empty else math.nan
