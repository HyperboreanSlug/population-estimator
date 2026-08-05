# SOURCE.md - Module Documentation

## Overview

Population Estimator: multi-source estimation of true US population using
physical infrastructure as primary evidence. Census data is one input among
many, capped at 15% ensemble weight.

## Module Map

### Data Clients (fetch + parse external data)

| Module | Function | Source |
|--------|----------|--------|
| `water.py` | County-level water withdrawals | USGS ScienceBase 2015 |
| `wastewater.py` | Municipal WWTP design flows | EPA ICIS-NPDES (332 MB) |
| `energy.py` | State electricity/gas consumption | EIA (hardcoded 2022) |
| `waste.py` | MSW, food, gasoline, vehicles | EPA/USDA/EIA/FHWA |
| `healthcare.py` | ER visits, physician visits, discharges | CDC NCHS/AHRQ |
| `census.py` | Census population + housing units | Census API (or fallback) |

### Estimation Methods (apply per-capita constants)

| Module | Method | Granularity |
|--------|--------|-------------|
| `methods/water_budget.py` | A: Water budget | County |
| `methods/wastewater.py` | B: WWTP design flow | County |
| `methods/energy.py` | C: Residential electricity | State |
| `methods/waste_food.py` | D: MSW/gasoline/vehicles | National |
| `methods/healthcare.py` | E: Healthcare utilization | National |
| `methods/housing.py` | G: Housing units | National |

### Analysis and Output

| Module | Function |
|--------|----------|
| `ensemble.py` | Precision-weighted combination, census capped 15% |
| `discrepancy.py` | Per-method gap vs census |
| `sensitivity.py` | Per-capita constant sensitivity table |
| `constants.py` | All per-capita rates with uncertainty ranges |
| `geo.py` | FIPS codes, state mappings |
| `config.py` | YAML config loader |
| `cli.py` | Entry point, all subcommands |

## Data Flow

```
External sources → data clients → estimation methods → ensemble → output/
                                                        ↓
                                              discrepancy report
```

## Key Design Decisions

1. Physical methods (water, wastewater) get highest ensemble weight
2. Census capped at 15% regardless of internal precision
3. Per-capita constants are calibration knobs with published ranges
4. EPA wastewater data has mixed units — heuristic correction applied
5. Census API optional — falls back to hardcoded national totals

## Output Files

All written to `output/`:
- `water_budget_2015.csv` — county water estimates
- `wastewater_flow.csv` — county wastewater estimates
- `energy_electricity.csv` — state electricity estimates
- `waste_food_vehicle.csv` — national waste/food/vehicle
- `healthcare.csv` — national healthcare
- `housing.csv` — national housing
- `discrepancy_report.csv` — all methods vs census
- `sensitivity.csv` — constant sensitivity table
