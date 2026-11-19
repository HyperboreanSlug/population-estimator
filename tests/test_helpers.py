"""Unit tests for helpers: DMR processing, geo, constants, sources."""

import zipfile

import pandas as pd
import pytest

from popest import dmr
from popest.constants import (
    BOD5,
    GAL_PER_MGAL,
    GRAMS_PER_LB,
    MSW_GENERATION,
    PerCapitaConstant,
)
from popest.geo import STATE_ABBREV_TO_FIPS, is_valid_county_fips
from popest.sources import CORE_SOURCES, EXTENDED_SOURCES


# --- geo ------------------------------------------------------------------

def test_valid_county_fips():
    assert is_valid_county_fips("01001")
    assert is_valid_county_fips("11001")
    assert not is_valid_county_fips("72001")   # Puerto Rico excluded
    assert not is_valid_county_fips("01000")   # state total row
    assert not is_valid_county_fips("1001")    # not 5 digits
    assert not is_valid_county_fips("99001")   # not a state


def test_state_map_covers_states_dc_and_pr():
    # keys are state abbreviations; 50 states + DC + PR
    assert len(STATE_ABBREV_TO_FIPS) == 52
    assert STATE_ABBREV_TO_FIPS["DC"] == "11"
    assert STATE_ABBREV_TO_FIPS["CA"] == "06"
    assert STATE_ABBREV_TO_FIPS["PR"] == "72"


# --- constants ------------------------------------------------------------

def test_all_constants_ordered():
    import popest.constants as c

    for name in dir(c):
        value = getattr(c, name)
        if isinstance(value, PerCapitaConstant):
            assert value.low <= value.central <= value.high, name
            assert value.unit, name
            assert value.source, name


def test_conversion_factors():
    assert GRAMS_PER_LB == pytest.approx(453.592)
    assert GAL_PER_MGAL == 1_000_000
    assert 55 <= BOD5.low <= 90 <= BOD5.high
    assert 4.0 <= MSW_GENERATION.low <= 5.5 <= MSW_GENERATION.high


# --- sources manifest -----------------------------------------------------

def test_core_manifest_has_required_sources():
    keys = {k for k, *_ in CORE_SOURCES}
    for required in ("usgs_water_2015", "npdes_part1", "npdes_dmr_fy2024",
                     "irs_soi_2022", "bls_employed", "eia_total_energy"):
        assert required in keys


def test_manifest_keys_and_paths_unique():
    for manifest in (CORE_SOURCES, EXTENDED_SOURCES):
        keys = [k for k, *_ in manifest]
        paths = [p for _, _, p, _, _ in manifest]
        assert len(keys) == len(set(keys))
        assert len(paths) == len(set(paths))


# --- dmr ------------------------------------------------------------------

def _write_dmr_zip(tmp_path, rows):
    csv = (
        "EXTERNAL_PERMIT_NMBR,PARAMETER_CODE,PARAMETER_DESC,"
        "DMR_VALUE_NMBR,DMR_UNIT_CODE,DMR_UNIT_DESC,"
        "VALUE_TYPE_CODE,MONITORING_PERIOD_END_DATE\n"
        + "\n".join(rows) + "\n"
    )
    path = tmp_path / "dmr.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("NPDES_DMRS_FY2024.csv", csv)
    return path


def test_filter_dmr_finds_targets(tmp_path, monkeypatch):
    monkeypatch.setattr(dmr, "DATA", tmp_path)
    rows = [
        "GA1,00310,BOD5,100,LD,lb/d,AVG,2024-06-30",
        "GA1,00670,Total N,50,LD,lb/d,AVG,2024-06-30",
        "GA1,00900,Other,7,XX,mg/L,AVG,2024-06-30",
    ]
    zpath = _write_dmr_zip(tmp_path, rows)
    df = dmr.filter_dmr(zpath)
    assert len(df) == 2
    assert set(df["PARAMETER_CODE"]) == {"00310", "00670"}
    # cached CSV was written and reloads
    assert (tmp_path / "dmr_filtered_fy2024.csv").exists()
    df2 = dmr.filter_dmr(zpath)
    assert len(df2) == 2


def test_facility_loads_unit_conversion(tmp_path, monkeypatch):
    monkeypatch.setattr(dmr, "DATA", tmp_path)
    rows = [
        # 365,000 lb/yr == 1000 lb/d
        "P1,00310,BOD5,365000,LC,lb/yr,AVG,2024-12-31",
        "P1,00310,BOD5,730,LC,lb/wk,AVG,2024-06-30",  # 104.3 lb/d
        "P2,00310,BOD5,100,LD,lb/d,AVG,2024-06-30",
        "P2,00530,TSS,45.3592,K3,kg/d,AVG,2024-06-30",  # 100 lb/d
    ]
    zpath = _write_dmr_zip(tmp_path, rows)
    df = dmr.filter_dmr(zpath)
    loads = dmr.facility_loads(df)
    p1 = loads[loads["EXTERNAL_PERMIT_NMBR"] == "P1"].iloc[0]
    assert p1["BOD5_lb_d"] == pytest.approx((1000 + 104.2857) / 2, rel=1e-3)
    p2 = loads[loads["EXTERNAL_PERMIT_NMBR"] == "P2"].iloc[0]
    assert p2["BOD5_lb_d"] == pytest.approx(100.0)
    assert p2["TSS_lb_d"] == pytest.approx(45.3592 * 2.20462)


def test_facility_county_map(tmp_path):
    fac_csv = (
        "NPDES_ID,COUNTY_CODE,STATE_CODE\n"
        "GA1,001,GA\n"
        "GA2,003,GA\n"
        "XX1,999,ZZ\n"
        "GA3,001,GA\n"
    )
    path = tmp_path / "npdes.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("ICIS_FACILITIES.csv", fac_csv)
    cmap = dmr.facility_county_map(path)
    got = dict(zip(cmap["EXTERNAL_PERMIT_NMBR"], cmap["fips"]))
    assert got["GA1"] == "13001"
    assert got["GA2"] == "13003"
    assert "XX1" not in got          # invalid state dropped
    assert cmap["EXTERNAL_PERMIT_NMBR"].is_unique


def test_municipal_permit_ids(tmp_path):
    sics_csv = "NPDES_ID,SIC_CODE\nGA1,4952\nGA2,4953\nGA3, 4952 \n"
    path = tmp_path / "npdes.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("NPDES_SICS.csv", sics_csv)
    ids = dmr.municipal_permit_ids(path)
    assert ids == {"GA1", "GA3"}
