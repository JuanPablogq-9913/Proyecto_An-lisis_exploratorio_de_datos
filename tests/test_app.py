"""Pruebas de humo de la interfaz con el ejecutor de Streamlit."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")
DATA = Path(__file__).resolve().parents[1] / "data" / "Datos.xlsx"

pytestmark = pytest.mark.skipif(not DATA.exists(), reason="Requiere data/Datos.xlsx")


def _run(**filters: list[str]) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.run()
    for key, value in filters.items():
        app.multiselect(key=key).set_value(value)
    app.run()
    return app


def test_app_renders_without_errors() -> None:
    app = _run()
    assert not app.exception
    assert not app.error


@pytest.mark.parametrize(
    "filters",
    [{"f_Tipo_Escuela": ["Privada"]}, {"f_Ubicacion_Escuela": ["Rural"]}, {"f_Genero": ["Femenino"]}],
)
def test_app_survives_single_group_filters(filters: dict[str, list[str]]) -> None:
    app = _run(**filters)
    assert not app.exception


def test_every_third_variable_option_renders() -> None:
    app = _run()
    for option in app.radio(key="third_variable").options:
        app.radio(key="third_variable").set_value(option).run()
        assert not app.exception
