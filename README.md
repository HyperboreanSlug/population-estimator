# Population Estimator

Multi-source estimation of the true United States population at county-level
granularity, using physical infrastructure as primary evidence.

Water consumption, wastewater chemistry (nitrogen, ammonia, BOD), energy use,
waste generation, food supply, and healthcare utilization reveal actual human
presence independent of self-report surveys. Census data is included for
comparison only, capped at 15% of ensemble weight, never as an anchor.

See [PLAN.md](PLAN.md) for full methodology, data sources, and per-capita
calibration constants. [SOURCE.md](SOURCE.md) documents every module.

## Quick Start

```bash
pip install -e .
popest download          # core data, ~1.3 GB
popest run --year 2024   # full pipeline
```

`--year` labels the target estimate year. Source data years vary (USGS water
2015, EPA DMR FY2024, EIA SEDS 2024, NCES 2024-25, SNAP FY2025, FHWA VMT
2024, census PEP Vintage 2024); each method cites its own data year in the
run output and summary.

No API keys are required. A Census API key is optional (`--api-key`) and only
affects the county-level decennial-2020 comparison; PEP county data needs no
key. CMS Medicare and FCC opendata are DNS-blocked on some resolvers; those
voices drop fail-soft with the reason printed.

## Commands

| Command | What it does |
|---------|--------------|
| `popest run [--year Y]` | Full pipeline: all methods, national ensemble with bootstrap 90% CI, county ensemble, state rollup, reconciliation analysis, all outputs |
| `popest download [--all]` | Core data manifest (~1.3 GB); `--all` adds the full PLAN.md tier 1-5 catalog (several GB) |
| `popest verify` | Check every downloaded file is non-empty and parseable |
| `popest status` | Report which numbers come from downloaded files vs. literature constants |
| `popest sensitivity` | Per-capita constant sensitivity table |
| `popest water / wastewater / chemistry / energy / waste / healthcare / housing / vitals / buildings / consumption / irs / bls` | Run a single method and save its CSV |

## Output

All written to `output/` by `popest run`:

- `counties.csv` — per-county ensemble: FIPS, county, state, estimate,
  range endpoints, method contributions, per-method populations
- `states.csv` — state rollup of covered counties
- `national.csv` — ensemble, bootstrap 90% CI, census comparisons
- `discrepancy_report.csv` — every method vs. census
- `reconciliation.csv` — implied per-capita constant at each population
  level vs. its published range
- `summary.txt` — human-readable report

## Results (run of 2026-11-18, fresh clone, all data downloaded)

| Metric | Value |
|--------|-------|
| Ensemble central | 360,979,127 |
| Bootstrap 90% CI (1000 draws) | 338,090,490 - 380,824,318 |
| Census PEP 2024 | 340,110,988 |
| Ratio to census PEP | 1.061 |
| Census decennial 2020 | 331,449,281 |

Method contributions (central, weight, data):

| Method | Central | Weight | Data |
|--------|---------|--------|------|
| Wastewater design flow | 553.7M | 0.11 | EPA ICIS-NPDES permits |
| Vehicles | 427.5M | 0.03 | FHWA registrations 2022 |
| Water systems served | 390.5M | 0.05 | EPA SDWIS: 331.9M utility-reported, active CWS |
| Water budget | 356.2M | 0.13 | USGS 2015, 3,142 counties |
| Energy | 353.1M | 0.05 | EIA SEDS residential kWh 2024 |
| BLS employment | 352.5M | 0.04 | BLS API (employed / adult EP ratio / share) |
| Census PEP 2024 | 340.1M | 0.12 | capped comparison voice |
| SNAP | 339.9M | 0.03 | USDA FNS annual summary FY2025 (42.14M participants) |
| Gasoline | 339.7M | 0.03 | EIA product supplied |
| VMT | 339.6M | 0.03 | FHWA VM-1 2024 (3.294T miles) |
| Grocery | 339.3M | 0.03 | census retail 2023 |
| K-12 enrollment | 337.2M | 0.03 | NCES 2024-25 (49.57M students) |
| Vitals (births) | 333.4M | 0.04 | CDC NCHS births 2022 |
| Wireless | 333.3M | 0.03 | CTIA survey 2023 |
| MSW | 327.0M | 0.04 | EPA 2018 |
| Healthcare (ER) | 325.0M | 0.05 | CDC NCHS 2021 |
| IRS filers | 323.1M | 0.07 | IRS SOI TY2022 (284.3M exemptions) |
| Housing | 321.3M | 0.06 | census 2020 housing units |
| Buildings | 209.3M | 0.05 | MS footprints (approximated ratios) |

Reported, not ensemble-weighted:

- Wastewater chemistry (EPA DMR mass loads): BOD 17.6M / TSS 208.6M
  population equivalents; only 4,046 of ~30,121 municipal plants report
  BOD in mass units, so the numerator is a reporting subset
- LMOP measured landfill acceptance: 470.97M tons/yr from 2,233 landfills
  (all waste streams, mixed reporting years; upper-bound context, not
  comparable to EPA's modeled MSW generation)
- FHWA VM-1 "motor vehicles" 2024: 297.5M (different count basis than the
  MV-1 registrations the vehicles method calibrates on)
- NSLP FY2025 29.99M avg daily participation; WIC FY2025 6.87M participants

## What a 450M+ claim would require

`popest run` computes, for each measured national total, the per-capita
constant a given population level would require, and checks it against
the constant's published range (`output/reconciliation.csv`):

| Claimed population | Constants outside published range |
|---|---|
| Census PEP 2024 (340.1M) | 3 of 15 |
| Ensemble (361.0M) | 5 of 15 |
| 400M | 7 of 15 |
| 450M | 12 of 15 |
| 500M | 14 of 15 |

At 450M only three measured totals stay inside their published ranges:
total water withdrawals (92.0 gal/person/day, at the very bottom of the
blended 90.5-153.5 range), vehicle registrations (0.63 per person = 0.81
per adult), and wastewater design flow (98.4 gal/person/day, a capacity
figure). Every other measured total — electricity sold, gasoline
supplied, MSW, VMT, K-12 enrollment, SNAP, births, ER visits, IRS
exemptions, housing units, employment — would need its per-capita rate
to be wrong by 15-45% in the same direction simultaneously. At 500M only
the wastewater design-flow constant survives.

Three voices do sit meaningfully above census: utility-reported
community-water population served (378-405M after the coverage
fraction), vehicle registrations (363-485M), and wastewater design
capacity (403-738M). The bootstrap 90% CI of the full ensemble is
338-381M. The measured evidence does not support 450M+; it clusters
between the census count and roughly 380M.

## Method status (data honesty)

Runs on downloaded real data: water (USGS), wastewater design flow (EPA
NPDES), wastewater chemistry (EPA DMR), energy (EIA SEDS), VMT (FHWA
VM-1), IRS (SOI CSV), BLS (API), MSW and gasoline (EPA/EIA pages), SNAP
(USDA FNS annual summary), K-12 enrollment (NCES CCD), water systems
(EPA SDWIS), census PEP (bulk CSV).

Uses published national constants where bulk data is blocked or app-shelled:
healthcare totals (CDC NCHS/AHRQ), vitals (NCHS final), wireless (CTIA),
grocery (census retail), vehicles numerator (FHWA MV-1 2022), buildings
(footprint counts verified for 5 states, national total and ratios
approximated and marked `APPROXIMATED` in the code).

Blocked or unavailable from this machine (fail-soft, reason printed):
CMS Medicare (cms.gov DNS blocked locally; dataset is public),
FCC wireless (fcc.gov DNS blocked locally), CWNS 2022 facility data
(SSO-gated), ERS total-calorie food series (ends 2010 and is
per-capita, i.e. census-denominated and circular), TTB alcohol (CSVs
fetched; units not stated in file, so reported raw, not converted).

## Known limitations

See PLAN.md "Known Limitations". Per-capita constants are calibration
knobs with published ranges; the bootstrap resamples them within those
ranges, so the CI reflects assumption uncertainty, not measurement
noise. Several constants (enrollment share, aged share, SNAP rate) have
census-informed denominators; those voices are weighted modestly and
flagged in the source column. Counties with no method data keep blank
estimates (`n_methods` 0), never invented values.
