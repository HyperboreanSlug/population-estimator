# Population Estimator - Comprehensive Plan

## Goal

Estimate the true resident population of the United States at county-level
granularity (3,143 counties + DC). Produce a point estimate with uncertainty
bounds per county and nationally. Cross-validate across independent methods
and data sources.

The "true population" means: all persons usually resident in the US on a
given reference date, including those missed by the decennial census
(undercount), undocumented residents, and transient populations. Excludes
overseas military/civilians unless noted.

---

## Data Sources

### Tier 1: Primary (direct population measurement)

| # | Source | Granularity | Access | Coverage | Notes |
|---|--------|-------------|--------|----------|-------|
| 1 | Census Decennial (2020) | Block/county | API: `api.census.gov/data/2020/dec/pl` | Apr 2020 | Base count. Known net undercount ~0.24% |
| 2 | Census PEP Vintage 2024 | County | API: `api.census.gov/data/2024/pep/population` | Jul 2024 | Components-method estimate. Official but inherits base errors |
| 3 | Census Post-Enumeration Survey (PES) 2020 | State/national | Bulk PDF/CSV from census.gov | 2020 | Measures differential undercount by race/age. Key for adjustment |
| 4 | American Community Survey (ACS) 5-year | County/tract | API: `api.census.gov/data/2023/acs/acs5` | 2019-2023 | Sample-based. Group quarters, household size, vacancy |
| 5 | CDC WONDER Natality | County | HTTP API (form POST) | 2007-2024 | Births by county, year, mother's age/race |
| 6 | CDC WONDER Mortality | County | HTTP API (form POST) | 1999-2022 | Deaths by county, year, age/race |

### Tier 2: Administrative records (independent population proxies)

| # | Source | Granularity | Access | Coverage | Notes |
|---|--------|-------------|--------|----------|-------|
| 7 | IRS SOI ZIP Code Data | ZIP (→county) | Bulk CSV download | TY2022 | Returns filed, dependents, exemptions. ~150M returns |
| 8 | SSA SSN Issuance | State/year | Bulk download (ssa.gov) | Annual | New SSNs = births + immigration proxy |
| 9 | CMS Medicare Enrollment | County | Bulk CSV (data.cms.gov) | Annual | 65+ population near-complete coverage |
| 10 | Medicaid/CHIP Enrollment | State/county | data.medicaid.gov | Monthly | Low-income + children coverage |
| 11 | USPS Delivery Sequence File | ZIP/carrier route | Commercial license OR aggregate from census | Quarterly | Deliverable address count. Best housing proxy |
| 12 | Census Building Permits Survey | County/place | API: `api.census.gov/data/2023/bps` | Annual | New housing units authorized |
| 13 | HUD/Census Housing Vacancy Survey (HVS) | State/metro | Bulk download | Annual | Occupancy and vacancy rates |
| 14 | NCES School Enrollment | District/county | Bulk download (nces.ed.gov) | Annual | K-12 enrollment. Ages 5-17 proxy |
| 15 | BLS County Employment | County | API: `api.bls.gov` | Monthly | Employment-to-population ratio application |
| 16 | State Voter Registration Files | County/precinct | State-specific (varies) | Current | Registered voters. Coverage varies by state |
| 17 | State DMV License/ID Counts | County | State-specific (varies) | Current | Adult population proxy |

### Tier 3: Migration and hard-to-count

| # | Source | Granularity | Access | Coverage | Notes |
|---|--------|-------------|--------|----------|-------|
| 18 | DHS Yearbook of Immigration | State/national | Bulk PDF/CSV (dhs.gov) | Annual | Legal permanent residents, naturalizations |
| 19 | CBP Border Encounter Data | Sector/national | Bulk CSV (cbp.gov) | Monthly | Proxy for unauthorized migration flows |
| 20 | Pew/MPI Unauthorized Estimates | State/national | Published reports | Periodic | Model-based estimates of undocumented pop |
| 21 | Census ACS Foreign-born by Year of Entry | County | API | 5-year | Recent immigration at county level |
| 22 | I-94 Arrival/Departure (DHS) | Port/national | Bulk data | Annual | Non-immigrant admissions (students, workers) |

### Tier 4: Geospatial and proxy indicators

| # | Source | Granularity | Access | Coverage | Notes |
|---|--------|-------------|--------|----------|-------|
| 23 | NASA VIIRS Nighttime Lights | ~750m grid | Bulk GeoTIFF (LAADS DAAC) | Monthly | Population density proxy. Saturation issues in cities |
| 24 | WorldPop / GPW v4 | 1km/30arc-sec | Bulk GeoTIFF (sedac.ciesin.columbia.edu) | 2020 | Gridded population. Model-based |
| 25 | Meta Data for Good | 30m grid | Bulk download (dataforgood.facebook.com) | 2024 | ML on satellite imagery. Building-level |
| 26 | Microsoft Building Footprints | Building polygon | Bulk GeoJSON (github.com/microsoft) | 2024 | Structure count proxy |
| 27 | Google Open Buildings | Building polygon | Bulk GeoJSON | 2024 | Africa-focused but US coverage exists |
| 28 | EIA Electric Utility Customers | Utility/county | Bulk CSV (eia.gov) | Monthly | Meter count = occupied housing proxy |
| 29 | EPA Water Utility Connections | Utility/county | Bulk CSV (epa.gov) | Annual | Another housing occupancy proxy |
| 30 | CTIA/FCC Wireless Subscriptions | State/national | Published reports | Annual | >100% penetration, limited use alone |

### Tier 5: Validation and cross-check

| # | Source | Granularity | Access | Coverage | Notes |
|---|--------|-------------|--------|----------|-------|
| 31 | Census Demographic Analysis (DA) | National/age-sex | Published | 2020 | Independent of census. Uses SSA, Medicare, births/deaths |
| 32 | UN World Population Prospects | National | API (population.un.org) | 2024 | International comparison |
| 33 | Census Bureau International Database | National | API | 2024 | Another national cross-check |
| 34 | State-level population registers | State | Varies | Current | Some states maintain their own estimates |

---

## Methodology

### Method A: Adjusted Census Base + Components

The core demographic accounting approach:

```
P(county, t) = P_census(county, 2020) × (1 + undercount_rate(county))
             + Births(county, 2020→t)
             - Deaths(county, 2020→t)
             + Net_Migration(county, 2020→t)
```

**Undercount adjustment:** Apply PES differential undercount rates by
race/age group. Distribute national/state undercount to counties using ACS
demographic composition weights.

**Births/Deaths:** CDC WONDER county-level, annual. Straightforward.

**Net Migration:** Hardest component. Decompose into:
- Domestic net migration: IRS tax return address changes (county-to-county
  flow data from IRS SOI migration files)
- International legal migration: DHS admissions allocated to county via ACS
  foreign-born settlement patterns
- Unauthorized migration: National estimate × county allocation weights
  (ACS foreign-born non-citizen share, employment in low-skill sectors)
- Puerto Rico/territories migration: ACS migration flows

### Method B: Administrative Records Ratio

Independent estimate from administrative data:

```
P(county) = max(IRS_filers + dependents,
                Medicare_65+ / coverage_rate_65+,
                School_enrollment / enrollment_rate_5_17,
                Medicaid_enrolled / eligibility_rate)
```

Each administrative source covers a subset. Combine via:
- IRS: ~85% of adults file. Add estimated non-filers (undocumented, homeless,
  very low income).
- Medicare: Near-complete for 65+. Use as anchor for elderly.
- Schools: ~90% enrollment rate for 5-17. Anchor for children.
- Medicaid: Covers ~40% of population. Useful for low-income segment.

Stack these age-segment anchors to build a full population estimate.

### Method C: Housing Unit Method

```
P(county) = Housing_Units(county) × Occupancy_Rate(county) × Persons_per_Household(county)
```

- Housing units: Census 2020 + building permits since + USPS address growth
- Occupancy: ACS/HVS vacancy rate
- Persons per household: ACS, adjusted for trend

Strong independent check. Weakness: misses group quarters (prisons, dorms,
nursing homes, military barracks). Add GQ from ACS separately.

### Method D: Geospatial / ML Estimate

Use Meta Data for Good 30m population density rasters. Aggregate to county.
Cross-check with WorldPop and VIIRS. These are ML models trained on census +
satellite, so they're partially circular — use as validation, not primary.

### Method E: Employment-Based

```
P(county) = Employment(county) / Employment_Rate(county)
```

BLS county employment ÷ ACS labor force participation rate. Crude but
independent. Best as a sanity bound, not a primary estimate.

---

## Ensemble Strategy

Combine methods A-E into a final estimate per county:

1. **Weighted average** with weights inversely proportional to each method's
   estimated variance (precision-weighted mean).
2. **Variance estimation** via bootstrap: resample inputs within their known
   uncertainty, recompute each method, measure spread.
3. **Outlier detection:** If any method diverges >2σ from the ensemble, flag
   for investigation. Do not blindly average.
4. **Hierarchical reconciliation:** County estimates must sum to state
   estimates which must sum to national. Use iterative proportional fitting
   (raking) to enforce consistency.
5. **Final output:** Point estimate + 90% credible interval per county.

National-level cross-checks:
- Compare to Census PEP national estimate
- Compare to Census Demographic Analysis
- Compare to UN WPP
- The ensemble should bracket or closely match these.

---

## Implementation Phases

### Phase 1: Infrastructure and Census Base
- Project scaffolding (Python, data pipeline framework)
- Census API client (decennial, PEP, ACS)
- Download and store 2020 census county population
- Download ACS 5-year county demographics
- Download PES undercount rates
- Apply undercount adjustment → adjusted 2020 base per county

### Phase 2: Vital Statistics
- CDC WONDER client (births, deaths by county)
- Compute natural increase (births - deaths) per county, 2020→2024
- Add to adjusted base

### Phase 3: Migration
- IRS SOI county-to-county migration flows (domestic)
- DHS immigration data → county allocation
- Unauthorized migration estimate → county allocation
- Compute net migration per county

### Phase 4: Administrative Records (Method B)
- IRS ZIP→county crosswalk + filer/dependent counts
- CMS Medicare county enrollment
- NCES school enrollment by district→county
- Medicaid enrollment
- Build age-segment anchors

### Phase 5: Housing Unit Method (Method C)
- Census housing units + building permits
- ACS vacancy/occupancy
- Persons per household
- Group quarters addition

### Phase 6: Geospatial (Method D)
- Download Meta Data for Good rasters
- Aggregate to county via GIS operations
- WorldPop cross-check

### Phase 7: Ensemble and Output
- Implement all methods as independent estimators
- Precision-weighted combination
- Hierarchical reconciliation (county→state→national)
- Uncertainty quantification
- Final report generation (CSV, JSON, optional maps)

### Phase 8: Validation
- Compare to Census PEP, DA, UN WPP
- Sensitivity analysis on key assumptions
- Document known limitations

---

## Project Structure

```
population-estimator/
├── PLAN.md                 # This file
├── README.md
├── SOURCE.md               # Module documentation
├── pyproject.toml
├── .gitignore
├── config/
│   └── sources.yaml        # Data source URLs, API keys, parameters
├── src/
│   └── popest/
│       ├── __init__.py
│       ├── cli.py          # Entry point
│       ├── config.py       # Config loader
│       ├── geo.py          # County FIPS, crosswalks (ZIP→county, etc.)
│       ├── census.py       # Census API client (decennial, PEP, ACS)
│       ├── cdc.py          # CDC WONDER client (births, deaths)
│       ├── irs.py          # IRS SOI data loader
│       ├── migration.py    # DHS, CBP, migration estimation
│       ├── admin.py        # Medicare, Medicaid, schools, DMV
│       ├── housing.py      # Building permits, vacancy, USPS
│       ├── geospatial.py   # Raster aggregation (Meta, WorldPop)
│       ├── methods/
│       │   ├── __init__.py
│       │   ├── components.py   # Method A
│       │   ├── admin_ratio.py  # Method B
│       │   ├── housing.py      # Method C
│       │   ├── geospatial.py   # Method D
│       │   └── employment.py   # Method E
│       ├── ensemble.py     # Combination, reconciliation, uncertainty
│       └── report.py       # Output generation
├── data/                   # Downloaded raw data (gitignored)
├── output/                 # Final estimates (gitignored)
└── tests/
    ├── test_census.py
    ├── test_cdc.py
    └── test_ensemble.py
```

---

## Technical Decisions

- **Language:** Python 3.11+
- **Dependencies:** requests, pandas, geopandas, rasterio, pyyaml, numpy
- **Storage:** Parquet files for intermediate data. No database needed.
- **GIS:** geopandas + rasterio for county aggregation of rasters
- **API keys:** Census API key (free, register at census.gov). No key for CDC WONDER.
- **Rate limits:** Census API = 500 requests/day without key, 5000 with key.
  Batch requests by state. CDC WONDER = no hard limit but be polite.

---

## Known Limitations and Risks

1. **County-level undercount rates don't exist.** PES is state/national only.
   Must distribute using demographic weights. This is the largest uncertainty.
2. **Unauthorized migration at county level is model-dependent.** No ground
   truth. Pew/MPI estimates are national/state only.
3. **IRS data lags by 2 years.** TY2022 data in 2026 is stale.
4. **CDC WONDER suppresses counts <10.** Small counties lose signal.
5. **Group quarters are hard to track inter-censally.** Prisons, dorms,
   military change without building permits.
6. **Geospatial methods are partially circular** (trained on census data).
   Use for validation only.
7. **USPS DSF requires commercial license.** May use census housing + permits
   as substitute.

---

## Success Criteria

- National estimate within ±1% of Census PEP (sanity bound)
- County estimates sum to state estimates sum to national (reconciliation)
- Each method produces independent estimate; ensemble narrows uncertainty
- All data fetched programmatically (reproducible)
- Full run completes in <30 minutes on a laptop
- Output: CSV with columns [FIPS, county_name, state, estimate, lower_90, upper_90, method_weights]
