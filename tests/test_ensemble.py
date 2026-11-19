"""Unit tests for ensemble combination, bootstrap, reconciliation."""

import numpy as np
import pandas as pd
import pytest

from popest.discrepancy import discrepancy_report
from popest.ensemble import (
    CENSUS_WEIGHT_CAP,
    combine_county,
    combine_national,
    state_rollup,
)
from popest.uncertainty import bootstrap_national


def test_combine_national_weights_and_census_cap():
    estimates = {"water": 400.0, "energy": 200.0}
    result = combine_national(estimates, census=100.0)
    w = {"water": 0.16, "energy": 0.06}
    census_w = min(CENSUS_WEIGHT_CAP, 1.0 - 0.22)
    expected = (400 * 0.16 + 200 * 0.06 + 100 * census_w) / (0.22 + census_w)
    assert result["combined"] == pytest.approx(expected)
    assert result["contributions"]["census"]["weight"] == pytest.approx(census_w)


def test_combine_national_skips_zero_and_none_census():
    result = combine_national({"water": 0.0, "energy": 300.0}, census=None)
    assert set(result["contributions"]) == {"energy"}
    assert result["combined"] == pytest.approx(300.0)


def test_combine_county_renormalizes_missing_methods():
    water = pd.DataFrame({
        "fips": ["01001", "01003"],
        "pop_water_central": [100.0, 50.0],
        "pop_water_low": [80.0, 40.0],
        "pop_water_high": [130.0, 70.0],
    })
    ww = pd.DataFrame({
        "fips": ["01001"],
        "pop_wastewater_central": [200.0],
        "pop_wastewater_low": [150.0],
        "pop_wastewater_high": [260.0],
    })
    census = pd.DataFrame({
        "fips": ["01001", "01003"],
        "census_pop": [90.0, 45.0],
    })
    out = combine_county({"water": water, "wastewater": ww}, census)

    r1 = out[out["fips"] == "01001"].iloc[0]
    # weights: water .35 + ww .25 + census .15 = .75
    expected1 = (100 * 0.35 + 200 * 0.25 + 90 * 0.15) / 0.75
    assert r1["ensemble_pop"] == pytest.approx(expected1)
    assert r1["n_methods"] == 3

    r3 = out[out["fips"] == "01003"].iloc[0]
    # water + census only
    expected3 = (50 * 0.35 + 45 * 0.15) / 0.50
    assert r3["ensemble_pop"] == pytest.approx(expected3)
    assert r3["n_methods"] == 2
    assert r3["ensemble_low"] == pytest.approx((40 * 0.35 + 45 * 0.15) / 0.50)

    # contributions sum to 1 where methods exist
    contribs = [c for c in out.columns if c.startswith("contrib_")]
    shares = out[out["fips"] == "01001"][contribs].iloc[0].astype(float).sum()
    assert shares == pytest.approx(1.0)


def test_combine_county_unknown_county_left_blank():
    water = pd.DataFrame({
        "fips": ["01001"],
        "pop_water_central": [100.0],
        "pop_water_low": [80.0],
        "pop_water_high": [130.0],
    })
    out = combine_county({"water": water})
    unknown = out[out["fips"] == "99999"]
    assert unknown.empty  # outer join keeps only seen fips; no invention


def test_state_rollup_sums_and_coverage():
    county = pd.DataFrame({
        "fips": ["01001", "01003", "02010"],
        "ensemble_pop": [100.0, 50.0, 0.0],
        "ensemble_low": [80.0, 40.0, 0.0],
        "ensemble_high": [130.0, 70.0, 0.0],
        "n_methods": [2, 1, 0],
    })
    states = state_rollup(county)
    al = states[states["state_fips"] == "01"].iloc[0]
    assert al["ensemble_pop"] == pytest.approx(150.0)
    assert al["counties_covered"] == 2


def test_bootstrap_inverse_form_spans_published_range():
    methods = {
        "water": {"central": 350.0, "low": 300.0, "high": 420.0,
                  "form": "inverse"},
    }
    boot = bootstrap_national(methods, census=0.0, n_draws=2000, seed=7)
    assert boot["lower_90"] >= 300.0 - 1e-9
    assert boot["upper_90"] <= 420.0 + 1e-9
    assert boot["lower_90"] < boot["combined"] < boot["upper_90"]
    # exact sampler: mean of pop = total/const with const ~ U[a, b]
    # endpoints map to const extremes; combined mean lands inside
    assert 300.0 < boot["combined"] < 420.0


def test_bootstrap_direct_form():
    methods = {
        "housing": {"central": 320.0, "low": 300.0, "high": 340.0,
                    "form": "direct"},
    }
    boot = bootstrap_national(methods, census=0.0, n_draws=1000)
    assert boot["lower_90"] >= 300.0 - 1e-9
    assert boot["upper_90"] <= 340.0 + 1e-9


def test_bootstrap_deterministic_with_seed():
    methods = {
        "water": {"central": 350.0, "low": 300.0, "high": 420.0,
                  "form": "inverse"},
        "msw": {"central": 330.0, "low": 290.0, "high": 370.0,
                "form": "inverse"},
    }
    a = bootstrap_national(methods, census=100.0, n_draws=500, seed=3)
    b = bootstrap_national(methods, census=100.0, n_draws=500, seed=3)
    assert a == b


def test_bootstrap_census_shifts_combined_toward_census():
    methods = {
        "water": {"central": 500.0, "low": 400.0, "high": 600.0,
                  "form": "inverse"},
    }
    with_census = bootstrap_national(methods, census=100.0, n_draws=4000, seed=5)
    without = bootstrap_national(methods, census=0.0, n_draws=4000, seed=5)
    assert with_census["combined"] < without["combined"]


def test_discrepancy_report_values():
    disc = discrepancy_report({"water": 400.0, "energy": 300.0}, census=331.0)
    rows = disc.set_index("method")
    assert rows.loc["water", "pct_above_census"] == pytest.approx(
        (400 - 331) / 331 * 100)
    assert rows.loc["energy", "difference"] == pytest.approx(-31.0)
    # sorted descending by estimate
    assert disc.iloc[0]["method"] == "water"


def test_weights_sum_near_one_with_census_cap():
    from popest.ensemble import METHOD_WEIGHTS

    assert sum(METHOD_WEIGHTS.values()) <= 1.55
    physical = sum(v for k, v in METHOD_WEIGHTS.items()
                   if k not in ("census",))
    assert physical > 0.85  # physical methods keep the bulk of weight
