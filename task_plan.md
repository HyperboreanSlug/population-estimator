# Task Plan: Population Estimator

## Goal
Implement Phase 1: Water budget + wastewater chemistry population estimates.
Physical infrastructure primary. Census demoted to comparison.

## Phases

### Phase 1: Infrastructure + Water/Wastewater
Status: in_progress
- [x] Project scaffolding (PLAN.md, README, pyproject.toml)
- [x] Package structure (src/popest/)
- [x] constants.py — per-capita rates with uncertainty
- [x] geo.py — FIPS codes, county list
- [x] water.py — USGS ScienceBase client (2015 county data)
- [x] methods/water_budget.py — Method A (WORKING: 356M central)
- [x] wastewater.py — EPA NPDES client (301 MB download)
- [x] methods/wastewater.py — Method B (code ready, needs data download)
- [x] cli.py — entry point with water + wastewater commands
- [ ] Run wastewater method (requires 301 MB EPA download)
- [ ] Cross-check water vs wastewater estimates

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
