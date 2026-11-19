# SOURCE.md - Module Documentation

## Overview

Population Estimator: multi-source estimation of the true US population
using physical infrastructure as primary evidence. Census data is one
input among many, capped at 15% ensemble weight.

Run `popest run` for the full pipeline. Each method cites its own data
year; the target year labels the run.

## Module Map

### Data Clients (fetch + parse external data)

| Module | Function | Source |
|--------|----------|--------|
| `water.py` | County-level water withdrawals | USGS ScienceBase 2015 |
| `wastewater.py` | Municipal WWTP design flows | EPA ICIS-NPDES zip (332 MB) |
| `dmr.py` | Per-facility BOD/TSS/N loads, county crosswalk, municipal SIC filter | EPA DMR FY2024 zip (612 MB) + ICIS_FACILITIES |
| `sdwis.py` | Community water system population served (active CWS) | EPA SDWA system search zip (35 MB) |
| `education.py` | Public K-12 enrollment, NSLP, WIC | NCES CCD 2024-25 zip; USDA FNS XLSX |
| `medicare.py` | Aged Medicare beneficiaries | data.cms.gov public CSV (DNS-blocked on some resolvers) |
| `sources.py` | Canonical manifest downloader (core + tiers 1-5) | all URLs from former download_* scripts and subagent sweeps |
| `energy.py` | State residential electricity (ESRCP) and natural gas (NGRCP) | EIA SEDS Complete_SEDS.csv, Vintage 2024F |
| `waste.py` | MSW, gasoline, VMT (FHWA VM-1), LMOP landfill acceptance, vehicles | EPA HTML / EIA CSV / FHWA XLSX |
| `healthcare.py` | ER visits, physician visits, discharges | CDC NCHS/AHRQ published totals |
| `census.py` | County PEP comparison + 2020 PL population/housing | PEP Vintage 2024 bulk CSV (no key); PL via key or national fallback |
| `vitals.py` | Births/deaths | CDC WONDER attempt, NCHS fallback |
| `consumption.py` | SNAP, wireless, grocery | USDA/CTIA/census published totals |
| `irs.py` | Tax returns + exemptions | IRS SOI ZIP CSV (206 MB) |
| `bls.py` | Employment, labor force | BLS API JSON |
| `buildings.py` | Building footprint counts + recount utility | MS USBuildingFootprints GeoJSON |
| `real_data.py` | `popest status`: which numbers come from downloaded files | data/ contents |
| `verify_downloads.py` | `popest verify`: file sanity | data/ contents |

### Estimation Methods (apply per-capita constants)

| Module | Method | Granularity |
|--------|--------|-------------|
| `methods/water_budget.py` | A: Water budget | County |
| `methods/wastewater.py` | B1: WWTP design flow | County |
| `methods/wastewater_chemistry.py` | B2: Monitored BOD loads (DMR) | County |
| `methods/energy.py` | C: Residential electricity | State |
| `methods/waste_food.py` | D: MSW/gasoline/vehicles/VMT | National |
| `methods/healthcare.py` | E: Healthcare utilization | National |
| `methods/housing.py` | G: Housing units | County |
| `methods/vitals.py` | Births/deaths rates | National |
| `methods/buildings.py` | Building count x occupancy | National |
| `methods/education.py` | K-12 enrollment share | National |
| `methods/sdwis.py` | CWS served / coverage fraction | National |
| `methods/medicare.py` | Aged beneficiaries / aged share | National |

### Combination and Output

| Module | Function |
|--------|----------|
| `ensemble.py` | National weighted combine (census capped 15%), county ensemble with contributions, state rollup |
| `uncertainty.py` | Bootstrap 90% CI: per-capita constants resampled in published ranges |
| `reconcile.py` | Implied constants at claimed population levels vs published ranges |
| `pipeline.py` | `popest run`: all methods fail-soft, combine, write outputs |
| `national.py` | National-only method collectors |
| `runners.py` | Single-method CLI commands |
| `report.py` | Output writers (counties/states/national/discrepancy/reconciliation/summary) |
| `discrepancy.py` | Per-method gap vs census |
| `sensitivity.py` | Per-capita constant sensitivity table |
| `constants.py` | All per-capita rates with uncertainty ranges |
| `geo.py` | FIPS codes, state mappings |
| `config.py` | YAML config loader |
| `cli.py` | Entry point, subcommand dispatch |

## Data Flow

```
popest download -> data/ (gitignored)
popest run -> methods (fail-soft) -> ensemble + bootstrap
           -> output/counties.csv, states.csv, national.csv,
              discrepancy_report.csv, summary.txt
```

## Key Design Decisions

1. Physical methods (water, wastewater flow, energy) get the highest
   ensemble weights; census capped at 15%
2. Bootstrap samples per-capita constants uniformly in published ranges;
   the closed-form sampler in `uncertainty.py` is exact for
   single-constant methods
3. Wastewater chemistry counts only SIC 4952 (municipal) facilities, so
   industrial loads do not inflate the population
4. Wastewater chemistry is REPORTED but never ensemble-weighted: its
   mass-unit reporters are a subset (4,046 of ~30,121 municipal plants),
   so it is a coverage-limited lower bound, not a total
5. Counties with no method data get blank estimates (n_methods 0),
   never invented values
6. A failed source drops that method's voice; the run never dies
7. EPA NPDES data has mixed flow units; heuristic correction applied in
   `wastewater.py` (values > 100 treated as gal/day)
8. IRS SOI rows with zipcode 00000/99999 are state totals and excluded
   (they double the counts)
9. Residential electricity constant is per person (~4,200 kWh from RECS
   10,500 kWh per household / ~2.5 per household), fixing the prior
   per-household mislabel

## Historical note

The 19 one-off download/extract/DMR scripts from the exploration phase
(download_all, download_everything, process_dmr, analyze_dmr_loads,
scraper, count_buildings, etc.) were consolidated into `sources.py`,
`dmr.py`, `buildings.py`, and `real_data.py`. They remain in git history.

## Output Files

Written to `output/` by `popest run`:
- `counties.csv` — per-county ensemble, endpoints, contributions
- `states.csv` — state rollup of covered counties
- `national.csv` — ensemble, bootstrap 90% CI, census comparison
- `discrepancy_report.csv` — every method vs census
- `reconciliation.csv` — implied constants at each claimed population
- `summary.txt` — human-readable report

Single-method commands save per-method CSVs (`water_budget_2015.csv`,
`wastewater_flow.csv`, `wastewater_chemistry.csv`, `energy_electricity.csv`,
`waste_food_vehicle.csv`, `healthcare.csv`, `housing.csv`, `buildings.csv`,
`sensitivity.csv`).
