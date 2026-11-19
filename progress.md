# Progress

## Session 1 — 2026-07-28
- Created project, PLAN.md, README, pyproject.toml
- Created private GitHub repo: HyperboreanSlug/population-estimator
- Revised plan: physical infrastructure primary, census demoted
- Starting Phase 1 implementation

## Session 2 — 2026-07-28 (continued)
- Implemented package structure (src/popest/)
- Water budget method WORKING: 356M central (vs USGS 321M, +10.8%)
- Wastewater method WORKING: 563M central (+70% vs census)
- Energy method: 279M central (-15.7% vs census)
- MSW: 327M, Gasoline: 344M, Vehicles: 427M
- Healthcare: 325M central
- Housing: 321M central
- ENSEMBLE COMBINED: 375M (+13.3% vs census 331M)
- All 7 phases complete
- SOURCE.md written
- All code committed and pushed

## Session 3 — 2026-11-18
- Audited repo: phases 1-7 done, but README `popest run` missing, ensemble
  national-only, Method B unintegrated, download sprawl (20 scripts), no
  tests, heavy unused deps.
- Completion plan written (phases 8-13).
- Session 3 continued: fixed IRS double-count, energy data+constant,
  span inversions, county 00000 row; chemistry reported-not-weighted.
- Verification: 29 tests pass; full run 10.7s warm; outputs verified
  (3,159 counties, contributions sum 1.0, states rollup equals county
  sum). Ensemble 358,571,850 (CI 331.6M-382.6M), ratio 1.054 vs PEP.
- README results + method-status table written; docs updated; pushed.
- Phase 14: two verified DeepSeek-flash sweeps; wired education (NCES),
  sdwis (active CWS 331.9M served), VMT (FHWA 2024), real SNAP FY2025,
  medicare (fail-soft, DNS), LMOP/TTB/NSLP/WIC/VM-1-vehicles reported
  voices; BLS denominator fix; reconcile.py with 15-16 constant rows.
- 36 tests passing. Ensemble 360,979,127 (CI 338.1-380.8M), ratio 1.061
  vs PEP 2024. 450M claim: 12/15 constants break; 500M: 14/15.
- Medicare voice live via VPS-proxied download (operator-authorized
  ssh), dlgate PASS, parse fixed for month names; ensemble 361.8M.
  FCC: no subscriptions dataset exists on opendata (verified through
  the same tunnel); CTIA constant documented as the only source.
- Phase 15 complete: 27 national voices + 4 county voices, 28 core
  files. Ensemble 356,412,430 (CI 338.3M-370.3M), ratio 1.048.
  Reconciliation: 27 constants; 450M breaks 21, 500M breaks 25. All
  committed and pushed.
- VPS batch complete: Medicaid enrollment voice (72.95M -> 339.3M),
  hospital inpatient days voice (190.0M -> 339.3M), SDUD prescriptions
  reported (596.3M Rx). SSA blocked from workstation AND VPS
  (datacenter-IP 403). Final: 31 voices, ensemble 355,562,959 (CI
  337.4M-371.7M), ratio 1.045; reconciliation 31 constants, 450M
  breaks 25/31, 500M breaks 29/31. All pushed.
