"""Unit tests for estimation methods on synthetic data. No network."""

import pandas as pd
import pytest

from popest.constants import (
    BOD5,
    GAL_PER_MGAL,
    GRAMS_PER_LB,
    WASTEWATER_FLOW,
    WATER_USE_DOMESTIC_SELF_SUPPLIED,
    WATER_USE_PUBLIC_SUPPLY_TOTAL,
)
from popest.methods.wastewater import estimate as ww_estimate
from popest.methods.wastewater_chemistry import (
    estimate as chem_estimate,
    national_summary as chem_summary,
)
from popest.methods.water_budget import estimate as water_estimate
from popest.methods.water_budget import national_summary as water_summary


def _water_frame():
    # One normal county, one Puerto Rico county (excluded),
    # one state-level row (fips 000) that must be dropped.
    return pd.DataFrame({
        "fips": ["01001", "72001", "01000"],
        "state": ["AL", "PR", "AL"],
        "county": ["Autauga", "San Juan", "STATEWIDE"],
        "year": [2015, 2015, 2015],
        "ps_pop_thousands": [50.0, 10.0, 0.0],
        "ps_withdrawals_mgal_d": [6.0, 1.0, 0.0],
        "dom_pop_thousands": [2.0, 1.0, 0.0],
        "dom_withdrawals_mgal_d": [0.17, 0.085, 0.0],
        "dom_per_capita_gpd": [85.0, 85.0, 0.0],
        "total_pop_thousands": [52.0, 11.0, 0.0],
        "ps_dom_deliveries_mgal_d": [1.0, 0.2, 0.0],
    })


def test_water_budget_math():
    result = water_estimate(_water_frame())
    assert list(result["fips"]) == ["01001"]
    row = result.iloc[0]
    ps_pop = 6.0 * GAL_PER_MGAL / WATER_USE_PUBLIC_SUPPLY_TOTAL.central
    dom_pop = 0.17 * GAL_PER_MGAL / WATER_USE_DOMESTIC_SELF_SUPPLIED.central
    assert row["pop_central"] == pytest.approx(ps_pop + dom_pop)
    # low_pop uses high per-capita use (fewer people per gallon)
    low = (6.0 * GAL_PER_MGAL / WATER_USE_PUBLIC_SUPPLY_TOTAL.high
           + 0.17 * GAL_PER_MGAL / WATER_USE_DOMESTIC_SELF_SUPPLIED.high)
    assert row["pop_low_pop"] == pytest.approx(low)
    assert row["pop_central"] > row["pop_low_pop"]
    assert row["pop_central"] < row["pop_high_pop"]


def test_water_budget_summary_sums():
    result = water_estimate(_water_frame())
    s = water_summary(result)
    assert s["counties"] == 1
    assert s["central"] == pytest.approx(result["pop_central"].sum())
    assert s["usgs_official"] == pytest.approx((50.0 + 2.0) * 1000.0)


def test_wastewater_design_flow_math():
    flows = pd.DataFrame({
        "fips": ["01001", "01001", "06037"],
        "design_flow_mgd": [2.0, 1.0, 100.0],
    })
    result = ww_estimate(flows)
    by_fips = result.set_index("fips")
    assert by_fips.loc["01001", "pop_ww_central"] == pytest.approx(
        3.0 * 1e6 / WASTEWATER_FLOW.central)
    assert by_fips.loc["06037", "pop_ww_central"] == pytest.approx(
        100.0 * 1e6 / WASTEWATER_FLOW.central)
    # low uses the high per-capita constant
    assert by_fips.loc["06037", "pop_ww_low"] == pytest.approx(
        100.0 * 1e6 / WASTEWATER_FLOW.high)


def _facility_loads():
    """Pivoted per-facility loads, the shape dmr.facility_loads() emits."""
    return pd.DataFrame({
        "EXTERNAL_PERMIT_NMBR": ["P1", "P2", "P3", "P4"],
        "BOD5_lb_d": [1500.0, 500.0, 999999.0, None],
        "TSS_lb_d": [None, None, None, 300.0],
    })


def _county_map():
    return pd.DataFrame({
        "EXTERNAL_PERMIT_NMBR": ["P1", "P2", "P3", "P4"],
        "fips": ["01001", "01001", "01003", "01003"],
    })


def test_chemistry_excludes_industrial_and_groups_county():
    muni = {"P1", "P2"}  # P3, P4 industrial
    result = chem_estimate(_facility_loads(), _county_map(), muni)
    assert list(result["fips"]) == ["01001"]
    # P1 mean of 1000, 2000 = 1500; P2 = 500; county total 2000 lb/d
    assert result.iloc[0]["bod_lb_d"] == pytest.approx(2000.0)
    assert result.iloc[0]["n_facilities"] == 2
    assert result.iloc[0]["pop_chem_central"] == pytest.approx(
        2000.0 * GRAMS_PER_LB / BOD5.central)


def test_chemistry_national_summary_parameters():
    muni = {"P1", "P2", "P3"}
    loads = _facility_loads()
    result = chem_estimate(loads, _county_map(), muni)
    s = chem_summary(result, loads, muni)
    # county-level BOD covers municipal P1+P2 (01001) and P3 (01003)
    assert s["bod_lb_d"] == pytest.approx(2000.0 + 999999.0)
    assert s["bod_pop"] == pytest.approx(
        (2000.0 + 999999.0) * GRAMS_PER_LB / BOD5.central)
    # parameter loop: BOD national includes P3 too (1500+500+999999)
    assert s["BOD5_lb_d"] == pytest.approx(1500 + 500 + 999999)
    assert s["BOD5_pop"] == pytest.approx(s["BOD5_lb_d"] * GRAMS_PER_LB / BOD5.central)
    # TSS only P4 (not municipal here) -> absent
    assert "TSS_pop" not in s


def test_chemistry_empty_inputs():
    empty = pd.DataFrame(columns=["EXTERNAL_PERMIT_NMBR", "BOD5_lb_d"])
    result = chem_estimate(empty, _county_map(), set())
    assert result.empty
