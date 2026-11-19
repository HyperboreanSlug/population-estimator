"""Offline test for the SEDS-based energy client and method math."""

import pandas as pd

from popest import energy as energy_mod
from popest.methods import energy as energy_method
from popest.constants import ELECTRICITY_RESIDENTIAL


def test_energy_method_math(tmp_path, monkeypatch):
    seds = tmp_path / "Complete_SEDS.csv"
    seds.write_text(
        "MSN,StateCode,Year,Data\n"
        "ESRCP,CA,2024,15000.0\n"    # 15,000 million kWh = 15 B kWh
        "ESRCP,TX,2024,30000.0\n"    # 30 B kWh
        "NGRCP,CA,2024,200000.0\n"
        "ESRCP,US,2024,999999.0\n"   # national row: excluded
    )
    monkeypatch.setattr(energy_mod, "SEDS_COMPLETE", seds)

    elec = energy_mod.fetch_residential_electricity_state(2024)
    assert list(elec["state"]) == ["CA", "TX"]
    assert elec["residential_bkwh"].sum() == 45.0
    assert elec["year"].iloc[0] == 2024

    result = energy_method.estimate(2024)
    ca = result[result["state"] == "CA"].iloc[0]
    expected_ca = 15e9 / ELECTRICITY_RESIDENTIAL.central
    assert ca["pop_elec_central"] == expected_ca
    # low estimate uses the high per-person constant
    assert ca["pop_elec_low"] == 15e9 / ELECTRICITY_RESIDENTIAL.high

    gas = energy_mod.fetch_natural_gas_residential(2024)
    assert gas["residential_bcf"].sum() == 200.0


def test_energy_latest_year_and_missing_file(tmp_path, monkeypatch):
    seds = tmp_path / "Complete_SEDS.csv"
    seds.write_text(
        "MSN,StateCode,Year,Data\n"
        "ESRCP,CA,2023,10000.0\n"
        "ESRCP,CA,2024,11000.0\n"
    )
    monkeypatch.setattr(energy_mod, "SEDS_COMPLETE", seds)
    latest = energy_mod.fetch_residential_electricity_state()
    assert latest["year"].iloc[0] == 2024
    assert latest["residential_bkwh"].iloc[0] == 11.0

    monkeypatch.setattr(energy_mod, "SEDS_COMPLETE",
                        tmp_path / "missing.csv")
    empty = energy_mod.fetch_residential_electricity_state(2024)
    assert empty.empty
