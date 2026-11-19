"""Offline tests for the source-expansion parsers and reconciliation.

Fixtures are synthetic files written to tmp_path; module paths are
monkeypatched. No network.
"""

import zipfile

import pandas as pd
import pytest

from popest import education as education_mod
from popest import consumption as consumption_mod
from popest import medicare as medicare_mod
from popest import reconcile as reconcile_mod
from popest import sdwis as sdwis_mod
from popest import waste as waste_mod
from popest.constants import (
    CWS_COVERAGE_FRACTION,
    EDUCATION_ENROLLMENT_SHARE,
)
from popest.methods.education import estimate as education_estimate
from popest.methods.sdwis import estimate as sdwis_estimate


def _zip_with(path, name, content: str):
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(name, content)


def test_public_enrollment_totals(tmp_path, monkeypatch):
    zpath = tmp_path / "ccd.zip"
    csv = (
        "SCHOOL_YEAR,FIPST,STATENAME,ST,GRADE,RACE_ETHNICITY,SEX,"
        "STUDENT_COUNT,TOTAL_INDICATOR\n"
        "2024-2025,01,ALABAMA,AL,Grade 1,Total,Total,187,"
        "Category Set A - By Race/Ethnicity; Sex; Grade\n"
        "2024-2025,01,ALABAMA,AL,Total,Total,Total,750000,"
        "Education Unit Total\n"
        "2024-2025,06,CALIFORNIA,CA,Total,Total,Total,1500000,"
        "Education Unit Total\n"
    )
    _zip_with(zpath, "ccd.csv", csv)
    monkeypatch.setattr(education_mod, "NCES_ZIP", zpath)
    enroll = education_mod.public_enrollment()
    assert enroll["enrollment"].sum() == 2_250_000
    assert set(enroll["state"]) == {"AL", "CA"}


def test_education_method_math(tmp_path, monkeypatch):
    zpath = tmp_path / "ccd.zip"
    csv = ("SCHOOL_YEAR,ST,STATENAME,STUDENT_COUNT,TOTAL_INDICATOR\n"
           "2024-2025,AL,ALABAMA,49573761,Education Unit Total\n")
    _zip_with(zpath, "ccd.csv", csv)
    monkeypatch.setattr(education_mod, "NCES_ZIP", zpath)
    monkeypatch.setattr(education_mod, "NSLP_XLSX", tmp_path / "no.xlsx")
    monkeypatch.setattr(education_mod, "WIC_XLSX", tmp_path / "no.xlsx")

    r = education_estimate()
    expected = 49_573_761 / EDUCATION_ENROLLMENT_SHARE.central
    assert r["education_central"] == pytest.approx(expected)
    # low population: high enrollment share
    assert r["education_low"] == pytest.approx(
        49_573_761 / EDUCATION_ENROLLMENT_SHARE.high)
    assert "reported_nslp_participants" not in r


def test_sdwis_excludes_inactive_and_non_community(tmp_path, monkeypatch):
    zpath = tmp_path / "sdwa.zip"
    csv = (
        "PWSID,PWS_NAME,STATE_CODE,PWS_TYPE_CODE,PWS_ACTIVITY_CODE,"
        "POPULATION_SERVED_COUNT\n"
        "CA1,Active Muni,CA,CWS,A,1000\n"
        "CA2,Ghost Muni,CA,CWS,I,5000\n"
        "CA3,School Well,CA,NTNCWS,A,100\n"
        "TX1,Active Muni TX,TX,CWS,A,2000\n"
    )
    _zip_with(zpath, "SDWA_SYSTEM_SEARCH.csv", csv)
    monkeypatch.setattr(sdwis_mod, "SDWIS_ZIP", zpath)

    served = sdwis_mod.cws_population_served()
    assert served["pop_served"].sum() == 3000  # 1000 + 2000 only
    assert served["n_systems"].sum() == 2

    r = sdwis_estimate()
    assert r["sdwis_central"] == pytest.approx(3000 / CWS_COVERAGE_FRACTION.central)
    assert r["sdwis_low"] == pytest.approx(3000 / CWS_COVERAGE_FRACTION.high)
    assert r["sdwis_high"] == pytest.approx(3000 / CWS_COVERAGE_FRACTION.low)


def test_snap_real_file(tmp_path, monkeypatch):
    fixture = pd.DataFrame([
        ["SNAP ANNUAL SUMMARY (fna.usda.gov)", None, None],
        [None, None, None],
        ["Fiscal Year", "Average Participation (Thousands)",
         "Total Benefits (Millions of Dollars)"],
        ["FY 2024", 41147.0, 1.0],
        ["FY 2025", 42142.18, 2.0],
    ])
    path = tmp_path / "snap.xlsx"
    fixture.to_excel(path, index=False, header=False)
    monkeypatch.setattr(consumption_mod, "SNAP_XLSX", path)

    snap = consumption_mod.snap_participation_national()
    assert snap["year"] == 2025
    assert snap["participants"] == pytest.approx(42_142_180.0)
    assert "0.008%" in snap["note"]

    results = consumption_mod.estimate_consumption()
    assert results["snap_central"] == pytest.approx(
        42_142_180.0 / 0.124)
    assert results["snap_low"] < results["snap_high"]


def test_vmt_parse(tmp_path, monkeypatch):
    rows = [
        ["ANNUAL VEHICLE DISTANCE TRAVELED - 2024", None, None, None,
         None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None, None],
        ["Updated: February 2026", "Table VM-1", None, None, None, None,
         None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None, None],
        ["YEAR", "ITEM", "LDV SHORT", "MOTORCYCLES", "BUSES", "LDV LONG",
         "SU TRUCKS", "COMBO", "ALL LDV", "SU+COMBO", "ALL MOTOR VEHICLES"],
        [None, None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None, None],
        ["Motor-Vehicle Travel:", None, None, None, None, None, None,
         None, None, None, None],
        ["(millions of vehicle-miles)", None, None, None, None, None,
         None, None, None, None, None],
        [2024, "Interstate Rural", 146051.1, 1069.3, 1501.6, 51571.6,
         11956.5, 30180.9, 197622.7, 42137.4, 229760.1],
        [2023, "Interstate Rural", 141501.7, 1014.3, 1575.9, 53227.6,
         11956.5, 28800.0, 194729.3, 40756.5, 235485.8],
        [2024, "Total Rural and Urban  5/", 2222414.7, 6451.2, 6088.2,
         257221.3, 119556.1, 301809.4, 2479636.0, 421365.5, 3294031.2],
        [2023, "Total Rural and Urban  5/", 2173555.4, 6029.1, 6047.0,
         255861.9, 50278.8, 281000.0, 2229417.3, 331278.8, 3246817.0],
        [2024, "Number of motor vehicles", 205550881, 9261249, 1051056,
         62105773, 13380605, 3200000, 27665654, 16580605, 297525836],
    ]
    path = tmp_path / "vm1.xlsx"
    pd.DataFrame(rows).to_excel(path, index=False, header=False)
    monkeypatch.setattr(waste_mod, "VMT_XLSX", path)

    vmt = waste_mod.vmt_annual()
    assert vmt["year"] == 2024
    assert vmt["total_million_miles"] == pytest.approx(3_294_031.2)
    assert vmt["vm1_motor_vehicles_registered"] == pytest.approx(
        297_525_836.0)


def test_medicare_latest_national_rows(tmp_path, monkeypatch):
    csv = (
        "YEAR,MONTH,BENE_GEO_LVL,BENE_STATE_ABRVTN,BENE_COUNTY_DESC,"
        "BENE_FIPS_CD,TOT_BENES,ORGNL_MDCR_BENES,MA_AND_OTH_BENES,"
        "AGED_TOT_BENES,AGED_ESRD_BENES,DSBLD_TOT_BENES\n"
        "2025,11,National,,,,58000000,34000000,24000000,52000000,"
        "100000,6000000\n"
        "2026,7,National,,,,60000000,34000000,26000000,54000000,"
        "100000,6000000\n"
        "2026,7,State,AL,,,500000,300000,200000,450000,5000,50000\n"
    )
    cache = tmp_path / "medicare.csv"
    cache.write_text(csv)
    monkeypatch.setattr(medicare_mod, "CACHE", cache)

    benes = medicare_mod.national_aged_beneficiaries()
    assert benes["year"] == 2026
    assert benes["month"] == 7
    assert benes["aged_benes"] == 54_000_000.0
    assert benes["total_benes"] == 60_000_000.0

    from popest.methods.medicare import estimate
    r = estimate()
    expected = 54_000_000 / (0.17 * 0.97)
    assert r["medicare_central"] == pytest.approx(expected)
    assert r["medicare_low"] == pytest.approx(
        54_000_000 / (0.185 * 0.97))
    assert r["medicare_high"] == pytest.approx(
        54_000_000 / (0.155 * 0.97))


def test_reconciliation_math_kinds():
    totals = {"water_total": 4.2e10, "irs_exemptions": 2.8e8,
              "housing_units": 1.4e8, "medicare_aged": 6.0e7,
              "vmt": 3.294e12}
    table = reconcile_mod.reconciliation_table(
        totals, [("pop", 3.4e8)])
    row = table[table["method"] == "water withdrawals (PS+wells)"].iloc[0]
    assert row["implied_pop"] == pytest.approx(4.2e10 / 3.4e8)
    assert row["verdict_pop"] == "inside"

    row = table[table["method"] == "IRS non-filer share"].iloc[0]
    assert row["implied_pop"] == pytest.approx(1 - 2.8e8 / 3.4e8)

    row = table[table["method"] == "household size"].iloc[0]
    assert row["implied_pop"] == pytest.approx(
        3.4e8 / (1.4e8 * 0.87 * 1.025))

    row = table[table["method"] == "Medicare aged share"].iloc[0]
    assert row["implied_pop"] == pytest.approx(6.0e7 / (3.4e8 * 0.97))

    # missing numerator rows are dropped
    assert "K-12 enrollment share" not in set(table["method"])


def test_reconciliation_outside_verdict():
    totals = {"births": 3.667e6}
    table = reconcile_mod.reconciliation_table(
        totals, [("tiny", 1.0e8)])
    row = table[table["method"] == "birth rate"].iloc[0]
    assert row["implied_tiny"] == pytest.approx(36.67)  # per 1000
    assert row["verdict_tiny"] == "OUTSIDE"
