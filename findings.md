# Findings

## USGS National Water Use Data
- URL: https://waterdata.usgs.gov/nwis/wu
- Bulk download by state: https://waterdata.usgs.gov/{state_code}/nwis/water_use
- Format: tab-delimited, county-level
- Key category: "Public Supply" (PS) = municipal water systems
- Fields: county FIPS, year, PS freshwater withdrawals (Mgal/d)
- Available years: 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020
- National total PS withdrawals 2020: ~39,000 Mgal/d (needs verification)

## EPA NPDES / ECHO
- API: https://echo.epa.gov/api/
- Facility search: https://echo.epa.gov/api/facility/search
- Bulk data: https://www.epa.gov/echo/download-export-data
- ICIS-NPDES discharge monitoring reports (DMRs)
- Pollutants: Total Nitrogen (00670), Ammonia-N (00608), BOD (00310), TSS (00530)
- Units: lbs/day for loads, MGD for flow

## Per-Capita Constants (literature)
- Domestic water use: 80-100 gal/person/day (EPA, AWWA)
- Wastewater flow: 60-110 gal/person/day (Metcalf & Eddy)
- Total nitrogen: 9-14 g N/person/day (EPA design manuals)
- Ammonia-N: 4-7 g/person/day
- BOD5: 55-90 g/person/day (standard: 60-80)
- TSS: 8-18 g/person/day

## Code inventory (audit 2026-11-18)
- 20 one-off scripts in src/popest: download_{all,accessible,comprehensive,
  everything,final,fix,retry}.py, fix_downloads.py, extract_{all_real,data,
  real,irs}.py, process_dmr{,_fast}.py, analyze_dmr_loads.py, audit_files.py,
  check_files.py, count_buildings.py, scraper.py. All same-family dev-era
  scripts; unique URLs collected for the canonical manifest.
- geopandas/rasterio listed in pyproject but never imported anywhere.
- CLI has no `run` command (README promises `popest run --year 2024`).
- ensemble.combine_county exists but is never called; no CI, no
  reconciliation, census cap logic duplicated.
- Method B (chemistry) never integrated: process_dmr_fast filters DMR zip to
  data/epa/dmr_nitrogen_bod_filtered.csv, analyze_dmr_loads computes BOD
  pop (83.5M from 5,607 facilities lb/d per git log) but only prints.
- census.py requires an API key for county data; keyless returns only the
  hardcoded national row. Census 2020 PL endpoint allows keyless use.
- irs.py, bls.py, waste.py read real downloaded files under data/ (all
  gitignored): soi_zip_2022.csv (206MB), total_employed.json,
  msw_national_overview.html, gasoline_weekly.csv.
- Git history author: dev <dev@localhost> (anonymous already).
- Real-data gaps confirmed by real_data.py report: CDC natality CSV is
  surveillance not vital stats; SNAP/CTIA/CMS/census-retail/AHRQ/NCES pages
  are app shells with no extractable numbers. Healthcare method stays on
  published NCHS/HCUP constants.

## Session 3 discoveries
- Census API now requires a key for the 2020 PL county endpoint (returns
  HTML "Missing Key" page with HTTP 200). Keyless bulk replacement: PEP
  Vintage 2024 county CSV (co-est2024-alldata.csv, latin-1), 3,144
  counties + 51 states, POPESTIMATE2020-2024, BIRTHS/DEATHS/GQ columns.
  PEP 2024 national sum: 340,110,988 (field POPESTIMATE2024, SUMLEV 50).
- No housing-unit columns in the PEP county file; county housing needs
  the key-gated census API, so housing runs at national granularity
  without a key.
- Census PEP national file URL 404s (vintage rolled over); the county
  file's state rows subsume it. Manifest carries the county file only.
- DMR zip first entry is the FY2024 CSV; chunked filter at 500k rows
  keeps the target parameters only.
- Machine download gate blocks interactive curl (correct); all data
  comes through the project's own downloader.

## Accuracy fixes forced by the verification run (2026-11-18)
- IRS SOI 22zpallagi.csv: zipcode 00000 rows are state totals (N2
  288.4M) plus 99999 unknown rows; real per-ZIP exemptions N2 = 284.3M.
  Without the filter the method claimed 655M people.
- energy.py hardcoded dict summed 2,934.5 BkWh (residential+commercial)
  while claiming residential ~1,509 BkWh, divided by 10,500 kWh which is
  EIA's per-HOUSEHOLD figure. Two errors roughly cancelled into the old
  279M. Replaced with real SEDS series ESRCP (2024: 1,482.9 BkWh across
  51 states) and constant 4,200 kWh/person (RECS: 10,500 kWh/household
  / ~2.5 people/household). Energy now lands 353.1M.
- Vitals (pipeline mapping) and buildings (module labels) had inverted
  low/high spans; tests now cover span ordering.
- combine_county accepted the housing national fallback row (fips 00000)
  as a county, inflating the covered sum by 321M. Valid-FIPS guard added.
- Wastewater chemistry: 4,046 municipal mass-unit reporters vs 30,121
  plants with design flows. The load numerator is a reporting subset,
  so the voice is reported (county columns, national.csv, discrepancy)
  but carries no ensemble weight. BOD pop 17.6M, TSS pop 208.6M.
- Final verified run: ensemble 358,571,850 (CI 331.6M-382.6M, 1000
  draws), census PEP 2024 340,110,988, ratio 1.054. Spot checks exact:
  IRS 284,291,130/0.88 = 323,058,102; energy 1,482.9e9/4200 = 353.07M;
  vitals 3,667,758 births at 11/1000 = 333,432,545; housing
  140,498,736 x 0.87 x 2.6 x 1.025 = 321,320,609; census PEP
  340,110,988 matches co-est2024-alldata.csv POPESTIMATE2024 SUMLEV 50.

## User order (2026-11-18, session 3 continued)
Review data sources; pull in every additional bulk source findable; the
user reports multiple people claiming the true population is 450M+. The
hypothesis space in PLAN.md explicitly includes 500M+. Method: do NOT
tune constants toward any target; add real sources; run PLAN.md's own
reconciliation analysis (which per-capita constants a 450M/500M figure
would require, and whether they sit inside published ranges).

## Source audit vs PLAN.md 38-source catalog (wired status)
- Wired, real data: USGS water (1), NPDES design flow (2), EIA SEDS
  electricity (5, now real), EPA MSW (7, page), gasoline (9), FHWA
  vehicles (10), IRS SOI (29), BLS (32), DMR chemistry (reported), PEP
  (27), decennial (26), SEDS natural gas (20, file parsed, unwired).
- Wired, literature constants only: healthcare (11-14,16), grocery (18),
  CTIA wireless (21), SNAP (25), housing units+census (28 partial).
- Not wired with real bulk data (candidates for expansion): SDWIS
  population served (23), school lunch/WIC (24), NCES enrollment (31),
  CMS Medicare (30), USDA food availability (8, currently None),
  VMT/FHWA, FCC subscriptions, TTB alcohol, CWNS facility data (3),
  DHS/CBP flows (33/34, stock-inapplicable), VIIRS/WorldPop (35/38,
  model-circular, validation only).
- Voice that contradicts 450M+ hard: IRS exemptions (284.3M) would need a
  37% non-filer rate (published 8-18%); vehicles 283.4M would need 0.63
  per adult (published 0.75-1.0); electricity 1,483 BkWh would need
  3,296 kWh/person (RECS-derived range 3,500-5,200). Gasoline is the
  most compatible: 134B gal -> 298 gal/person at 450M, at the low edge
  of the published 300-500 range.

## Subagent sweep 1 (education/health/admin) 2026-11-18, verified URLs
- NCES public K-12 2024-25: nces.ed.gov/ccd/Data/zip/ccd_sea_052_2425_l_1a_073025.zip
  (310KB; STUDENT_COUNT; "Education Unit Total" rows sum 49,573,761
  computed by the sweep, CA 5.81M, TX 5.55M). Digest national fall 2023:
  49,516,361 (tabn203.10). Census circularity: enrollment-share constant
  is census-informed; modest weight.
- SDWIS: echo.epa.gov/files/echodownloads/SDWA_system_search_download.zip
  (35MB, SDWA_SYSTEM_SEARCH.csv, POPULATION_SERVED_COUNT, PWS_TYPE_CODE,
  FIPS_CODES). Full 558MB SDWA_latest_downloads.zip also exists.
- SNAP real data: host fns.usda.gov 504s via Azure Front Door; live host
  fna.usda.gov. snap-annualsummary-10.xlsx FY2025 avg participation
  42,142,184 (thousands per header). Conflict: snap-4fymonthly-10.xlsx
  FY2025 = 42,145,499 (avg of monthly). Annual summary labeled
  "subject to revision"; both reported.
- NSLP: 01slfypart-10.xlsx FY2025 = 29,988,041 (nine-month avg daily).
- WIC: 37wic-monthly-10.xlsx FY2025 total = 6,867,418.
- CMS Medicare: cms.gov NXDOMAIN on this machine's resolver; host exists
  via public DNS (Akamai). Not bypassed; reported unavailable here.

## Subagent sweep 2 (consumption/infrastructure) 2026-11-18, verified URLs
- FHWA VMT 2024: fhwa.dot.gov/policyinformation/statistics/2024/xls/vm1.xlsx
  (Total Rural and Urban row, ALL MOTOR VEHICLES = 3,294,031.21898
  million miles). Bonus rows: motor vehicles registered 2024 = 297,525,836
  (VM-1 basis; NOT substituted into the vehicles method, which calibrates
  on MV-1), person-miles 5.18T, fuel consumed.
- EPA LMOP measured landfill acceptance: lmopcompositedata.xlsx;
  dedupe by Landfill ID -> 470,973,446 tons/yr over 2,233 landfills;
  all waste streams, mixed years; reported, not weighted.
- TTB alcohol CSVs (2025): beer removals 139,429,735; wine withdrawals
  554,428,785; spirits bottled 523,309,665. Units NOT stated in files;
  reported raw only, no per-capita conversion.
- ERS nutrient availability: calorie series ENDS 2010 and is per-capita
  (census-denominated, circular) -> food method stays unweighted/None.
- FCC opendata: DNS-blocked locally, unverified.
- CWNS 2022: SSO-gated, no public bulk file.
- CMS Medicare: dataset verified public (data.csv, July 2026, TOT_BENES)
  but cms.gov NXDOMAIN on this resolver; client wired fail-soft, no DNS
  bypass performed on the project's own authority.

## Expansion corrections (found by tests/verification, 2026-11-18)
- SDWIS search export includes inactive/merged systems: filter
  PWS_ACTIVITY_CODE == 'A'; CWS served drops 387.1M -> 331.9M.
- VMT XLSX: stacked multi-row headers; ALL MOTOR VEHICLES is the last
  numeric column of the Total row (row 26), not a header label.
- BLS method conflated denominators: 0.595 EP ratio is against the
  civilian 16+ population; method now uses employed/(ratio x 0.78 adult
  share) -> 352.5M (was 275.0M).
- Reconciliation water row: separate PS/well rows divided well withdrawals
  by TOTAL population (invalid); replaced with the blended constant row
  (PS 95-160, wells 65-110 at 0.85 served share -> 90.5-153.5).
- Final expanded run: ensemble 360,979,127 (CI 338.1M-380.8M), PEP ratio
  1.061. Reconciliation: 450M needs 12/15 constants outside published
  ranges (water blend 92.0, vehicles 0.63/person, ww design 98.4 fit);
  500M needs 14/15 outside (only ww design fits).
