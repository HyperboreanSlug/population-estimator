# Task Plan: Population Estimator

## Goal
Implement Phase 1: Water budget + wastewater chemistry population estimates.
Physical infrastructure primary. Census demoted to comparison.

## Phases

### Phase 1: Infrastructure + Water/Wastewater
Status: complete
- [x] Project scaffolding (PLAN.md, README, pyproject.toml)
- [x] Package structure (src/popest/)
- [x] constants.py — per-capita rates with uncertainty
- [x] geo.py — FIPS codes, county list
- [x] water.py — USGS ScienceBase client (2015 county data)
- [x] methods/water_budget.py — Method A (356M central)
- [x] wastewater.py — EPA NPDES client (332 MB download)
- [x] methods/wastewater.py — Method B (563M central)
- [x] cli.py — entry point

### Phase 2: Energy and Waste
Status: complete
- [x] energy.py — EIA state electricity data
- [x] waste.py — EPA MSW, USDA food, EIA gasoline, FHWA vehicles
- [x] methods/energy.py — Method C (279M central)
- [x] methods/waste_food.py — Method D (327-427M)

### Phase 3: Healthcare and Consumption
Status: complete
- [x] healthcare.py — CDC NCHS / AHRQ utilization data
- [x] methods/healthcare.py — Method E (325M central)

### Phase 4: Housing, Vehicles, Geospatial
Status: complete
- [x] census.py — Census API client with fallback
- [x] methods/housing.py — Method G (321M central)

### Phase 5: Census Comparison
Status: complete
- [x] discrepancy.py — per-method gap vs census
- [x] Discrepancy report generated

### Phase 6: Ensemble and Output
Status: complete
- [x] ensemble.py — precision-weighted combination
- [x] Census capped at 15% weight
- [x] Combined estimate: 375M (+13.3% vs census)

### Phase 7: Validation and Sensitivity
Status: complete
- [x] sensitivity.py — per-capita constant sensitivity table
- [x] SOURCE.md — module documentation
- [x] All results documented

## Next Step
Create package scaffolding and constants.py

## Decisions Made
- Physical methods get 85% ensemble weight, census capped at 15%
- Per-capita constants are calibration knobs with published ranges
- Water/wastewater are hardest-to-fake (biological constants)

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (none yet) | | |
