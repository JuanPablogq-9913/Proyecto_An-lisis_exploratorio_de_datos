"""Genera una base SINTÉTICA con la estructura de Datos.xlsx.

Sirve solo para desarrollar y probar el tablero mientras no se tiene la base
oficial del curso. Sus cifras imitan aproximadamente las de la guía, pero NO
deben usarse para el informe.

Uso:
    python scripts/generate_sample_data.py [ruta_salida.xlsx]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

N_STUDENTS = 300
SEED = 2026


def generate(n: int = N_STUDENTS, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    grado = rng.integers(1, 12, n)
    edad = np.clip(grado + 5 + rng.integers(0, 3, n), 6, 18)
    tipo = np.where(rng.random(n) < 0.67, "Pública", "Privada")
    ubicacion = np.where(rng.random(n) < 0.24, "Rural", "Urbana")
    internet = np.where((tipo == "Privada") | (rng.random(n) < 0.52), "Sí", "No")
    extra = np.where(rng.random(n) < 0.45, "Sí", "No")
    genero = np.where(rng.random(n) < 0.5, "Femenino", "Masculino")

    asistencia = np.clip(rng.normal(87, 7, n) - (ubicacion == "Rural") * 3, 60, 100)
    promedio = (
        6.3
        + (tipo == "Privada") * 1.4
        + (internet == "Sí") * 0.5
        + (extra == "Sí") * 0.2
        + (asistencia - 87) * 0.03
        + rng.normal(0, 0.8, n)
    )
    return pd.DataFrame(
        {
            "ID_Estudiante": np.arange(1, n + 1),
            "Edad": edad,
            "Grado": grado,
            "Genero": genero,
            "Tipo_Escuela": tipo,
            "Ubicacion_Escuela": ubicacion,
            "Promedio_Calificaciones": np.clip(promedio, 0, 10).round(2),
            "Asistencia": asistencia.round(1),
            "Participacion_Extraescolares": extra,
            "Acceso_Internet": internet,
        }
    )


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/datos_sinteticos.xlsx")
    output.parent.mkdir(parents=True, exist_ok=True)
    generate().to_excel(output, index=False)
    print(f"Base sintética guardada en {output}")


if __name__ == "__main__":
    main()
