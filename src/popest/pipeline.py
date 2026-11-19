"""Full pipeline orchestration: `popest run`.

Runs every method fail-soft (a failed source drops that voice, never the
run), combines the national ensemble with bootstrap uncertainty, builds
the county ensemble, rolls counties to states, and writes every output
under output/ along with a human-readable summary.
"""

import pandas as pd

from popest import report
from popest.discrepancy import discrepancy_report
from popest.ensemble import combine_county, combine_national, state_rollup
from popest.uncertainty import bootstrap_national


def run(year: int = 2024, api_key: str | None = None) -> dict:
    """Execute the full pipeline. Returns the result bundle."""
    methods: dict[str, dict] = {}
    county_dfs: dict[str, pd.DataFrame] = {}
    names = pd.DataFrame(columns=["fips", "county"])
    notes: list[str] = []

    def step(msg: str) -> None:
        print(f"\n{msg}")

    # --- county-level physical methods -------------------------------
    step("[1/12] Water budget (USGS 2015)...")
    try:
        from popest.methods.water_budget import estimate, national_summary
        from popest.water import fetch_water_use_2015

        raw = fetch_water_use_2015()
        water = estimate(raw)
        ws = national_summary(water)
        methods["water"] = {
            "central": ws["central"], "low": ws["low_pop"],
            "high": ws["high_pop"], "form": "inverse",
            "source": f"USGS water use {ws.get('counties', 0)} counties (2015)",
        }
        water_c = water.rename(columns={
            "pop_central": "pop_water_central",
            "pop_low_pop": "pop_water_low",
            "pop_high_pop": "pop_water_high",
        })
        county_dfs["water"] = water_c[
            ["fips", "pop_water_central", "pop_water_low", "pop_water_high"]]
        names = water[["fips", "state", "county"]].copy()
        print(f"  central {ws['central']:,.0f}")
    except Exception as e:
        notes.append(f"water FAILED: {e}")
        print(f"  FAILED: {e}")

    step("[2/12] Wastewater design flow (EPA NPDES)...")
    try:
        from popest.methods.wastewater import estimate, national_summary
        from popest.wastewater import download_npdes_part1, load_municipal_flows

        flows = load_municipal_flows(download_npdes_part1())
        ww = estimate(flows)
        wws = national_summary(ww)
        methods["wastewater"] = {
            "central": wws["central"], "low": wws["low"],
            "high": wws["high"], "form": "inverse",
            "source": "EPA ICIS-NPDES design flows",
        }
        ww = ww.rename(columns={
            "pop_ww_central": "pop_wastewater_central",
            "pop_ww_low": "pop_wastewater_low",
            "pop_ww_high": "pop_wastewater_high",
        })
        county_dfs["wastewater"] = ww
        print(f"  central {wws['central']:,.0f} ({wws.get('counties', 0)} counties)")
    except Exception as e:
        notes.append(f"wastewater FAILED: {e}")
        print(f"  FAILED: {e}")

    step("[3/12] Wastewater chemistry (EPA DMR FY2024)...")
    chem_summary = {}
    try:
        from popest import dmr
        from popest.methods.wastewater_chemistry import estimate, national_summary

        loads = dmr.facility_loads(dmr.filter_dmr())
        cmap = dmr.facility_county_map()
        muni = dmr.municipal_permit_ids()
        chem_c = estimate(loads, cmap, muni)
        chem_summary = national_summary(chem_c, loads, muni)
        for key in ("bod", "TSS", "Total N", "Ammonia-N"):
            pop = chem_summary.get(f"{key}_pop")
            if pop:
                n = chem_summary.get(f"{key}_facilities", 0)
                print(f"  {key + ' population':<16} {pop:>15,.0f}"
                      f"  ({n} municipal reporters)")
        if chem_summary:
            notes.append(
                f"wastewater chemistry REPORTED but not ensemble-weighted: "
                f"only {chem_summary.get('bod_facilities', 0)} municipal "
                f"plants report BOD in mass units; the load numerator is a "
                f"reporting subset, a coverage-limited lower bound.")
        chem_c = chem_c.rename(columns={
            "pop_chem_central": "pop_wastewater_chem_central",
            "pop_chem_low": "pop_wastewater_chem_low",
            "pop_chem_high": "pop_wastewater_chem_high",
        })
        county_dfs["wastewater_chem"] = chem_c
    except Exception as e:
        notes.append(f"wastewater_chem FAILED: {e}")
        print(f"  FAILED: {e}")

    step("[4/12] Housing units (census 2020)...")
    try:
        from popest.methods.housing import estimate, national_summary

        housing = estimate(api_key)
        if not housing.empty and not (housing["fips"] == "00000").any():
            hs = national_summary(housing)
            methods["housing"] = {
                "central": hs["central"], "low": hs["low"],
                "high": hs["high"], "form": "direct",
                "source": f"census housing units {hs.get('counties', 0)} counties",
            }
            county_dfs["housing"] = housing
        elif not housing.empty:
            central = float(housing["pop_housing_central"].sum())
            methods["housing"] = {
                "central": central,
                "low": float(housing["pop_housing_low"].sum()),
                "high": float(housing["pop_housing_high"].sum()),
                "form": "direct", "source": "census housing units (national)",
            }
        print(f"  central {methods.get('housing', {}).get('central', 0):,.0f}")
    except Exception as e:
        notes.append(f"housing FAILED: {e}")
        print(f"  FAILED: {e}")

    step(f"[5/12] Census comparison (PEP Vintage 2024, capped 15%)...")
    census_df = pd.DataFrame()
    census_pop = 0.0
    try:
        from popest.census import fetch_census_pep_counties

        pep = fetch_census_pep_counties(year)
        census_df = pep["counties"]
        census_pop = pep["national"]
        if pep["year_used"]:
            print(f"  PEP {pep['year_used']}: {census_pop:,.0f} "
                  f"({len(census_df)} counties)")
            if pep["year_used"] != year:
                print(f"  note: target year {year} outside PEP range, "
                      f"using {pep['year_used']}")
        else:
            print("  PEP CSV not downloaded; run: popest download")
    except Exception as e:
        notes.append(f"census FAILED: {e}")
        print(f"  FAILED: {e}")

    decennial_2020 = 0.0
    try:
        from popest.census import (
            CENSUS_2020_NATIONAL,
            fetch_census_population_2020,
        )

        decennial_df = fetch_census_population_2020(api_key)
        decennial_2020 = float(decennial_df["census_pop_2020"].sum())
        print(f"  Decennial 2020: {decennial_2020:,.0f} "
              f"({CENSUS_2020_NATIONAL['source']})")
    except Exception as e:
        print(f"  FAILED (decennial): {e}")

    # --- national-only methods ---------------------------------------
    from popest import national

    step("Energy (EIA residential electricity)...")
    national.add_national(methods, "energy", national.energy)

    step("Waste/food/vehicles/VMT...")
    national.add_national_multi(methods, national.waste_food,
                               national.NATIONAL_MULTI_SPEC)

    step("Healthcare utilization...")
    national.add_national(methods, "healthcare", national.healthcare)

    step("Vitals: births...")
    national.add_national(methods, "vitals", national.vitals)

    step("Vitals: deaths...")
    national.add_national(methods, "vitals_deaths", national.deaths)

    step("Consumption (SNAP/wireless/grocery)...")
    national.add_national_multi(methods, national.consumption,
                                national.CONSUMPTION_SPEC)

    step("IRS filers...")
    national.add_national(methods, "irs", national.irs)

    step("IRS total AGI...")
    national.add_national(methods, "irs_agi", national.agi)

    step("BLS employment...")
    national.add_national(methods, "bls", national.bls)

    step("Education (NCES enrollment)...")
    national.add_national(methods, "education", national.education)

    step("College enrollment (IPEDS)...")
    national.add_national(methods, "college", national.college)

    step("Utility meters (EIA-861 + gas customers)...")
    national.add_national(methods, "electricity_meters",
                          national.electricity_meters)
    national.add_national(methods, "gas_meters", national.gas_meters)

    step("Travel (FAA enplanements, NTD transit)...")
    national.add_national(methods, "enplanements", national.enplanements)
    national.add_national(methods, "transit", national.transit)

    step("Libraries (IMLS visits)...")
    national.add_national(methods, "library_visits", national.library_visits)

    step("Food expenditure (ERS)...")
    national.add_national(methods, "food_expenditure",
                          national.food_expenditure)

    step("Personal income (BEA)...")
    national.add_national(methods, "personal_income",
                          national.personal_income)

    step("Licensed drivers (FHWA DL-1C)...")
    national.add_national(methods, "drivers", national.drivers)

    step("Water systems (EPA SDWIS CWS served)...")
    national.add_national(methods, "sdwis", national.sdwis)

    step("Medicare aged beneficiaries (national + county)...")
    national.add_national(methods, "medicare", national.medicare)

    step("Total primary energy...")
    national.add_national(methods, "total_energy", national.total_energy)

    step("Residential natural gas volume...")
    national.add_national(methods, "gas_volume", national.gas_volume)

    step("Building footprints...")
    national.add_national(methods, "buildings", national.buildings)

    # --- county medicare voice ------------------------------------------
    try:
        from popest.medicare import county_aged_beneficiaries
        from popest.methods.medicare import estimate_county

        med_county = estimate_county(county_aged_beneficiaries())
        if not med_county.empty:
            county_dfs["medicare"] = med_county
            print(f"  Medicare county voice: {len(med_county)} counties")
    except Exception as e:
        notes.append(f"medicare county FAILED: {e}")
        print(f"  Medicare county voice FAILED: {e}")

    # --- reported-only voices (never ensemble-weighted) ----------------
    try:
        from popest.waste import lmop_landfill_acceptance

        lmop = lmop_landfill_acceptance()
        if lmop:
            notes.append(
                f"LMOP measured landfill acceptance (REPORTED): "
                f"{lmop['acceptance_tons_per_year']:,.0f} tons/yr from "
                f"{lmop['landfills_reporting']:,} landfills; all waste "
                f"streams, mixed years — upper bound, not MSW-only.")
    except Exception as e:
        print(f"  LMOP reported voice FAILED: {e}")
    try:
        from popest.waste import vmt_annual

        vmt_r = vmt_annual()
        if vmt_r.get("vm1_motor_vehicles_registered"):
            notes.append(
                f"FHWA VM-1 'motor vehicles' 2024 (REPORTED): "
                f"{vmt_r['vm1_motor_vehicles_registered']:,.0f} — "
                f"different count basis than the MV-1 registrations the "
                f"vehicles method calibrates on; not substituted.")
    except Exception as e:
        print(f"  VM-1 vehicles reported voice FAILED: {e}")

    # --- combine ------------------------------------------------------
    print("\n" + "=" * 60)
    print("  NATIONAL ENSEMBLE")
    print("=" * 60)
    estimates = {m: v["central"] for m, v in methods.items() if v["central"] > 0}
    result = combine_national(estimates, census_pop)
    boot = bootstrap_national(
        {m: v for m, v in methods.items()}, census_pop)
    print(f"  Combined:   {result['combined']:>15,.0f}")
    print(f"  Bootstrap 90% CI: {boot['lower_90']:,.0f} - "
          f"{boot['upper_90']:,.0f} ({boot['n_draws']} draws)")
    if census_pop:
        print(f"  Census PEP: {census_pop:>15,.0f}")
        print(f"  Ratio to census PEP: {result['combined'] / census_pop:.3f}")

    print("\n  Method contributions:")
    print(report.method_table(methods, result["contributions"]))

    # --- county ensemble ----------------------------------------------
    print("\n" + "=" * 60)
    print("  COUNTY ENSEMBLE")
    print("=" * 60)
    county = combine_county(county_dfs, census_df)
    covered = int((county["n_methods"] > 0).sum()) if not county.empty else 0
    covered_pop = float(county["ensemble_pop"].sum()) if not county.empty else 0.0
    print(f"  Counties with data: {covered} of {len(county)}")
    print(f"  Covered-county population: {covered_pop:,.0f}")
    states = state_rollup(county)
    print(f"  States covered: {len(states)}")

    # --- reconciliation --------------------------------------------
    print("\n" + "=" * 60)
    print("  RECONCILIATION: implied constants per population level")
    print("  (measured totals vs what each claim would require)")
    print("=" * 60)
    rec = pd.DataFrame()
    try:
        from popest import reconcile

        rec = reconcile.run_reconciliation(census_pop, result["combined"])
        for line in reconcile.summarize(rec):
            print(f"  {line}")
    except Exception as e:
        print(f"  FAILED: {e}")

    # --- outputs -------------------------------------------------------
    paths = _write_outputs(county, names, states, result, boot, census_pop,
                           methods, notes, decennial_2020, chem_summary, rec)
    print("\n  Outputs:")
    for p in paths:
        print(f"    {p}")
    return {
        "combined": result["combined"], "bootstrap": boot,
        "contributions": result["contributions"], "census": census_pop,
        "counties": county, "states": states, "notes": notes,
    }


def _write_outputs(county, names, states, result, boot, census_pop,
                   methods, notes, decennial_2020=0.0,
                   chem_summary=None, reconciliation=None) -> list:
    paths = [
        report.write_counties(county, names),
        report.write_states(states),
    ]
    if reconciliation is not None and not reconciliation.empty:
        paths.append(report.write_reconciliation(reconciliation))

    national_rows = [{
        "metric": "ensemble_combined", "value": result["combined"],
    }, {
        "metric": "ensemble_lower_90", "value": boot["lower_90"],
    }, {
        "metric": "ensemble_upper_90", "value": boot["upper_90"],
    }, {
        "metric": "census_pep_target_year", "value": census_pop,
    }, {
        "metric": "census_decennial_2020", "value": decennial_2020,
    }, {
        "metric": "ratio_to_census_pep",
        "value": result["combined"] / census_pop if census_pop else 0.0,
    }]
    if chem_summary and chem_summary.get("bod_pop"):
        national_rows.append({
            "metric": "wastewater_chem_bod_pop_reported",
            "value": chem_summary["bod_pop"],
        })
        national_rows.append({
            "metric": "wastewater_chem_bod_facilities",
            "value": chem_summary.get("bod_facilities", 0),
        })
    national = pd.DataFrame(national_rows)
    paths.append(report.write_national(national))

    estimates = {m: v["central"] for m, v in methods.items()}
    if chem_summary and chem_summary.get("bod_pop"):
        estimates["wastewater_chem"] = chem_summary["bod_pop"]
    disc = discrepancy_report(estimates, census_pop)
    paths.append(report.write_discrepancy(disc))

    lines = [
        "Population Estimator - full run",
        "=" * 60,
        f"Ensemble: {result['combined']:,.0f}",
        f"Bootstrap 90% CI: {boot['lower_90']:,.0f} - {boot['upper_90']:,.0f} "
        f"({boot['n_draws']} draws)",
        f"Census PEP (target year): {census_pop:,.0f}",
        f"Census decennial 2020: {decennial_2020:,.0f}",
    ]
    if census_pop:
        lines.append(f"Ratio to census PEP: "
                     f"{result['combined'] / census_pop:.3f}")
    if chem_summary and chem_summary.get("bod_pop"):
        lines.append(
            "Wastewater chemistry (REPORTED, not ensemble-weighted): "
            f"BOD {chem_summary['bod_pop']:,.0f} from "
            f"{chem_summary.get('bod_facilities', 0)} municipal reporters")
        for key in ("TSS", "Total N", "Ammonia-N"):
            pop = chem_summary.get(f"{key}_pop")
            if pop:
                lines.append(f"  {key} population equivalent: {pop:,.0f}")
    lines += [
        "",
        "Method contributions:",
        report.method_table(methods, result["contributions"]),
        "",
        "County coverage: "
        f"{int((county['n_methods'] > 0).sum())} of {len(county)} counties",
        f"Covered-county population: {county['ensemble_pop'].sum():,.0f}",
    ]
    if notes:
        lines.append("\nNotes:")
        lines.extend(f"  {n}" for n in notes)
    paths.append(report.write_summary(lines))
    return paths


if __name__ == "__main__":
    run()
