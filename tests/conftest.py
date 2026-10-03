from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from generate_sample_data import generate  # noqa: E402


@pytest.fixture
def raw_sample() -> pd.DataFrame:
    """Base cruda con la estructura de Datos.xlsx."""
    return generate(n=120, seed=7)


@pytest.fixture
def dataset(raw_sample: pd.DataFrame) -> pd.DataFrame:
    from eda_dashboard.data_loader import prepare_dataset

    return prepare_dataset(raw_sample).data
