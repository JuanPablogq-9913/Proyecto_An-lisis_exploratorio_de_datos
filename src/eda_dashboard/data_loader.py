"""Lectura, validación y normalización de la base de datos en Excel.

El objetivo es que el resto de la aplicación trabaje siempre con un DataFrame
limpio y predecible: nombres de columna canónicos, tipos correctos y etiquetas
categóricas unificadas (p. ej. "Si", "sí", "SI" o 1 terminan siendo "Sí").

Los problemas se clasifican en dos niveles:

* ``DataValidationError``: la base no se puede analizar (faltan columnas,
  aparecen categorías desconocidas, no quedan filas válidas).
* Advertencias: la base se puede analizar, pero se hizo algún ajuste que el
  usuario debe conocer (filas descartadas, escala de asistencia convertida...).
"""

from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from .config import CATEGORIES, INTEGER_COLUMNS, NUMERIC_RANGES, Col, Label

ExcelSource = str | Path | bytes | BinaryIO


class DataValidationError(ValueError):
    """La base de datos no cumple el esquema mínimo para ser analizada."""


@dataclass(frozen=True)
class LoadResult:
    """Base lista para analizar más las advertencias generadas al prepararla."""

    data: pd.DataFrame
    warnings: tuple[str, ...]


# --------------------------------------------------------------------------- #
# API pública
# --------------------------------------------------------------------------- #


def load_dataset(source: ExcelSource, sheet_name: str | int = 0) -> LoadResult:
    """Lee un archivo Excel y devuelve la base validada y normalizada."""
    if isinstance(source, bytes):
        source = io.BytesIO(source)
    try:
        raw = pd.read_excel(source, sheet_name=sheet_name, engine="openpyxl")
    except Exception as exc:  # openpyxl lanza excepciones de varios tipos
        raise DataValidationError(f"No fue posible leer el archivo Excel: {exc}") from exc
    return prepare_dataset(raw)


def prepare_dataset(raw: pd.DataFrame) -> LoadResult:
    """Valida y normaliza un DataFrame crudo con la estructura de Datos.xlsx."""
    warnings: list[str] = []

    df = _standardize_column_names(raw)
    _ensure_required_columns(df)

    extra_columns = [c for c in df.columns if c not in set(Col)]
    if extra_columns:
        warnings.append(f"Se ignoraron columnas no esperadas: {', '.join(map(str, extra_columns))}.")
    df = df[[c.value for c in Col]].copy()

    df = _coerce_numeric_columns(df, warnings)
    df = _rescale_attendance(df, warnings)
    df = _normalize_categorical_columns(df)
    df = _drop_incomplete_rows(df, warnings)
    df = _drop_out_of_range_rows(df, warnings)

    if df.empty:
        raise DataValidationError("Después de la validación no quedó ningún registro válido.")

    for col in INTEGER_COLUMNS:
        df[col] = df[col].round().astype(int)

    duplicated = int(df[Col.ID].duplicated().sum())
    if duplicated:
        warnings.append(f"Hay {duplicated} identificadores de estudiante repetidos.")

    return LoadResult(data=df.reset_index(drop=True), warnings=tuple(warnings))


# --------------------------------------------------------------------------- #
# Normalización de texto
# --------------------------------------------------------------------------- #


def normalize_key(value: object) -> str:
    """Convierte un texto a una llave comparable: sin tildes, minúsculas, solo alfanuméricos."""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", text.lower())


_COLUMN_LOOKUP: dict[str, str] = {normalize_key(col.value): col.value for col in Col}

_LABEL_ALIASES: dict[str, str] = {
    "si": Label.SI, "s": Label.SI, "yes": Label.SI, "true": Label.SI, "1": Label.SI,
    "no": Label.NO, "n": Label.NO, "false": Label.NO, "0": Label.NO,
    "publica": Label.PUBLICA, "oficial": Label.PUBLICA,
    "privada": Label.PRIVADA, "nooficial": Label.PRIVADA,
    "urbana": Label.URBANA, "urbano": Label.URBANA,
    "rural": Label.RURAL,
    "femenino": Label.FEMENINO, "f": Label.FEMENINO, "mujer": Label.FEMENINO,
    "masculino": Label.MASCULINO, "m": Label.MASCULINO, "hombre": Label.MASCULINO,
}  # fmt: skip


def canonical_label(value: object) -> str | None:
    """Traduce una etiqueta cruda a su forma canónica (``None`` si está vacía)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    key = normalize_key(value)
    return _LABEL_ALIASES.get(key, str(value).strip())


# --------------------------------------------------------------------------- #
# Pasos de preparación
# --------------------------------------------------------------------------- #


def _standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {col: _COLUMN_LOOKUP.get(normalize_key(col), col) for col in df.columns}
    return df.rename(columns=renamed)


def _ensure_required_columns(df: pd.DataFrame) -> None:
    missing = [col.value for col in Col if col.value not in df.columns]
    if missing:
        raise DataValidationError("Faltan columnas obligatorias en el archivo: " + ", ".join(missing) + ".")


def _coerce_numeric_columns(df: pd.DataFrame, warnings: list[str]) -> pd.DataFrame:
    for col in NUMERIC_RANGES:
        original = df[col]
        if pd.api.types.is_numeric_dtype(original):
            converted = pd.to_numeric(original, errors="coerce")
        else:
            cleaned = (
                original.astype("string")
                .str.strip()
                .str.replace("%", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            converted = pd.to_numeric(cleaned, errors="coerce")
        unparseable = int((converted.isna() & original.notna()).sum())
        if unparseable:
            warnings.append(f"{unparseable} valores no numéricos en «{col}» se trataron como vacíos.")
        df[col] = converted.astype(float)
    return df


def _rescale_attendance(df: pd.DataFrame, warnings: list[str]) -> pd.DataFrame:
    """Si la asistencia viene como proporción (0–1), la lleva a porcentaje (0–100)."""
    attendance = df[Col.ASISTENCIA].dropna()
    if not attendance.empty and attendance.max() <= 1.0:
        df[Col.ASISTENCIA] = df[Col.ASISTENCIA] * 100
        warnings.append("La asistencia venía en escala 0–1 y se convirtió a porcentaje (0–100).")
    return df


def _normalize_categorical_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col, allowed in CATEGORIES.items():
        mapped = df[col].map(canonical_label)
        invalid = sorted(
            {str(raw) for raw, label in zip(df[col], mapped, strict=True)
             if label is not None and label not in allowed}
        )  # fmt: skip
        if invalid:
            raise DataValidationError(
                f"La columna «{col}» tiene valores no reconocidos: {', '.join(invalid)}. "
                f"Valores esperados: {', '.join(allowed)}."
            )
        df[col] = pd.Categorical(mapped, categories=list(allowed))
    return df


def _drop_incomplete_rows(df: pd.DataFrame, warnings: list[str]) -> pd.DataFrame:
    incomplete = df.isna().any(axis=1)
    if incomplete.any():
        warnings.append(f"Se descartaron {int(incomplete.sum())} filas con valores faltantes.")
    return df.loc[~incomplete]


def _drop_out_of_range_rows(df: pd.DataFrame, warnings: list[str]) -> pd.DataFrame:
    valid = pd.Series(True, index=df.index)
    for col, (low, high) in NUMERIC_RANGES.items():
        in_range = df[col].between(low, high)
        out = int((~in_range).sum())
        if out:
            warnings.append(f"Se descartaron {out} filas con «{col}» fuera del rango {low:g}–{high:g}.")
        valid &= in_range
    return df.loc[valid]
