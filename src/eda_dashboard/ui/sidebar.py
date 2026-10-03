"""Panel lateral: carga del archivo y filtros interactivos."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ..analysis import FilterSelection
from ..config import CATEGORIES, Col
from ..formatting import fmt_int

UPLOAD_KEY = "excel_upload"


def file_uploader() -> bytes | None:
    """Permite subir un Excel distinto al incluido por defecto."""
    st.sidebar.header("Datos")
    uploaded = st.sidebar.file_uploader(
        "Cargar base de datos (.xlsx)",
        type=["xlsx"],
        key=UPLOAD_KEY,
        help="Debe tener las 10 columnas de Datos.xlsx. Si no sube nada, se usa la base incluida.",
    )
    return uploaded.getvalue() if uploaded is not None else None


def _multiselect(label: str, column: Col) -> tuple[str, ...]:
    options = CATEGORIES[column]
    chosen = st.sidebar.multiselect(label, options=options, default=list(options), key=f"f_{column}")
    # Dejar un filtro vacío se interpreta como "todos", no como "ninguno".
    return tuple(chosen) or options


def filters(df: pd.DataFrame) -> FilterSelection:
    """Dibuja los filtros y devuelve la selección activa."""
    st.sidebar.header("Filtros")
    st.sidebar.caption("Afectan a todos los gráficos y textos, salvo la sección de decisiones.")

    ubicacion = _multiselect("Ubicación de la escuela", Col.UBICACION)
    tipo = _multiselect("Tipo de escuela", Col.TIPO)
    genero = _multiselect("Género", Col.GENERO)

    low, high = int(df[Col.GRADO].min()), int(df[Col.GRADO].max())
    grados = (
        st.sidebar.slider("Grados", min_value=low, max_value=high, value=(low, high), key="f_grados")
        if low < high
        else (low, high)
    )
    return FilterSelection(ubicacion=ubicacion, tipo=tipo, genero=genero, grados=tuple(grados))


def filter_summary(total: int, shown: int) -> None:
    st.sidebar.divider()
    st.sidebar.metric("Estudiantes en la vista", fmt_int(shown), delta=None)
    if shown < total:
        st.sidebar.caption(f"Filtrando {fmt_int(total - shown)} de {fmt_int(total)} estudiantes.")
