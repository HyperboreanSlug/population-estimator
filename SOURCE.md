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
| `sources.py` | Canonical manifest downloader (core + tiers 1-5) | all URLs from former download_* scripts |
| `energy.py` | State electricity/gas consumption | EIA SEDS constants (2022) |
| `waste.py` | MSW, gasoline, vehicles | EPA HTML / EIA CSV / FHWA |
| `healthcare.py` | ER visits, physician visits, discharges | CDC NCHS/AHRQ published totals |
| `census.py` | County population + housing units | Census 2020 PL API (keyless) with national fallback |
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
| `methods/waste_food.py` | D: MSW/gasoline/vehicles | National |
| `methods/healthcare.py` | E: Healthcare utilization | National |
| `methods/housing.py` | G: Housing units | County |
| `methods/vitals.py` | Births/deaths rates | National |
| `methods/buildings.py` | Building count x occupancy | National |

### Combination and Output

| Module | Function |
|--------|----------|
| `ensemble.py` | National weighted combine (census capped 15%), county ensemble with contributions, state rollup |
| `uncertainty.py` | Bootstrap 90% CI: per-capita constants resampled in published ranges |
| `pipeline.py` | `popest run`: all methods fail-soft, combine, write outputs |
| `runners.py` | Single-method CLI commands |
| `report.py` | Output writers (counties/states/national/discrepancy/summary) |
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

1. Physical methods (water, wastewater flow, wastewater chemistry) get
   the highest ensemble weights; census capped at 15%
2. Bootstrap samples per-capita constants uniformly in published ranges;
   the closed-form sampler in `uncertainty.py` is exact for
   single-constant methods
3. Wastewater chemistry counts only SIC 4952 (municipal) facilities, so
   industrial loads do not inflate the population
4. Counties with no method data get blank estimates (n_methods 0),
   never invented values
5. A failed source drops that method's voice; the run never dies
6. EPA NPDES data has mixed flow units; heuristic correction applied in
   `wastewater.py` (values > 100 treated as gal/day)

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
- `summary.txt` — human-readable report

Single-method commands save per-method CSVs (`water_budget_2015.csv`,
`wastewater_flow.csv`, `wastewater_chemistry.csv`, `energy_electricity.csv`,
`waste_food_vehicle.csv`, `healthcare.csv`, `housing.csv`, `buildings.csv`,
`sensitivity.csv`).
