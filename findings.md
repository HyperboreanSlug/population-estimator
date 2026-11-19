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
