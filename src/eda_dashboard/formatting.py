"""Formato numérico en convención colombiana (coma decimal, espacio antes de %)."""

from __future__ import annotations

import math

NOT_AVAILABLE = "—"


def fmt_number(value: float, decimals: int = 2) -> str:
    """``7.0912 → '7,09'``; usa punto para miles: ``1234.5 → '1.234,50'``."""
    if value is None or math.isnan(value):
        return NOT_AVAILABLE
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_pct(value: float, decimals: int = 0) -> str:
    """``68.0 → '68 %'``."""
    if value is None or math.isnan(value):
        return NOT_AVAILABLE
    return f"{fmt_number(value, decimals)} %"


def fmt_int(value: int) -> str:
    return fmt_number(value, 0)


def fmt_points(value: float, decimals: int = 2) -> str:
    """Diferencia en puntos de la escala 0–10: ``1.63 → '1,63 puntos'``."""
    if value is None or math.isnan(value):
        return NOT_AVAILABLE
    unit = "punto" if math.isclose(abs(value), 1.0) else "puntos"
    return f"{fmt_number(value, decimals)} {unit}"
