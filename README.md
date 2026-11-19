# Population Estimator

Multi-source estimation of the true United States population at county-level
granularity, using physical infrastructure as primary evidence.

Water consumption, wastewater chemistry (nitrogen, ammonia, BOD), energy use,
waste generation, food supply, and healthcare utilization reveal actual human
presence independent of self-report surveys. Census data is comparison-only:
since the operator-set weighting change of 2026-11-19 it carries zero ensemble
weight. It never shifts the estimate.

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

## Results (run of 2026-11-19, 31 national voices, census weight 0)

| Metric | Value |
|--------|-------|
| Ensemble central | 357,139,690 |
| Bootstrap 90% CI (1000 draws) | 337,084,257 - 374,925,466 |
| Census PEP 2024 (comparison only) | 340,110,988 |
| Ratio to census PEP | 1.050 |
| Census decennial 2020 (comparison only) | 331,449,281 |

The census carries **zero ensemble weight** (operator-set 2026-11-19):
it is fetched, reported, and used as the reconciliation reference, but
it never shifts the estimate. Method contributions (central, weight,
data):

| Method | Central | Weight | Data |
|--------|---------|--------|------|
| Wastewater design flow | 553.7M | 0.088 | EPA ICIS-NPDES permits |
| Vehicles | 427.5M | 0.027 | FHWA registrations 2022 |
| Water systems served | 390.5M | 0.041 | EPA SDWIS: 331.9M active CWS |
| Medicare aged | 388.4M | 0.027 | CMS 2026-07: 64.04M aged |
| Water budget | 356.2M | 0.109 | USGS 2015, 3,142 counties |
| Energy | 353.1M | 0.041 | EIA SEDS kWh 2024 |
| BLS employment | 352.5M | 0.034 | BLS API |
| Transit trips | 348.6M | 0.007 | NTD 2024: 7.67B trips |
| Air enplanements | 347.5M | 0.014 | FAA CY2025: 973M |
| Electricity meters | 343.5M | 0.020 | EIA-861: 143.1M meters |
| Licensed drivers | 341.6M | 0.020 | FHWA DL-1C: 239.8M drivers |
| Grocery stores | 341.2M | 0.020 | Census MARTS 2025: $1.007T |
| BEA income | 341.1M | 0.014 | BEA 2024: $24.90T |
| Census PEP 2024 (comparison) | 340.1M | 0.000 | PEP 2024 |
| College enrollment | 340.0M | 0.014 | IPEDS 2023: 19.04M |
| SNAP | 339.9M | 0.020 | FNS FY2025: 42.14M |
| Gasoline | 339.7M | 0.027 | EIA supplied |
| Total energy | 339.7M | 0.020 | EIA 2025: 96.5 quad |
| VMT | 339.6M | 0.020 | FHWA 2024: 3.294T miles |
| Food expenditure | 339.4M | 0.014 | ERS 2025: $2.51T |
| Hospital inpatient days | 339.3M | 0.014 | CMS FY2021: 190.0M days |
| Medicaid+CHIP | 339.3M | 0.014 | CMS 2026-07: 72.95M |
| K-12 enrollment | 337.2M | 0.027 | NCES 2024-25: 49.57M |
| Gas volume | 335.0M | 0.020 | EIA 2024: 4,389 Bcf |
| Library visits | 334.7M | 0.007 | IMLS FY2023: 803M |
| Wireless | 333.3M | 0.020 | CTIA 2023 |
| IRS AGI | 328.3M | 0.027 | SOI TY2022: $14.61T |
| Births | 327.8M | 0.034 | PEP 2024: 3,605,563 births |
| MSW | 327.0M | 0.034 | EPA 2018 |
| Healthcare (ER) | 325.0M | 0.041 | CDC NCHS 2021 |
| IRS exemptions | 323.1M | 0.054 | SOI TY2022: 284.3M |
| Housing | 321.3M | 0.048 | census 2020 units |
| Gas customers | 313.3M | 0.014 | EIA 2024: 73.7M |
| Deaths | 308.7M | 0.027 | PEP 2024: 3,086,925 deaths |
| Buildings | 209.3M | 0.041 | MS footprints (approximated) |

| Census PEP 2024 (340.1M) | 27 of 31 fit |
| Ensemble (357.1M) | 5 of 31 outside published range |
| 400M | 16 of 31 outside published range |
| 450M | 25 of 31 outside published range |
| 500M | 29 of 31 outside published range |

## What a 450M+ claim would require

`popest run` computes, for each measured national total, the per-capita
constant a given population level would require, and checks it against
the constant's published range (`output/reconciliation.csv`):

| Claimed population | Constants outside published range |
|---|---|
| Census PEP 2024 (340.1M) | 4 of 31 |
| Ensemble (357.1M) | 5 of 31 |
| 400M | 16 of 31 |
| 450M | 25 of 31 |
| 500M | 29 of 31 |

At 450M only six measured totals stay inside their published ranges:
total water withdrawals, vehicle registrations, wastewater design
capacity (a capacity figure with growth headroom), and the widest-range
behavioral voices (transit, libraries). Every other measured total
would need its per-capita rate to be wrong by 15-45% in the same
direction simultaneously. At 500M only two survive.

Four voices sit meaningfully above census: utility-reported
community-water population served (378-405M), Medicare aged
beneficiaries (357-426M), vehicle registrations (363-485M), and
wastewater design capacity (403-738M). The bootstrap 90% CI of the full
census-free ensemble is 337-375M. The measured evidence does not
support 450M+; it clusters between the census count and roughly 375M.

## Method status (data honesty)

Runs on downloaded real data: water (USGS), wastewater design flow (EPA
NPDES), wastewater chemistry (EPA DMR), energy (EIA SEDS), total primary
energy (EIA MER), natural gas volume and customer counts (EIA), VMT and
registrations (FHWA), electricity meters (EIA-861, Bundled+Delivery),
licensed drivers (FHWA DL-1C), IRS exemptions and AGI (SOI CSV), BLS
(API), MSW and gasoline (EPA/EIA pages), SNAP (USDA FNS annual summary),
K-12 enrollment (NCES CCD), college enrollment (NCES Digest 303.10),
water systems (EPA SDWIS), Medicare aged enrollment (CMS Monthly
Enrollment CSV, July 2026, county rows included), Medicaid+CHIP
enrollment (CMS state data, 2026-07), hospital inpatient days (CMS
Hospital Provider Cost Report FY2021), births and deaths (Census PEP
NCHS-derived columns), transit trips (NTD via data.transportation.gov),
enplanements (FAA), food expenditure (USDA ERS), grocery (census MARTS
NAICS 445), personal income (BEA CAINC1), library visits (IMLS PLS),
census PEP (bulk CSV). The CMS/Medicaid files were fetched through an
operator-authorized SSH proxy to a VPS because the local resolver's
DNSSEC validation fails for cms.gov and medicaid.gov; each passed the
machine's ClamAV download gate before use, and the clients also support
`POP_EST_SOCKS_PROXY` as an alternative route.

Uses published national constants where bulk data is blocked or
unpublished: healthcare ER totals (CDC NCHS/AHRQ), wireless (CTIA survey —
verified that no FCC bulk dataset of subscriptions exists; the counts
are CTIA-proprietary), vehicles numerator (FHWA MV-1 2022), buildings
(footprint counts verified for 5 states, national total and ratios
approximated and marked `APPROXIMATED` in the code).

Unavailable (fail-soft, reason printed): SSA OASDI (Akamai 403 from
both the workstation and the VPS — public data behind datacenter-IP
blocking), USFWS license reports (origin dead, HTTP 530), HUD USPS
delivery points (registration-gated), BEA PCE levels (bulk tree
replaced by a JS app shell; the level needs an API key), FCC Form 477
fixed broadband (DNS block + Akamai 403; fixed series ended June 2020),
CWNS 2022 facility data (SSO-gated), PRC postal volume (PDF-only),
TSA throughput (HTML-only), ERS total-calorie food series (ends 2010
and is per-capita, i.e. census-denominated and circular), TTB alcohol
(CSVs fetched; units not stated in file, so reported raw, not
converted). Medicaid reimbursed prescriptions (FY2025: 596.3M) and
hospital discharges (FY2021: 32.2M) are reported but not
ensemble-weighted: their per-capita chains stack multiple
census-informed denominators.

## Known limitations

See PLAN.md "Known Limitations". Per-capita constants are calibration
knobs with published ranges; the bootstrap resamples them within those
ranges, so the CI reflects assumption uncertainty, not measurement
noise. Several constants (enrollment share, aged share, SNAP rate) have
census-informed denominators; those voices are weighted modestly and
flagged in the source column. Counties with no method data keep blank
estimates (`n_methods` 0), never invented values.
