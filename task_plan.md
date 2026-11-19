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
Status: complete
- [x] Download core data (USGS, NPDES part1, DMR FY2024, IRS SOI, BLS,
      EIA incl. SEDS complete, EPA MSW, gasoline, census PEP counties)
- [x] ClamAV scan of data/ before parsing (0 infected, 1,169 MB)
- [x] `popest run --year 2024` end to end (10.7s warm, 50s cold)
- [x] Spot-check outputs against source values
- [x] Accuracy fixes found by the run: IRS state-total row double-count,
      energy data mislabeled residential+commercial with a per-household
      constant, vitals/buildings range inversions, housing national row
      leaking into the county ensemble, chemistry subset numerator
      weighted as a total

### Phase 13: Documentation and push
Status: complete
- [x] README: real usage, method-status table, run results
- [x] SOURCE.md: new module map + design decisions
- [x] PLAN.md: structure section + electricity constant corrected
- [x] Planning files updated
- [x] Commit and push

## Next Step
Complete: all phases finished. See progress.md session 3.

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
| Census 2020 PL keyless returns HTML "Missing Key" (HTTP 200) | 1 | PEP Vintage 2024 county CSV as keyless comparison source |
| Census PEP national file URL 404 (vintage rolled over) | 2 | county file subsumes it; URL removed from manifest |
| EIA SEDS/861 old URLs now HTML error pages | 3 | found current CDF/Complete_SEDS.csv from the SEDS page; MSN codes ESRCP/NGRCP |
| clamscan scanned 0 bytes | 1 | system DB path empty; pass --database=$HOME/.local/share/clamav |
| IRS SOI N2 double-counted (zipcode 00000 state-total rows) | 1 | exclude zipcode 00000/99999 |
| Energy constant 10,500 kWh/person was per HOUSEHOLD | 1 | RECS chain: 10,500 kWh/household / ~2.5 = 4,200 kWh/person; data moved to real SEDS ESRCP |
| Energy dict summed 2,934 BkWh but docstring said 1,509 (residential+commercial mislabeled) | 1 | replaced with parsed ESRCP state series |
| Vitals/buildings low-high spans inverted in pipeline/methods | 1 | corrected mappings |
| Housing national fallback row (fips 00000) entered county ensemble | 1 | valid-FIPS guard in combine_county |
| Chemistry subset numerator weighted in ensemble (dragged -28M) | 1 | reported but unweighted; documented |

### Phase 14: Source expansion and reconciliation (user order 2026-11-18)
Status: in_progress
- [ ] Two DeepSeek-flash sweeps for bulk URLs: education/health/admin,
      consumption/infrastructure
- [ ] Wire new real-data methods: K-12 enrollment, Medicare enrollment,
      SDWIS population served, SNAP real participants, food availability
      calories, VMT, FCC subscriptions, TTB (whichever return usable
      bulk files)
- [ ] reconcile.py: implied per-capita constants at 340.1M / 450M / 500M
      vs published ranges, per PLAN.md discrepancy methodology
- [ ] EIA natural gas (NGRCP, already parsed) as a meter-count voice
- [ ] Rerun, document, push

### Phase 14 outcome (2026-11-18)
Status: complete
- [x] Sweeps: education/health (NCES, SDWIS, SNAP, NSLP/WIC found; CMS
      DNS-blocked, reported) and consumption/infrastructure (VMT, LMOP,
      TTB found; ERS circular+stale, FCC DNS-blocked, CWNS SSO-gated)
- [x] New weighted methods: education, sdwis, vmt, snap real, medicare
      (fail-soft); BLS denominator correction
- [x] reconcile.py: implied constants at 340.1M/361M/400M/450M/500M
- [x] Reported-only voices: chemistry, LMOP, TTB, NSLP/WIC, VM-1 vehicles
- [x] 36 tests passing; README results + reconciliation section; pushed

### Phase 15: Wire all remaining sources (user order 2026-11-19)
Status: in_progress
- [ ] On-disk five: PEP births/deaths (vitals real data), IRS AGI voice,
      EIA total energy voice, NGRCP gas volume voice, Medicare county
      voice into the county ensemble
- [ ] URL hunt (subagent): EIA-861 meters, EIA-176 gas customers,
      TSA/FAA enplanements, NTD transit, SSA OASDI, IPEDS, ERS food
      expenditure, IMLS, USFWS licenses, HUD USPS, BEA PCE
- [ ] Wire each verified source: client + method + constants + weights
- [ ] GHSL as reported-only (census-trained satellite, validation-only
      per PLAN.md); WONDER superseded by PEP NCHS-derived columns
- [ ] Rebalance ensemble + county weights; extend reconciliation rows
- [ ] Tests, full run, docs, push
