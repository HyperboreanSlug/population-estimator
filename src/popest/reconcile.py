"""Reconciliation analysis (PLAN.md Discrepancy Analysis).

For each measured national total, compute the per-capita constant that a
given target population would require, and check it against the constant's
published range. If a claimed population level needs constants far outside
their published ranges across many independent methods simultaneously, the
claimed level is inconsistent with the measured totals (and vice versa).

This never tunes constants to a target; it states what each target
implies and whether that is inside the published literature range.
"""

import pandas as pd

from popest.census import CENSUS_2020_NATIONAL


def gather_totals() -> dict:
    """Collect measured national totals from cached data files."""
    from popest.constants import GAL_PER_MGAL

    totals = {}
    from popest.water import fetch_water_use_2015

    w = fetch_water_use_2015()
    totals["water_total"] = (
        float(w["ps_withdrawals_mgal_d"].sum())
        + float(w["dom_withdrawals_mgal_d"].sum())) * GAL_PER_MGAL

    from popest.wastewater import download_npdes_part1, load_municipal_flows

    flows = load_municipal_flows(download_npdes_part1())
    totals["ww_design"] = float(flows["design_flow_mgd"].sum()) * 1e6

    from popest.energy import fetch_residential_electricity_state

    e = fetch_residential_electricity_state()
    if not e.empty:
        totals["energy"] = float(e["residential_bkwh"].sum()) * 1e9
        totals["energy_year"] = int(e["year"].max())

    from popest.waste import (
        gasoline_consumption_national,
        msw_generation_national,
        vehicle_registrations_national,
    )

    totals["msw"] = (
        msw_generation_national()["total_million_tons"] * 1e6 * 2000.0)
    totals["gasoline"] = (
        gasoline_consumption_national()["total_billion_gal"] * 1e9)
    totals["vehicles"] = (
        vehicle_registrations_national()["total_million_vehicles"] * 1e6)

    from popest.irs import load_soi_summary

    soi = load_soi_summary()
    if "error" not in soi:
        totals["irs_exemptions"] = float(soi["total_exemptions"])

    from popest.bls import load_bls_data

    bls = load_bls_data()
    if bls.get("total_employed_thousands"):
        totals["employed"] = (
            float(bls["total_employed_thousands"][0]["value"]) * 1000.0)

    from popest.vitals import national_births, national_deaths

    totals["births"] = float(national_births(2024)["count"])
    totals["deaths"] = float(national_deaths(2024)["count"])

    try:
        from popest.irs import load_soi_agi

        totals["irs_agi"] = load_soi_agi()["total_agi"]
    except Exception:
        pass

    try:
        from popest.energy import total_primary_energy

        te = total_primary_energy()
        if te:
            totals["total_energy_btus"] = te["quad_btu"] * 1e15
    except Exception:
        pass

    try:
        from popest.energy import fetch_natural_gas_residential

        gas = fetch_natural_gas_residential()
        if not gas.empty:
            totals["gas_volume_cf"] = (
                float(gas["residential_bcf"].sum()) * 1e9)
    except Exception:
        pass

    from popest.education import public_enrollment

    enroll = public_enrollment()
    if not enroll.empty:
        totals["enrollment"] = float(enroll["enrollment"].sum())

    from popest.sdwis import cws_population_served

    served = cws_population_served()
    if not served.empty:
        totals["cws_served"] = float(served["pop_served"].sum())

    from popest.waste import vmt_annual

    vmt = vmt_annual()
    if vmt:
        totals["vmt"] = float(vmt["total_million_miles"]) * 1e6

    try:
        from popest.medicare import national_aged_beneficiaries

        mb = national_aged_beneficiaries()
        totals["medicare_aged"] = mb["aged_benes"]
    except Exception:
        # cms.gov unreachable from some resolvers; voice reported absent
        pass

    from popest.consumption import snap_participation_national

    totals["snap"] = float(snap_participation_national()["participants"])

    from popest.healthcare import healthcare_utilization_national

    totals["er_visits"] = float(
        healthcare_utilization_national()["er_visits_total"])

    totals["housing_units"] = float(
        CENSUS_2020_NATIONAL["total_housing_units"])
    return totals


# (name, unit, numerator key, published low, high, kind, scale, note)
# kind "divide": implied = numerator / pop * scale
# kind "complement": implied = 1 - numerator / pop
# kind "units_pph": implied = pop / (numerator * occ * gq)
# kind "aged": implied = numerator / (pop * enrollment_rate)
ROWS = [
    ("water withdrawals (PS+wells)", "gal/person/day", "water_total", 90.5,
     153.5, "divide", 1.0,
     "blended PS 95-160 and well 65-110 at a 0.85 served share"),
    ("wastewater design flow", "gal/person/day", "ww_design", 60.0, 110.0,
     "divide", 1.0, "EPA NPDES municipal design flow"),
    ("residential electricity", "kWh/person/year", "energy", 3500.0, 5200.0,
     "divide", 1.0, "RECS-derived per person"),
    ("municipal solid waste", "lb/person/day", "msw", 4.0, 5.5,
     "divide", 1.0 / 365.0, "EPA 2018 generation"),
    ("gasoline", "gal/person/year", "gasoline", 300.0, 500.0,
     "divide", 1.0, "EIA product supplied"),
    ("vehicles", "vehicles/person", "vehicles", 0.585, 0.78,
     "divide", 1.0, "0.75-1.0 per adult x 0.78 adult share"),
    ("IRS non-filer share", "fraction", "irs_exemptions", 0.08, 0.18,
     "complement", 1.0, "exemptions counted, rest non-filers"),
    ("birth rate", "births/1000/year", "births", 9.5, 13.0,
     "divide", 1000.0, "Census PEP BIRTHS2024 (NCHS-derived)"),
    ("death rate", "deaths/1000/year", "deaths", 8.5, 12.0,
     "divide", 1000.0, "Census PEP DEATHS2024 (NCHS-derived)"),
    ("IRS AGI", "dollars/person/year", "irs_agi", 38000.0, 52000.0,
     "divide", 1.0, "IRS SOI total AGI / population"),
    ("total primary energy", "million Btu/person/year", "total_energy_btus",
     250.0, 320.0, "divide", 1e-6, "EIA MER total consumption"),
    ("residential gas volume", "cubic feet/person/year", "gas_volume_cf",
     9000.0, 18000.0, "divide", 1.0, "EIA residential deliveries"),
    ("employment share", "employed/person", "employed", 0.4446, 0.4836,
     "divide", 1.0, "BLS EP ratio 0.57-0.62 x 0.78 adult share"),
    ("SNAP participation", "fraction", "snap", 0.11, 0.14,
     "divide", 1.0, "USDA FNS participants (FY2025 file)"),
    ("ER visits", "visits/person/year", "er_visits", 0.3, 0.5,
     "divide", 1.0, "CDC NCHS 2021"),
    ("household size", "persons/occupied unit", "housing_units", 2.4, 2.8,
     "units_pph", 1.0, "assumes occupancy 0.87, GQ 2.5%"),
    ("K-12 enrollment share", "fraction", "enrollment", 0.140, 0.155,
     "divide", 1.0, "NCES 2024-25 enrollment"),
    ("CWS water coverage", "fraction", "cws_served", 0.82, 0.88,
     "divide", 1.0, "USGS share on community water"),
    ("VMT", "miles/person/year", "vmt", 8500.0, 11000.0,
     "divide", 1.0, "FHWA 2024 vehicle miles"),
    ("Medicare aged share", "fraction x 0.97", "medicare_aged", 0.155, 0.185,
     "aged", 1.0, "CMS aged beneficiaries / enrollment rate"),
]

UNITS_PPH_OCC = 0.87
UNITS_PPH_GQ = 1.025
MEDICARE_ENROLLMENT = 0.97


def _implied(row, numerator: float, pop: float) -> float:
    name, unit, key, low, high, kind, scale, note = row
    if kind == "divide":
        return numerator / pop * scale
    if kind == "complement":
        return 1.0 - numerator / pop
    if kind == "units_pph":
        return pop / (numerator * UNITS_PPH_OCC * UNITS_PPH_GQ)
    if kind == "aged":
        return numerator / (pop * MEDICARE_ENROLLMENT)
    raise ValueError(kind)


def reconciliation_table(totals: dict,
                         targets: list[tuple[str, float | None]],
                         ) -> pd.DataFrame:
    """Implied constants per target population vs published ranges.

    targets: list of (label, population). None entries are dropped.
    """
    live = [(label, pop) for label, pop in targets if pop]
    out = []
    for row in ROWS:
        name, unit, key, low, high, kind, scale, note = row
        numerator = totals.get(key)
        if not numerator:
            continue
        entry = {
            "method": name, "unit": unit, "measured_total": numerator,
            "published_low": low, "published_high": high, "source": note,
        }
        for label, pop in live:
            implied = _implied(row, numerator, pop)
            inside = (low <= implied <= high) or (
                abs(implied - low) < low * 0.01) or (
                abs(implied - high) < high * 0.01)
            entry[f"implied_{label}"] = implied
            entry[f"verdict_{label}"] = "inside" if inside else "OUTSIDE"
        out.append(entry)
    return pd.DataFrame(out)


def default_targets(census_pop: float, ensemble: float) -> list:
    return [
        ("census_pep_2024", census_pop),
        ("ensemble", ensemble),
        ("claimed_400m", 400_000_000.0),
        ("claimed_450m", 450_000_000.0),
        ("claimed_500m", 500_000_000.0),
    ]


def summarize(table: pd.DataFrame) -> list[str]:
    """One line per claimed target: how many constants would break."""
    lines = []
    for label in ("census_pep_2024", "ensemble", "claimed_400m",
                  "claimed_450m", "claimed_500m"):
        verdict_col = f"verdict_{label}"
        if verdict_col not in table.columns:
            continue
        outside = int((table[verdict_col] == "OUTSIDE").sum())
        total = int(table[verdict_col].notna().sum())
        lines.append(f"{label}: {outside} of {total} constants OUTSIDE "
                     f"their published ranges")
    return lines


def run_reconciliation(census_pop: float, ensemble: float) -> pd.DataFrame:
    totals = gather_totals()
    targets = default_targets(census_pop, ensemble)
    return reconciliation_table(totals, targets)


if __name__ == "__main__":
    from popest.census import fetch_census_pep_counties

    pep = fetch_census_pep_counties(2024)
    table = run_reconciliation(pep["national"], 358_571_850.0)
    pd.set_option("display.width", 200)
    print(table.to_string(index=False))
    print()
    for line in summarize(table):
        print(line)
