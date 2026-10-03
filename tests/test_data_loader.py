from __future__ import annotations

import io

import pandas as pd
import pytest

from eda_dashboard.config import Col, Label
from eda_dashboard.data_loader import (
    DataValidationError,
    canonical_label,
    load_dataset,
    prepare_dataset,
)


def test_clean_base_loads_without_warnings(raw_sample: pd.DataFrame) -> None:
    result = prepare_dataset(raw_sample)
    assert len(result.data) == len(raw_sample)
    assert result.warnings == ()
    assert list(result.data.columns) == [c.value for c in Col]


def test_reads_excel_bytes(raw_sample: pd.DataFrame) -> None:
    buffer = io.BytesIO()
    raw_sample.to_excel(buffer, index=False)
    result = load_dataset(buffer.getvalue())
    assert len(result.data) == len(raw_sample)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("si", Label.SI), ("SÍ", Label.SI), (1.0, Label.SI), (True, Label.SI), (0, Label.NO),
     ("publica", Label.PUBLICA), (" Rural ", Label.RURAL), ("F", Label.FEMENINO), (None, None)],
)  # fmt: skip
def test_canonical_label(raw: object, expected: str | None) -> None:
    assert canonical_label(raw) == expected


def test_column_names_are_matched_ignoring_accents_and_case(raw_sample: pd.DataFrame) -> None:
    renamed = raw_sample.rename(columns={"Genero": "Género", "Asistencia": " ASISTENCIA "})
    result = prepare_dataset(renamed)
    assert Col.GENERO in result.data.columns
    assert Col.ASISTENCIA in result.data.columns


def test_missing_column_raises(raw_sample: pd.DataFrame) -> None:
    with pytest.raises(DataValidationError, match="Acceso_Internet"):
        prepare_dataset(raw_sample.drop(columns=["Acceso_Internet"]))


def test_unknown_category_raises(raw_sample: pd.DataFrame) -> None:
    raw_sample.loc[0, "Tipo_Escuela"] = "Mixta"
    with pytest.raises(DataValidationError, match="Mixta"):
        prepare_dataset(raw_sample)


def test_attendance_as_fraction_is_rescaled(raw_sample: pd.DataFrame) -> None:
    raw_sample["Asistencia"] = raw_sample["Asistencia"] / 100
    result = prepare_dataset(raw_sample)
    assert result.data[Col.ASISTENCIA].max() > 1
    assert any("0–1" in w for w in result.warnings)


def test_text_numbers_with_comma_decimal_are_parsed(raw_sample: pd.DataFrame) -> None:
    raw_sample["Promedio_Calificaciones"] = raw_sample["Promedio_Calificaciones"].map(
        lambda v: f"{v:.2f}".replace(".", ",")
    )
    result = prepare_dataset(raw_sample)
    assert result.data[Col.PROMEDIO].dtype == float
    assert result.warnings == ()


def test_invalid_rows_are_dropped_with_warning(raw_sample: pd.DataFrame) -> None:
    raw_sample.loc[0, "Promedio_Calificaciones"] = 15
    raw_sample.loc[1, "Edad"] = None
    result = prepare_dataset(raw_sample)
    assert len(result.data) == len(raw_sample) - 2
    assert len(result.warnings) == 2
