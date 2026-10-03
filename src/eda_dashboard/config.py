"""Configuración central del dashboard.

Todo lo que un equipo podría querer ajustar sin tocar la lógica vive aquí:
esquema esperado de la base, etiquetas canónicas, paleta, umbrales de alerta
y la información del equipo que aparece en el encabezado y el pie del tablero.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Final

# --------------------------------------------------------------------------- #
# Esquema de la base de datos
# --------------------------------------------------------------------------- #


class Col(StrEnum):
    """Nombres canónicos de las columnas de Datos.xlsx."""

    ID = "ID_Estudiante"
    EDAD = "Edad"
    GRADO = "Grado"
    GENERO = "Genero"
    TIPO = "Tipo_Escuela"
    UBICACION = "Ubicacion_Escuela"
    PROMEDIO = "Promedio_Calificaciones"
    ASISTENCIA = "Asistencia"
    EXTRA = "Participacion_Extraescolares"
    INTERNET = "Acceso_Internet"


class Label:
    """Etiquetas canónicas de las variables categóricas."""

    SI: Final = "Sí"
    NO: Final = "No"
    PUBLICA: Final = "Pública"
    PRIVADA: Final = "Privada"
    URBANA: Final = "Urbana"
    RURAL: Final = "Rural"
    FEMENINO: Final = "Femenino"
    MASCULINO: Final = "Masculino"


#: Categorías válidas por columna, en el orden en que se muestran.
CATEGORIES: Final[dict[Col, tuple[str, ...]]] = {
    Col.GENERO: (Label.FEMENINO, Label.MASCULINO),
    Col.TIPO: (Label.PUBLICA, Label.PRIVADA),
    Col.UBICACION: (Label.URBANA, Label.RURAL),
    Col.EXTRA: (Label.SI, Label.NO),
    Col.INTERNET: (Label.SI, Label.NO),
}

#: Rango válido (inclusive) de cada variable numérica.
NUMERIC_RANGES: Final[dict[Col, tuple[float, float]]] = {
    Col.ID: (1, float("inf")),
    Col.EDAD: (4, 25),
    Col.GRADO: (0, 11),
    Col.PROMEDIO: (0, 10),
    Col.ASISTENCIA: (0, 100),
}

INTEGER_COLUMNS: Final = (Col.ID, Col.EDAD, Col.GRADO)

#: Nombres legibles para títulos, ejes y tooltips.
DISPLAY_NAMES: Final[dict[Col, str]] = {
    Col.ID: "ID del estudiante",
    Col.EDAD: "Edad",
    Col.GRADO: "Grado",
    Col.GENERO: "Género",
    Col.TIPO: "Tipo de escuela",
    Col.UBICACION: "Ubicación de la escuela",
    Col.PROMEDIO: "Promedio de calificaciones",
    Col.ASISTENCIA: "Asistencia (%)",
    Col.EXTRA: "Participa en extraescolares",
    Col.INTERNET: "Internet en casa",
}

# --------------------------------------------------------------------------- #
# Umbrales pedagógicos (ajustables por el equipo)
# --------------------------------------------------------------------------- #

#: Asistencia por debajo de este porcentaje se considera alerta de deserción.
ATTENDANCE_ALERT: Final = 75.0

#: Promedio mínimo aprobatorio en la escala 0–10.
PASSING_GRADE: Final = 6.0

# --------------------------------------------------------------------------- #
# Paleta (validada: contraste ≥ 3:1 y separación para daltonismo ΔE ≥ 24)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Palette:
    """Azul para los datos principales; naranja reservado al grupo en riesgo."""

    primary: str = "#2266B8"
    accent: str = "#D9661F"
    primary_soft: str = "#E8F0FA"
    accent_soft: str = "#FBEDE3"
    ink: str = "#14212E"
    ink_muted: str = "#56636F"
    grid: str = "#E3E8EE"
    surface: str = "#FFFFFF"
    background: str = "#F6F8FB"


PALETTE: Final = Palette()

#: Color por etiqueta: la categoría en desventaja siempre va en naranja,
#: así el ojo va al mismo lugar en todos los gráficos.
COLOR_BY_LABEL: Final[dict[str, str]] = {
    Label.SI: PALETTE.primary,
    Label.NO: PALETTE.accent,
    Label.PRIVADA: PALETTE.primary,
    Label.PUBLICA: PALETTE.accent,
    Label.URBANA: PALETTE.primary,
    Label.RURAL: PALETTE.accent,
    Label.FEMENINO: PALETTE.primary,
    Label.MASCULINO: PALETTE.accent,
}

# --------------------------------------------------------------------------- #
# Información del equipo (editar antes de publicar)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class TeamInfo:
    """Datos de autoría que se muestran en el encabezado y el pie del tablero."""

    title: str = "Lo que los datos dicen del aula que tenemos"
    subtitle: str = (
        "Análisis exploratorio de 300 estudiantes de instituciones educativas "
        "colombianas para tomar decisiones informadas en la escuela."
    )
    team_name: str = "[Nombre del equipo]"
    members: tuple[str, ...] = field(
        default=(
            "[Integrante 1] · [cargo] · [nivel que orienta]",
            "[Integrante 2] · [cargo] · [nivel que orienta]",
            "[Integrante 3] · [cargo] · [nivel que orienta]",
        )
    )
    teaching_level: str = "[Nivel educativo en el que enseñan]"
    audience: str = "rectores, coordinadores académicos y docentes"
    analysis_date: str = "Octubre de 2026"
    program: str = "Maestría en Educación y Transformación Digital"
    module: str = "La información en el sistema educativo"


TEAM: Final = TeamInfo()

# --------------------------------------------------------------------------- #
# Rutas
# --------------------------------------------------------------------------- #

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]

#: Si este archivo existe, el tablero lo carga sin necesidad de subirlo.
#: Es lo que permite que la URL pública muestre datos a cualquier visitante.
DEFAULT_DATA_PATH: Final = PROJECT_ROOT / "data" / "Datos.xlsx"
