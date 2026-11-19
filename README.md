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

## Results (run of 2026-11-19, 27 national voices, all data downloaded)

| Metric | Value |
|--------|-------|
| Ensemble central | 356,412,430 |
| Bootstrap 90% CI (1000 draws) | 338,309,544 - 370,330,839 |
| Census PEP 2024 | 340,110,988 |
| Ratio to census PEP | 1.048 |
| Census decennial 2020 | 331,449,281 |

Method contributions (central, weight, data):

| Method | Central | Weight | Data |
|--------|---------|--------|------|
| Wastewater design flow | 553.7M | 0.09 | EPA ICIS-NPDES permits |
| Vehicles | 427.5M | 0.03 | FHWA registrations 2022 |
| Water systems served | 390.5M | 0.04 | EPA SDWIS: 331.9M utility-reported, active CWS |
| Medicare aged | 388.4M | 0.03 | CMS July 2026: 64.04M aged beneficiaries |
| Water budget | 356.2M | 0.11 | USGS 2015, 3,142 counties |
| Energy | 353.1M | 0.04 | EIA SEDS residential kWh 2024 |
| BLS employment | 352.5M | 0.03 | BLS API |
| Transit trips | 348.6M | 0.01 | NTD 2024: 7.67B unlinked trips |
| Air enplanements | 347.5M | 0.01 | FAA CY2025: 973M boardings |
| Electricity meters | 343.5M | 0.02 | EIA-861: 143.1M meters (Bundled+Delivery) |
| Census PEP 2024 | 340.1M | 0.10 | capped comparison voice |
| College enrollment | 340.0M | 0.01 | IPEDS 2023: 19.04M students |
| SNAP | 339.9M | 0.02 | USDA FNS FY2025: 42.14M participants |
| Gasoline | 339.7M | 0.03 | EIA product supplied |
| Total energy | 339.7M | 0.02 | EIA 2025: 96.5 quad Btu |
| VMT | 339.6M | 0.02 | FHWA 2024: 3.294T miles |
| Food expenditure | 339.4M | 0.01 | ERS 2025: $2.51T all purchasers |
| Grocery | 339.3M | 0.02 | census retail 2023 |
| K-12 enrollment | 337.2M | 0.03 | NCES 2024-25: 49.57M students |
| Gas volume | 335.0M | 0.02 | EIA 2024: 4,389 Bcf |
| Library visits | 334.7M | 0.01 | IMLS FY2023: 803M visits |
| Wireless | 333.3M | 0.02 | CTIA survey 2023 |
| IRS AGI | 328.3M | 0.03 | IRS SOI TY2022: $14.61T |
| Births | 327.8M | 0.03 | PEP 2024: 3,605,563 (NCHS-derived) |
| MSW | 327.0M | 0.03 | EPA 2018 |
| Healthcare (ER) | 325.0M | 0.04 | CDC NCHS 2021 |
| IRS exemptions | 323.1M | 0.05 | IRS SOI TY2022: 284.3M |
| Housing | 321.3M | 0.05 | census 2020 housing units |
| Gas customers | 313.3M | 0.01 | EIA 2024: 73.7M gas meters |
| Deaths | 308.7M | 0.03 | PEP 2024: 3,086,925 (NCHS-derived) |
| Buildings | 209.3M | 0.04 | MS footprints (approximated ratios) |

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
| Census PEP 2024 (340.1M) | 4 of 27 |
| Ensemble (356.4M) | 5 of 27 |
| 400M | 13 of 27 |
| 450M | 21 of 27 |
| 500M | 25 of 27 |

At 450M only six measured totals stay inside their published ranges:
total water withdrawals, vehicle registrations, wastewater design
capacity (a capacity figure with growth headroom), and the widest-range
behavioral voices (transit, libraries). Every other measured total —
electricity sold and metered, gas meters and volume, gasoline, VMT,
total energy, MSW, K-12 and college enrollment, SNAP, births, deaths,
ER visits, IRS exemptions and AGI, housing units, employment, Medicare
aged enrollment, water systems served, food expenditure — would need
its per-capita rate to be wrong by 15-45% in the same direction
simultaneously. At 500M only two survive.

Four voices sit meaningfully above census: utility-reported
community-water population served (378-405M), Medicare aged
beneficiaries (357-426M), vehicle registrations (363-485M), and
wastewater design capacity (403-738M). The bootstrap 90% CI of the full
ensemble is 338-370M. The measured evidence does not support 450M+; it
clusters between the census count and roughly 370M.

## Method status (data honesty)

Runs on downloaded real data: water (USGS), wastewater design flow (EPA
NPDES), wastewater chemistry (EPA DMR), energy (EIA SEDS), total primary
energy (EIA MER), natural gas volume and customer counts (EIA), VMT and
registrations (FHWA), electricity meters (EIA-861, Bundled+Delivery),
IRS exemptions and AGI (SOI CSV), BLS (API), MSW and gasoline (EPA/EIA
pages), SNAP (USDA FNS annual summary), K-12 enrollment (NCES CCD),
college enrollment (NCES Digest 303.10), water systems (EPA SDWIS),
Medicare aged enrollment (CMS Monthly Enrollment CSV, July 2026, county
rows included), births and deaths (Census PEP NCHS-derived columns),
transit trips (NTD via data.transportation.gov), enplanements (FAA),
food expenditure (USDA ERS), library visits (IMLS PLS), census PEP
(bulk CSV). The CMS file was fetched through an operator-authorized SSH
proxy to a VPS because the local resolver blocks cms.gov; it passed the
machine's ClamAV download gate before use, and the client also supports
`POP_EST_SOCKS_PROXY` as an alternative route.

Uses published national constants where bulk data is blocked or
unpublished: healthcare totals (CDC NCHS/AHRQ), wireless (CTIA survey —
verified that no FCC bulk dataset of subscriptions exists; the counts
are CTIA-proprietary), grocery (census retail), vehicles numerator (FHWA
MV-1 2022), buildings (footprint counts verified for 5 states, national
total and ratios approximated and marked `APPROXIMATED` in the code).

Unavailable (fail-soft, reason printed): SSA OASDI (403 to this network
on every statcomps path), USFWS license reports (origin dead, HTTP 530),
HUD USPS delivery points (registration-gated), BEA PCE (bulk tree
replaced by a JS app shell; the level needs an API key), CWNS 2022
facility data (SSO-gated), ERS total-calorie food series (ends 2010 and
is per-capita, i.e. census-denominated and circular), TTB alcohol (CSVs
fetched; units not stated in file, so reported raw, not converted).

## Known limitations

See PLAN.md "Known Limitations". Per-capita constants are calibration
knobs with published ranges; the bootstrap resamples them within those
ranges, so the CI reflects assumption uncertainty, not measurement
noise. Several constants (enrollment share, aged share, SNAP rate) have
census-informed denominators; those voices are weighted modestly and
flagged in the source column. Counties with no method data keep blank
estimates (`n_methods` 0), never invented values.
