# Task Plan: Population Estimator

## Goal
Finish the project per PLAN.md and README promises: a single `popest run`
command that produces county-level estimates with 90% CI, method
contributions, national ensemble with bootstrap uncertainty, and a
discrepancy report against census, with reproducible data downloads and
tests.

## Why it is unfinished (audit 2026-11-18)
- README promises `popest run --year 2024`; no `run` command exists.
- Ensemble is national-only; PLAN.md success criteria require a county
  CSV [FIPS, county, state, estimate, lower_90, upper_90, contributions].
- No bootstrap uncertainty, no hierarchical reconciliation.
- Method B (wastewater chemistry: BOD/N loads) exists only as a scratch
  script chain (process_dmr_fast -> analyze_dmr_loads), never wired into
  the CLI or ensemble.
- 20 overlapping one-off download/extract scripts; CLI `download` points
  at a stale one (download_comprehensive).
- No tests. geopandas/rasterio listed as deps but never imported.
- Fresh clone cannot run: data/ is empty (gitignored), census fetch is
  key-gated only.

## Phases

### Phase 1-7: Original build (2026-07-28)
Status: complete (see progress.md sessions 1-2)

### Phase 8: Environment and packaging
Status: complete
- [x] uv venv, install -e . with light deps
- [x] pyproject: geopandas/rasterio -> optional [geo] extra (never imported)
- [x] pytest dev extra
- [x] repo-local anonymous git identity

### Phase 9: Consolidation
Status: complete
- [x] sources.py: one manifest-driven downloader (core + extended tiers),
      merges all unique URLs from the 8 download_* scripts
- [x] dmr.py: DMR chunked filter + unit-normalized facility loads +
      county crosswalk + municipal SIC filter
- [x] methods/wastewater_chemistry.py: Method B (BOD/N loads -> population)
      with county allocation via ICIS_FACILITIES crosswalk
- [x] census.py: keyless API attempt with fallback
- [x] delete 19 superseded one-off scripts (capability folded; history
      keeps them)
- [x] CLI download -> sources.py; real_data report -> `popest status`

### Phase 10: Pipeline (the actual completion)
Status: complete
- [x] ensemble.py: bootstrap CI over per-capita constant ranges;
      county combine across water/ww-design/ww-chem/housing/census
      (contributions bug found by tests and fixed)
- [x] report.py: output writer (counties.csv, states.csv, national,
      discrepancy, summary)
- [x] pipeline.py: `popest run` orchestration
- [x] cli.py: run/status/chemistry commands; download -> sources.py

### Phase 11: Tests
Status: complete
- [x] tests/test_methods.py: water/wastewater/chemistry math on synthetic data
- [x] tests/test_ensemble.py: combine, bootstrap, reconciliation, census cap
- [x] tests/test_helpers.py: geo validity, constants sanity, DMR filter
- [x] 27 passing

### Phase 12: Verification run (fresh clone, real data)
Status: pending
- [ ] Download core data (USGS, NPDES part1, DMR FY2024, IRS SOI, BLS,
      EIA, EPA MSW, gasoline)
- [ ] ClamAV scan of data/ before parsing
- [ ] `popest run --year 2024` end to end
- [ ] Spot-check outputs against source values

### Phase 13: Documentation and push
Status: pending
- [ ] README: real usage, method-status table, run results
- [ ] SOURCE.md: new module map
- [ ] Planning files updated
- [ ] Commit and push

## Next Step
Phase 8: create venv, install dependencies, set repo-local git identity.

## Decisions Made
- Physical methods get 85% ensemble weight, census capped at 15%
- Per-capita constants are calibration knobs with published ranges
- Water/wastewater are hardest-to-fake (biological constants)
- County allocation of DMR loads via permit->facility county crosswalk
  (ICIS_FACILITIES from NPDES part 1 zip)
- Counties with no method data get blank estimates, never invented values
- National-only methods feed the national ensemble only; the county CSV
  reports per-county coverage honestly
- Bootstrap CI: per-capita constants resampled uniformly in published
  ranges (Method: PLAN.md Phase 6)
- Reconciliation: county -> state -> national sums reported; coverage
  share stated, no fabricated fills
- Census API used keyless when possible; national-total fallback retained
- git author: operator / noreply@localhost (anonymous, consistent with
  prior dev@localhost history)

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (sessions 1-2: none recorded) | | |
