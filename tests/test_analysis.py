from __future__ import annotations

import math

import pandas as pd
import pytest

from eda_dashboard.analysis import (
    FilterSelection,
    apply_filters,
    cohens_d,
    compute_kpis,
    group_gap,
    mean_gap,
    proportion_by,
    rank_gaps,
    share,
)
from eda_dashboard.config import Col, Label
from eda_dashboard.findings import build_findings
from eda_dashboard.formatting import fmt_number, fmt_pct


def test_kpis_match_manual_calculation(dataset: pd.DataFrame) -> None:
    kpis = compute_kpis(dataset)
    assert kpis.total == len(dataset)
    assert kpis.promedio == pytest.approx(dataset[Col.PROMEDIO].mean())
    assert kpis.sin_internet == (dataset[Col.INTERNET] == Label.NO).sum()
    assert kpis.pct_internet + kpis.sin_internet / kpis.total * 100 == pytest.approx(100)


def test_everything_filter_keeps_all_rows(dataset: pd.DataFrame) -> None:
    selection = FilterSelection.everything(dataset)
    assert selection.is_everything(dataset)
    assert len(apply_filters(dataset, selection)) == len(dataset)


def test_filter_by_location(dataset: pd.DataFrame) -> None:
    selection = FilterSelection.everything(dataset)
    rural = FilterSelection(
        ubicacion=(Label.RURAL,), tipo=selection.tipo, genero=selection.genero, grados=selection.grados
    )
    filtered = apply_filters(dataset, rural)
    assert set(filtered[Col.UBICACION]) == {Label.RURAL}


def test_proportions_sum_to_100_within_each_group(dataset: pd.DataFrame) -> None:
    table = proportion_by(dataset, Col.TIPO, Col.INTERNET)
    sums = table.groupby(Col.TIPO, observed=True)["pct"].sum()
    assert sums.to_numpy() == pytest.approx([100, 100])


def test_gap_is_nan_when_a_group_is_missing(dataset: pd.DataFrame) -> None:
    only_public = dataset.loc[dataset[Col.TIPO] == Label.PUBLICA]
    assert math.isnan(mean_gap(only_public, Col.TIPO, Col.PROMEDIO, Label.PRIVADA, Label.PUBLICA))
    assert group_gap(only_public, Col.TIPO, Col.PROMEDIO) is None


def test_cohens_d_known_value() -> None:
    a = pd.Series([2.0, 4.0, 6.0])
    b = pd.Series([1.0, 3.0, 5.0])
    assert cohens_d(a, b) == pytest.approx(0.5)


def test_ranking_is_sorted_by_gap(dataset: pd.DataFrame) -> None:
    ranking = rank_gaps(dataset, Col.PROMEDIO, [Col.TIPO, Col.GENERO, Col.UBICACION])
    gaps = [abs(g.gap) for g in ranking]
    assert gaps == sorted(gaps, reverse=True)


def test_share_of_empty_frame_is_nan(dataset: pd.DataFrame) -> None:
    assert math.isnan(share(dataset.iloc[0:0], Col.TIPO, Label.PUBLICA))


def test_findings_have_all_five_components(dataset: pd.DataFrame) -> None:
    findings = build_findings(dataset)
    assert 3 <= len(findings) <= 5
    for finding in findings:
        assert all([finding.hallazgo, finding.decision, finding.poblacion, finding.indicador, finding.riesgo])


def test_spanish_number_format() -> None:
    assert fmt_number(7.0912) == "7,09"
    assert fmt_number(1234.5, 1) == "1.234,5"
    assert fmt_pct(68.0) == "68 %"
    assert fmt_pct(math.nan) == "—"
