"""Offline tests for the on-disk-five wiring (AGI, energy, gas, county)."""

import pandas as pd
import pytest

from popest import energy as energy_mod
from popest import irs as irs_mod
from popest import medicare as medicare_mod
from popest.constants import (
    GAS_RESIDENTIAL_PER_CAPITA,
    IRS_AGI_PER_CAPITA,
    MEDICARE_AGED_SHARE,
)


def test_soi_agi_real_file():
    """The 206MB SOI file is on disk; verify AGI extraction end-to-end."""
    r = irs_mod.load_soi_agi()
    assert r["year"] == 2022
    # total AGI 2022 is ~$14.8 trillion; assert the order of magnitude
    assert 13e12 < r["total_agi"] < 16e12, r["total_agi"]

    from popest.national import agi
    entry = agi()
    expected = r["total_agi"] / IRS_AGI_PER_CAPITA.central
    assert entry["central"] == pytest.approx(expected)
    assert entry["low"] == pytest.approx(
        r["total_agi"] / IRS_AGI_PER_CAPITA.high)


def test_total_primary_energy(tmp_path, monkeypatch):
    path = tmp_path / "te.csv"
    path.write_text(
        "MSN,YYYYMM,Value,Column_Order,Description,Unit\n"
        "T01.01,202313,94.0,1,Total Primary Energy Consumption,Quadrillion Btu\n"
        "T01.01,202413,96.472337,1,Total Primary Energy Consumption,Quadrillion Btu\n"
        "T01.01,202401,8.0,1,Total Primary Energy Consumption,Quadrillion Btu\n"
    )
    monkeypatch.setattr(energy_mod, "TOTAL_ENERGY_CSV", path)
    e = energy_mod.total_primary_energy()
    assert e["year"] == 2024
    assert e["quad_btu"] == pytest.approx(96.472337)

    # divisor is PER-CAPITA in million Btu: ~284e6 Btu, not 284
    from popest.constants import TOTAL_ENERGY_PER_CAPITA
    implied = e["quad_btu"] * 1e15 / (TOTAL_ENERGY_PER_CAPITA.central * 1e6)
    assert 300e6 < implied < 400e6, implied


def test_gas_volume_voice():
    from popest import national

    entry = national.gas_volume()
    cf = 4389.0e9
    expected = cf / GAS_RESIDENTIAL_PER_CAPITA.central
    assert entry["central"] == pytest.approx(expected, rel=1e-3)
    assert entry["low"] < entry["central"] < entry["high"]


def test_medicare_county_parse(tmp_path, monkeypatch):
    csv = (
        "YEAR,MONTH,BENE_GEO_LVL,BENE_FIPS_CD,AGED_TOT_BENES\n"
        "2026,July,County,01001,54000\n"
        "2026,July,County,01003,21000\n"
        "2026,July,National,,64042910\n"
        "2025,December,County,01001,52000\n"
    )
    cache = tmp_path / "medicare.csv"
    cache.write_text(csv)
    monkeypatch.setattr(medicare_mod, "CACHE", cache)

    county = medicare_mod.county_aged_beneficiaries()
    # latest year/month only: 2026 July
    got = dict(zip(county["fips"], county["aged_benes"]))
    assert got == {"01001": 54000.0, "01003": 21000.0}

    from popest.methods.medicare import estimate_county
    est = estimate_county(county)
    row = est[est["fips"] == "01001"].iloc[0]
    expected = 54000 / (MEDICARE_AGED_SHARE.central * 0.97)
    assert row["pop_medicare_central"] == pytest.approx(expected)
    assert est["pop_medicare_low"].sum() < est["pop_medicare_high"].sum()
