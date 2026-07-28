# Task Plan: Population Estimator

## Goal
Implement Phase 1: Water budget + wastewater chemistry population estimates.
Physical infrastructure primary. Census demoted to comparison.

## Phases

### Phase 1: Infrastructure + Water/Wastewater
Status: in_progress
- [x] Project scaffolding (PLAN.md, README, pyproject.toml)
- [ ] Package structure (src/popest/)
- [ ] constants.py — per-capita rates with uncertainty
- [ ] geo.py — FIPS codes, county list
- [ ] water.py — USGS National Water Use client
- [ ] methods/water_budget.py — Method A
- [ ] methods/wastewater.py — Method B (EPA NPDES)
- [ ] cli.py — entry point
- [ ] Verify national estimate

### Phase 2: Energy and Waste
Status: pending

### Phase 3: Healthcare and Consumption
Status: pending

### Phase 4: Housing, Vehicles, Geospatial
Status: pending

### Phase 5: Census Comparison
Status: pending

### Phase 6: Ensemble and Output
Status: pending

### Phase 7: Validation and Sensitivity
Status: pending

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
