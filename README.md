# Population Estimator

Multi-source estimation of the true United States population at county-level granularity.

Combines census data, vital statistics, administrative records, migration data,
housing indicators, and geospatial proxies into a precision-weighted ensemble
estimate with uncertainty bounds for all 3,143 counties.

See [PLAN.md](PLAN.md) for full methodology and data source documentation.

## Quick Start

```bash
pip install -e .
popest run --year 2024
```

## Output

CSV with per-county estimates: FIPS, name, state, point estimate, 90% CI bounds, method weights.
