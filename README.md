# Population Estimator

Multi-source estimation of the true United States population at county-level
granularity, using physical infrastructure as primary evidence.

Water consumption, wastewater chemistry (nitrogen, ammonia, BOD), energy use,
waste generation, food supply, and healthcare utilization reveal actual human
presence independent of self-report surveys. Census data is included for
comparison only, not as an anchor.

See [PLAN.md](PLAN.md) for full methodology, data sources, and per-capita
calibration constants.

## Quick Start

```bash
pip install -e .
popest run --year 2024
```

## Output

- Per-county CSV: FIPS, name, state, estimate, 90% CI, method contributions
- National discrepancy report: each method's estimate vs census
