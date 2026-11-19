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
    try:
        from popest import dmr
        from popest.methods.wastewater_chemistry import estimate, national_summary

        loads = dmr.facility_loads(dmr.filter_dmr())
        cmap = dmr.facility_county_map()
        muni = dmr.municipal_permit_ids()
        chem_c = estimate(loads, cmap, muni)
        cs = national_summary(chem_c, loads, muni)
        methods["wastewater_chem"] = {
            "central": cs.get("bod_pop", 0.0),
            "low": float(chem_c["pop_chem_low"].sum()) if not chem_c.empty else 0.0,
            "high": float(chem_c["pop_chem_high"].sum()) if not chem_c.empty else 0.0,
            "form": "inverse",
            "source": (f"EPA DMR BOD loads, {cs.get('bod_facilities', 0)} "
                       "municipal reporters"),
        }
        chem_c = chem_c.rename(columns={
            "pop_chem_central": "pop_wastewater_chem_central",
            "pop_chem_low": "pop_wastewater_chem_low",
            "pop_chem_high": "pop_wastewater_chem_high",
        })
        county_dfs["wastewater_chem"] = chem_c
        print(f"  BOD population {cs.get('bod_pop', 0):,.0f} "
              f"({cs.get('bod_facilities', 0)} facilities)")
        for key in ("TSS", "Total N", "Ammonia-N"):
            if f"{key}_pop" in cs:
                print(f"  {key} population {cs[f'{key}_pop']:,.0f}")
    except Exception as e:
        notes.append(f"wastewater_chem FAILED: {e}")
        print(f"  FAILED: {e}")

    step("[4/12] Housing units (census 2020)...")
    try:
        from popest.methods.housing import estimate, national_summary

        housing = estimate(api_key)
        if not housing.empty and (housing["fips"].str.len() == 5).any():
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
    step("[6/12] Energy (EIA residential electricity)...")
    _add_national(methods, "energy", _energy, "low", "high")

    step("[7/12] Waste/food/vehicles...")
    _add_national_multi(methods, _waste_food, {
        "msw": ("msw", "inverse", "EPA MSW 2018"),
        "gasoline": ("gasoline", "inverse", "EIA gasoline"),
        "vehicles": ("vehicles", "inverse", "FHWA registrations 2022"),
    })

    step("[8/12] Healthcare utilization...")
    _add_national(methods, "healthcare", _healthcare, "low", "high")

    step("[9/12] Vitals (births/deaths)...")
    _add_national(methods, "vitals", _vitals, "low", "high")

    step("[10/12] Consumption (SNAP/wireless/grocery)...")
    _add_national_multi(methods, _consumption, {
        "snap": ("snap", "inverse", "USDA FNS SNAP 2023"),
        "wireless": ("wireless", "inverse", "CTIA survey 2023"),
        "grocery": ("grocery", "inverse", "census retail 2023"),
    })

    step("[11/12] IRS filers / BLS employment...")
    _add_national(methods, "irs", _irs, "low", "high")
    _add_national(methods, "bls", _bls, "low", "high")

    step("[12/12] Building footprints...")
    _add_national(methods, "buildings", _buildings, "low", "high")

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

    # --- outputs -------------------------------------------------------
    paths = _write_outputs(county, names, states, result, boot, census_pop,
                           methods, notes, decennial_2020)
    print("\n  Outputs:")
    for p in paths:
        print(f"    {p}")
    return {
        "combined": result["combined"], "bootstrap": boot,
        "contributions": result["contributions"], "census": census_pop,
        "counties": county, "states": states, "notes": notes,
    }


def _add_national(methods: dict, name: str, fn, low_key: str, high_key: str) -> None:
    try:
        entry = fn()
        if entry and entry.get("central", 0) > 0:
            methods[name] = entry
            print(f"  central {entry['central']:,.0f}")
        else:
            print(f"  no data ({name})")
    except Exception as e:
        print(f"  FAILED: {e}")


def _add_national_multi(methods: dict, fn, spec: dict) -> None:
    try:
        results = fn()
        for name, (key, form, source) in spec.items():
            central = results.get(f"{key}_central", 0)
            if central > 0:
                methods[name] = {
                    "central": central,
                    "low": results.get(f"{key}_low", central),
                    "high": results.get(f"{key}_high", central),
                    "form": form, "source": source,
                }
                print(f"  {name}: {central:,.0f}")
            else:
                print(f"  no data ({name})")
    except Exception as e:
        print(f"  FAILED: {e}")


def _energy() -> dict:
    from popest.methods.energy import estimate, national_summary

    s = national_summary(estimate())
    if not s or s.get("central", 0) <= 0:
        return {}
    return {"central": s["central"], "low": s["low"], "high": s["high"],
            "form": "inverse", "source": "EIA SEDS residential kWh 2022"}


def _waste_food() -> dict:
    from popest.methods.waste_food import estimate

    return estimate()


def _healthcare() -> dict:
    from popest.methods.healthcare import estimate

    r = estimate()
    return {"central": r["er_central"], "low": r["er_low"],
            "high": r["er_high"], "form": "inverse",
            "source": "CDC NCHS ER visits 2021"}


def _vitals() -> dict:
    from popest.methods.vitals import estimate

    r = estimate()
    return {"central": r["births_central"], "low": r["births_high"],
            "high": r["births_low"], "form": "inverse",
            "source": "CDC NCHS births 2022"}


def _consumption() -> dict:
    from popest.consumption import estimate_consumption

    return estimate_consumption()


def _irs() -> dict:
    from popest.irs import estimate_from_irs

    r = estimate_from_irs()
    if "error" in r:
        raise RuntimeError(r["error"])
    return {"central": r["irs_central"], "low": r["irs_high"],
            "high": r["irs_low"], "form": "inverse",
            "source": "IRS SOI exemptions TY2022"}


def _bls() -> dict:
    from popest.bls import estimate_from_bls

    r = estimate_from_bls()
    if "error" in r:
        raise RuntimeError(r["error"])
    return {"central": r["bls_central"], "low": r["bls_low"],
            "high": r["bls_high"], "form": "inverse",
            "source": "BLS employment (API)"}


def _buildings() -> dict:
    from popest.buildings import estimate_from_buildings

    r = estimate_from_buildings()
    return {"central": r["buildings_central"], "low": r["buildings_low"],
            "high": r["buildings_high"], "form": "direct",
            "source": "MS building footprints (5 states verified)"}


def _write_outputs(county, names, states, result, boot, census_pop,
                   methods, notes, decennial_2020=0.0) -> list:
    paths = [
        report.write_counties(county, names),
        report.write_states(states),
    ]

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
    national = pd.DataFrame(national_rows)
    paths.append(report.write_national(national))

    disc = discrepancy_report(
        {m: v["central"] for m, v in methods.items()}, census_pop)
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
