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
2015, EPA DMR FY2024, IRS TY2022, EIA SEDS 2024, census PEP Vintage 2024);
each method cites its own data year in the run output and summary.

No API keys are required. A Census API key is optional (`--api-key`) and only
affects the county-level decennial-2020 comparison; PEP county data needs no
key.

## Commands

| Command | What it does |
|---------|--------------|
| `popest run [--year Y]` | Full pipeline: all methods, national ensemble with bootstrap 90% CI, county ensemble, state rollup, all outputs |
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
- `summary.txt` — human-readable report

## Results (run of 2026-11-18, fresh clone, all data downloaded)

| Metric | Value |
|--------|-------|
| Ensemble central | 358,571,850 |
| Bootstrap 90% CI (1000 draws) | 331,569,881 - 382,565,504 |
| Census PEP 2024 | 340,110,988 |
| Ratio to census PEP | 1.054 |
| Census decennial 2020 | 331,449,281 |

Method contributions (central, published-range span, weight):

| Method | Central | Weight | Data |
|--------|---------|--------|------|
| Wastewater design flow | 553.7M | 0.13 | EPA ICIS-NPDES permits |
| Vehicles | 427.5M | 0.04 | FHWA registrations 2022 |
| Water budget | 356.2M | 0.16 | USGS 2015, 3,142 counties |
| Energy | 353.1M | 0.06 | EIA SEDS residential kWh 2024 |
| Census PEP 2024 | 340.1M | 0.06 | capped comparison voice |
| Gasoline | 339.7M | 0.04 | EIA product supplied |
| Grocery | 339.3M | 0.03 | census retail 2023 |
| Vitals (births) | 333.4M | 0.05 | CDC NCHS births 2022 |
| Wireless | 333.3M | 0.03 | CTIA survey 2023 |
| SNAP | 332.3M | 0.03 | USDA FNS 2023 |
| MSW | 327.0M | 0.05 | EPA 2018 |
| Healthcare (ER) | 325.0M | 0.06 | CDC NCHS 2021 |
| IRS filers | 323.1M | 0.08 | IRS SOI TY2022 |
| Housing | 321.3M | 0.07 | census 2020 housing units |
| BLS employment | 275.0M | 0.05 | BLS API |
| Buildings | 209.3M | 0.06 | MS footprints (approximated ratios) |

Wastewater chemistry is **reported but not ensemble-weighted**: only 4,046
municipal plants report BOD in mass units (13% of plants with design flows),
so its numerator is a reporting subset, a coverage-limited lower bound
(BOD 17.6M, TSS 208.6M population equivalents; see
`output/national.csv` and `output/summary.txt`). County columns carry it
unweighted for inspection.

## Method status (data honesty)

Runs on downloaded real data: water (USGS), wastewater design flow (EPA
NPDES), wastewater chemistry (EPA DMR), energy (EIA SEDS), IRS (SOI CSV),
BLS (API), MSW and gasoline (EPA/EIA pages), census PEP (bulk CSV).

Uses published national constants where bulk data is blocked or app-shelled:
healthcare totals (CDC NCHS/AHRQ), vitals (NCHS final), SNAP/wireless/
grocery (published aggregates), vehicles (FHWA), buildings (footprint counts
verified for 5 states, national total and ratios approximated and marked
`APPROXIMATED` in the code).

## Known limitations

See PLAN.md "Known Limitations". Per-capita constants are calibration
knobs with published ranges; the bootstrap resamples them within those
ranges, so the CI reflects assumption uncertainty, not measurement noise.
Counties with no method data keep blank estimates (`n_methods` 0), never
invented values.
