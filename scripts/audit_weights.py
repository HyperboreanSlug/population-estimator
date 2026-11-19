#!/usr/bin/env python3
"""Weight audit: recompute every voice from its own numerator and
constant, compare with the latest run, and print the weight, the
citation class, and the census-dependency flag for each.

Checks the three things the operator asked for on 2026-11-19:
appropriately cited (source names the real file or statistic class),
calculated (recomputed central matches the run output within 0.5%),
and weighed (weight vs the plan's criteria is reviewed separately).

Usage: python scripts/audit_weights.py
"""
import pandas as pd

from popest import constants as K
from popest.constants import GAL_PER_MGAL

SUMMARY = "output/summary.txt"
ROWS = []


def load_summary_values():
    import re
    text = open(SUMMARY).read()
    block = re.search(r"Method contributions:\n(.*?)\n\nCounty coverage",
                      text, re.S).group(1)
    vals = {}
    for line in block.strip().splitlines():
        m = re.match(r"\s*(\S+)\s+([\d,]+)\s+w=([\d.]+)", line)
        if m:
            name, central, w = m.groups()
            vals[name] = (float(central.replace(",", "")), float(w))
    return vals


def check(summary_vals, name, numerator, unit, central_calc,
          const_name, const_src):
    sm = summary_vals.get(name, (0.0, 0.0))
    summary_val, weight = sm
    ok = (summary_val > 0
          and abs(central_calc - summary_val) / summary_val < 0.005)
    census_inf = any(w in const_src.lower()
                     for w in ("census", "recs", "census-informed"))
    ROWS.append((name, weight, f"{numerator:,.0f}"[:13], unit,
                 f"{central_calc:,.0f}",
                 f"{summary_val:,.0f}" if summary_val else "absent",
                 "OK" if ok else "MISMATCH", const_name,
                 "census-informed" if census_inf else "independent"))


def main():
    sm = load_summary_values()

    from popest.water import fetch_water_use_2015
    w = fetch_water_use_2015()
    ps = w["ps_withdrawals_mgal_d"].sum() * GAL_PER_MGAL
    dom = w["dom_withdrawals_mgal_d"].sum() * GAL_PER_MGAL
    check(sm, "water", ps + dom, "gal/day",
          ps / K.WATER_USE_PUBLIC_SUPPLY_TOTAL.central
          + dom / K.WATER_USE_DOMESTIC_SELF_SUPPLIED.central,
          "PS 120 + DOM 85", "AWWA/USGS engineering ranges")

    from popest.energy import (fetch_natural_gas_residential,
                               fetch_residential_electricity_state,
                               total_primary_energy)
    e = fetch_residential_electricity_state()
    kwh = e["residential_bkwh"].sum() * 1e9
    check(sm, "energy", kwh, "kWh/yr",
          kwh / K.ELECTRICITY_RESIDENTIAL.central,
          "4200 kWh/p", K.ELECTRICITY_RESIDENTIAL.source)
    te = total_primary_energy()["quad_btu"] * 1e15
    check(sm, "total_energy", te, "Btu",
          te / (K.TOTAL_ENERGY_PER_CAPITA.central * 1e6),
          "284 MMBtu", K.TOTAL_ENERGY_PER_CAPITA.source)
    g = fetch_natural_gas_residential()
    gcf = g["residential_bcf"].sum() * 1e9
    check(sm, "gas_volume", gcf, "cubic ft",
          gcf / K.GAS_RESIDENTIAL_PER_CAPITA.central,
          "13,100 cf", K.GAS_RESIDENTIAL_PER_CAPITA.source)

    from popest.waste import (gasoline_consumption_national,
                              msw_generation_national,
                              vehicle_registrations_national)
    msw = msw_generation_national()
    msw_lbs = msw["total_million_tons"] * 1e6 * 2000
    check(sm, "msw", msw_lbs, "lbs/yr",
          msw_lbs / (K.MSW_GENERATION.central * 365),
          "4.9 lb/p/d", "EPA per-capita (census-denominated)")
    gal = gasoline_consumption_national()["total_billion_gal"] * 1e9
    check(sm, "gasoline", gal, "gal/yr",
          gal / K.GASOLINE_USE.central, "390 gal/p", K.GASOLINE_USE.source)
    veh = vehicle_registrations_national()["total_million_vehicles"] * 1e6
    check(sm, "vehicles", veh, "vehicles",
          veh / (K.VEHICLES_PER_ADULT.central * 0.78),
          "0.85/adult x 0.78", "adult share is census-informed")

    from popest.healthcare import (healthcare_utilization_national,
                                   hospital_cost_report)
    hc = healthcare_utilization_national()
    check(sm, "healthcare", hc["er_visits_total"], "ER visits",
          hc["er_visits_total"] / K.ER_VISIT_RATE.central,
          "0.4 visits/p", "CDC NCHS published rate")
    hd = hospital_cost_report()["inpatient_days"]
    check(sm, "hospital_days", hd, "inpatient days",
          hd / K.INPATIENT_DAYS_PER_CAPITA.central,
          "0.56 d/p", K.INPATIENT_DAYS_PER_CAPITA.source)

    from popest.census import fetch_census_housing_2020
    hu = fetch_census_housing_2020()
    units = float(hu["housing_units_2020"].sum())
    check(sm, "housing", units, "units",
          units * 0.87 * 2.6 + units * 0.025,
          "0.87 occ x 2.6 pph + 2.5% GQ",
          "decennial enumeration + engineering ratios")

    from popest.vitals import national_births, national_deaths
    b = national_births(2024)["count"]
    check(sm, "vitals", b, "births", b / (11.0 / 1000),
          "11/1000", "rate is census-informed")
    d = national_deaths(2024)["count"]
    check(sm, "vitals_deaths", d, "deaths", d / (10.0 / 1000),
          "10/1000", "rate is census-informed")

    from popest.buildings import estimate_from_buildings
    r = estimate_from_buildings()
    check(sm, "buildings", 128_500_000, "buildings (approx)",
          r["buildings_central"], "0.72x0.87x2.6",
          "approximated: Tier-5 validation, reported-only")

    from popest.consumption import (grocery_sales_national,
                                     snap_participation_national,
                                     wireless_subscribers_national)
    snap = snap_participation_national()["participants"]
    check(sm, "snap", snap, "participants", snap / 0.124,
          "0.124 rate", "census-informed rate")
    wire = wireless_subscribers_national()["unique_subscriber_estimate"]
    check(sm, "wireless", wire, "unique subs (lit)", wire / 1.05,
          "1.05/person", "CTIA literature; no public dataset exists")
    gr = grocery_sales_national()["total_dollars"]
    check(sm, "grocery", gr, "dollars", gr / 2950.0,
          "2950 $/p", "census-informed constant")

    from popest.irs import load_soi_agi, load_soi_summary
    soi = load_soi_summary()
    check(sm, "irs", soi["total_exemptions"], "exemptions",
          soi["total_exemptions"] / 0.88, "12% non-filer",
          "rate range published")
    agi = load_soi_agi()["total_agi"]
    check(sm, "irs_agi", agi, "AGI dollars",
          agi / K.IRS_AGI_PER_CAPITA.central,
          "44.5k $/p", K.IRS_AGI_PER_CAPITA.source)

    from popest.bls import load_bls_data
    bls = load_bls_data()
    emp = bls["total_employed_thousands"][0]["value"] * 1000
    check(sm, "bls", emp, "employed", emp / (0.595 * 0.78),
          "0.595 EP x 0.78 adult", "census-informed adult share")

    from popest.education import higher_ed_enrollment, public_enrollment
    enr = public_enrollment()["enrollment"].sum()
    check(sm, "education", enr, "students",
          enr / K.EDUCATION_ENROLLMENT_SHARE.central,
          "0.147 share", K.EDUCATION_ENROLLMENT_SHARE.source)
    col = higher_ed_enrollment()["enrollment"]
    check(sm, "college", col, "students",
          col / K.COLLEGE_ENROLLMENT_SHARE.central,
          "0.056 share", K.COLLEGE_ENROLLMENT_SHARE.source)

    from popest.sdwis import cws_population_served
    served = cws_population_served()["pop_served"].sum()
    check(sm, "sdwis", served, "served pop",
          served / K.CWS_COVERAGE_FRACTION.central,
          "0.85 coverage", "USGS coverage fraction")

    from popest.medicare import national_aged_beneficiaries
    mb = national_aged_beneficiaries()["aged_benes"]
    check(sm, "medicare", mb, "aged benes",
          mb / (K.MEDICARE_AGED_SHARE.central * 0.97),
          "0.17 x 0.97", K.MEDICARE_AGED_SHARE.source)

    from popest.meters import (residential_electricity_meters,
                               residential_gas_customers)
    meters = residential_electricity_meters()["meters"].sum()
    check(sm, "electricity_meters", meters, "meters",
          meters * K.PERSONS_PER_METER.central,
          "2.40 p/meter", K.PERSONS_PER_METER.source)
    gc = residential_gas_customers()["customers"]
    check(sm, "gas_meters", gc, "gas customers",
          gc * K.GAS_PERSONS_PER_CUSTOMER.central,
          "4.25 p/customer", K.GAS_PERSONS_PER_CUSTOMER.source)

    from popest.travel import (enplanements, library_survey, transit_trips)
    faa = enplanements()["total"]
    check(sm, "enplanements", faa, "boardings",
          faa / K.ENPLANEMENTS_PER_CAPITA.central,
          "2.80/p", K.ENPLANEMENTS_PER_CAPITA.source)
    ntd = transit_trips()["total"]
    check(sm, "transit", ntd, "trips",
          ntd / K.TRANSIT_TRIPS_PER_CAPITA.central,
          "22 trips/p", K.TRANSIT_TRIPS_PER_CAPITA.source)
    lib = library_survey()["visits"]
    check(sm, "library_visits", lib, "visits",
          lib / K.LIBRARY_VISITS_PER_CAPITA.central,
          "2.4 visits/p", K.LIBRARY_VISITS_PER_CAPITA.source)

    from popest.consumption import food_expenditure
    food = food_expenditure()["total_dollars"]
    check(sm, "food_expenditure", food, "dollars",
          food / K.FOOD_EXPENDITURE_PER_CAPITA.central,
          "7400 $/p", K.FOOD_EXPENDITURE_PER_CAPITA.source)

    from popest.bea import national_personal_income
    inc = national_personal_income()["total_income"]
    check(sm, "personal_income", inc, "dollars",
          inc / K.PER_CAPITA_INCOME.central,
          "73k $/p", K.PER_CAPITA_INCOME.source)

    from popest.drivers import licensed_drivers
    drv = licensed_drivers()["drivers"]
    check(sm, "drivers", drv, "drivers",
          drv / (K.DRIVERS_PER_ADULT.central * K.ADULT_SHARE.central),
          "0.90 x 0.78", "census-informed adult share")

    from popest.medicaid import medicaid_chip_enrollment
    med = medicaid_chip_enrollment()["medicaid_chip"]
    check(sm, "medicaid", med, "enrolled",
          med / K.MEDICAID_ENROLLMENT_SHARE.central,
          "0.215 share", K.MEDICAID_ENROLLMENT_SHARE.source)

    df = pd.DataFrame(ROWS, columns=[
        "voice", "weight", "numerator", "num_unit", "recomputed",
        "in_summary", "check", "constant", "constant_class"])
    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 44)
    print(df.to_string(index=False))
    bad = df[df["check"] != "OK"]
    print(f"\nMISMATCHES: {len(bad)} of {len(df)}")
    return 0 if len(bad) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
