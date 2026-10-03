"""Punto de entrada del tablero.

Ejecutar con:
    streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Diseño "src layout": se agrega src/ al path para que el tablero funcione tanto
# en local como en Streamlit Community Cloud sin instalar el paquete.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from eda_dashboard.analysis import apply_filters  # noqa: E402
from eda_dashboard.config import DEFAULT_DATA_PATH, TEAM  # noqa: E402
from eda_dashboard.data_loader import DataValidationError, LoadResult, load_dataset  # noqa: E402
from eda_dashboard.ui import components as ui  # noqa: E402
from eda_dashboard.ui import sidebar  # noqa: E402
from eda_dashboard.ui.sections import SECTIONS, DashboardData  # noqa: E402
from eda_dashboard.ui.styles import CSS  # noqa: E402


@st.cache_data(show_spinner="Leyendo la base de datos…")
def _load_from_bytes(content: bytes) -> LoadResult:
    return load_dataset(content)


@st.cache_data(show_spinner="Leyendo la base de datos…")
def _load_from_path(path: str, modified: float) -> LoadResult:  # noqa: ARG001 (llave de caché)
    return load_dataset(path)


def _resolve_dataset() -> LoadResult | None:
    """Prioriza el archivo subido; si no hay, usa ``data/Datos.xlsx``."""
    uploaded = sidebar.file_uploader()
    if uploaded is not None:
        return _load_from_bytes(uploaded)
    if DEFAULT_DATA_PATH.exists():
        return _load_from_path(str(DEFAULT_DATA_PATH), DEFAULT_DATA_PATH.stat().st_mtime)
    return None


def _show_welcome() -> None:
    st.info(
        "Para empezar, cargue el archivo **Datos.xlsx** desde el panel lateral, "
        "o guárdelo en `data/Datos.xlsx` para que el tablero lo lea automáticamente."
    )


def main() -> None:
    st.set_page_config(page_title=TEAM.title, page_icon="📊", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)

    try:
        result = _resolve_dataset()
    except DataValidationError as error:
        st.error(f"No fue posible usar el archivo: {error}")
        st.stop()

    if result is None:
        ui.hero(TEAM, total=0)
        _show_welcome()
        st.stop()

    for message in result.warnings:
        st.sidebar.warning(message)

    full = result.data
    selection = sidebar.filters(full)
    view = apply_filters(full, selection)
    sidebar.filter_summary(total=len(full), shown=len(view))

    ui.hero(TEAM, total=len(full))
    if view.empty:
        st.warning("Ningún estudiante cumple los filtros seleccionados. Amplíe la selección.")
        st.stop()

    data = DashboardData.build(full=full, view=view)
    for render_section in SECTIONS:
        render_section(data)


if __name__ == "__main__":
    main()
