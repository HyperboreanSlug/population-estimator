# Population Estimator - Comprehensive Plan

## Goal

Estimate the true resident population of the United States at county-level
granularity (3,143 counties + DC). Produce a point estimate with uncertainty
bounds per county and nationally.

**Core assumption:** Census counts are one input among many, not the anchor.
The census is a self-report survey with known structural weaknesses. Physical
infrastructure data (water, wastewater, electricity, food, fuel) cannot be
undercounted — every person drinks water, generates waste, and consumes energy
regardless of whether they appear in any government registry.

Physical consumption indicators receive primary weight. Census/administrative
data is included for comparison but does not constrain the estimate.

The hypothesis space explicitly includes 500M+ residents. The tool reports
what the physical evidence says.

---

## Data Sources

### Tier 1: Physical Infrastructure (PRIMARY — highest weight)

These measure actual human presence. You cannot hide from water consumption
or wastewater generation.

| # | Source | Granularity | Access | What it measures |
|---|--------|-------------|--------|------------------|
| 1 | USGS National Water Use (municipal withdrawals) | County/state | Bulk CSV (waterdata.usgs.gov) | Total gallons/day withdrawn for public supply. ÷ per-capita use (~80-100 gal/person/day) = population served |
| 2 | EPA NPDES Wastewater Discharge Reports | Facility/county | Bulk CSV (EPA ECHO/ICIS) | Flow volume (MGD) + nitrogen/ammonia loads. ÷ per-capita contribution (~10-12g N/person/day, ~80-120 gal/person/day) = population served |
| 3 | EPA Clean Watersheds Needs Survey | Facility/state | Bulk download (epa.gov) | Design capacity of treatment plants (MGD). ÷ per-capita flow = max population served |
| 4 | State water quality annual reports | Facility | State EPA/DEP sites | BOD, TSS, ammonia, urea loads per plant. Per-capita BOD ~60-80g/person/day |
| 5 | EIA Residential Electricity Sales | County/utility | Bulk CSV (eia.gov) | Total kWh sold to residential customers. ÷ per-capita (~10,500 kWh/person/yr) = population |
| 6 | EIA Total Energy Consumption | State/county | Bulk CSV (eia.gov) | Total BTU including commercial/industrial. Cross-check |
| 7 | EPA Municipal Solid Waste Generation | State/national | Bulk download (epa.gov/facts-and-figures) | ~4.9 lbs/person/day. Total tonnage ÷ per-capita = population |
| 8 | USDA ERS Food Availability | National/state | Bulk CSV (ers.usda.gov) | Total caloric supply (kcal/capita/day × population = total). Back-solve from total food production/imports |
| 9 | EIA Petroleum/Gasoline Consumption | State | Bulk CSV (eia.gov) | ~390 gal/person/yr gasoline. Total ÷ per-capita = population |
| 10 | FHWA Vehicle Registrations | State/county | Bulk CSV (fhwa.dot.gov) | ~0.8 vehicles/person (adults ~1.0). Total ÷ rate = adult population |

### Tier 2: Healthcare and Biological Signals

Every person interacts with the healthcare system. Utilization data reveals
population independent of registration.

| # | Source | Granularity | Access | What it measures |
|---|--------|-------------|--------|------------------|
| 11 | CDC NCHS Hospital Utilization | State/national | Bulk CSV (cdc.gov/nchs) | Total ER visits, admissions, bed-days. ÷ per-capita utilization rate = population |
| 12 | AHRQ HCUP Hospital Statistics | State/national | Bulk download (hcup-us.ahrq.gov) | Discharges, ER visits per 1000. Back-solve from totals |
| 13 | CMS Hospital Cost Reports | Facility | Bulk CSV (data.cms.gov) | Patient volume by hospital. Sum nationally |
| 14 | CDC NCHS Ambulatory Care Visits | National | Bulk download | ~4 physician visits/person/yr. Total visits ÷ rate = population |
| 15 | Pharmacy dispensing data (IQVIA/state boards) | State/national | Published aggregates | ~12 prescriptions/person/yr. Total scripts ÷ rate |
| 16 | CDC Birth/Death Records | County | CDC WONDER API | Vital events. Birth rate ~11/1000. Total births ÷ rate = population |
| 17 | State hospital association reports | State | Varies | Admissions, ER volume by state |

### Tier 3: Consumption and Commercial Signals

| # | Source | Granularity | Access | What it measures |
|---|--------|-------------|--------|------------------|
| 18 | USDA food sales / grocery revenue | State/national | Published (ERS, Census retail) | Total food expenditure ÷ per-capita food spending (~$4,000/yr) |
| 19 | Census Retail Trade (food/beverage) | State/county | API | Grocery store sales as population proxy |
| 20 | EIA Natural Gas Residential Customers | State/utility | Bulk CSV | Meter count × avg household size |
| 21 | FCC/CTIA Wireless Subscribers | State/national | Published | ~1.1 subscriptions/person. Total ÷ rate |
| 22 | USPS mail volume / delivery points | National/ZIP | Published / commercial | Deliverable addresses × occupancy × household size |
| 23 | Total residential water meter connections | Utility/county | Utility reports, state PUC filings | Direct housing unit count |
| 24 | School lunch program participation (USDA) | State/district | Bulk download (fns.usda.gov) | Children in poverty + total enrollment proxy |
| 25 | SNAP/EBT participation | County/state | Bulk download (fns.usda.gov) | ~12-14% of population. Total ÷ rate |

### Tier 4: Census and Administrative (LOW weight — comparison only)

Included for cross-reference. Not used as anchor or constraint.

| # | Source | Granularity | Access | Notes |
|---|--------|-------------|--------|-------|
| 26 | Census Decennial 2020 | County | API | Self-report. Known undercount. One data point |
| 27 | Census PEP Vintage 2024 | County | API | Model-based on 2020 base. Inherits errors |
| 28 | Census ACS 5-year | County | API | Sample survey. Useful for ratios (HH size, vacancy) |
| 29 | IRS SOI ZIP Data | ZIP→county | Bulk CSV | Filers + dependents. Misses non-filers entirely |
| 30 | CMS Medicare Enrollment | County | Bulk CSV | 65+ only. Near-complete for that segment |
| 31 | NCES School Enrollment | District | Bulk CSV | Ages 5-17 proxy |
| 32 | BLS Employment | County | API | Labor force proxy |
| 33 | DHS Immigration Statistics | State/national | Bulk CSV | Legal flows only |
| 34 | CBP Encounter Data | Sector | Bulk CSV | Border flow proxy |

### Tier 5: Geospatial (validation)

| # | Source | Granularity | Access | Notes |
|---|--------|-------------|--------|-------|
| 35 | NASA VIIRS Nighttime Lights | 750m grid | Bulk GeoTIFF | Light intensity correlates with population |
| 36 | Meta Data for Good | 30m grid | Bulk download | ML on satellite. Partially circular (trained on census) |
| 37 | Microsoft Building Footprints | Polygon | Bulk GeoJSON | Structure count. × occupancy × HH size |
| 38 | WorldPop / GPW v4 | 1km grid | Bulk GeoTIFF | Model-based. Circular. Validation only |

---

## Methodology

### Method A: Water Budget (PRIMARY)

```
P = Total_Municipal_Water_Withdrawal / Per_Capita_Water_Use
```

- USGS reports total public-supply withdrawals per county (Mgal/day)
- Per-capita domestic use: 80-100 gal/person/day (EPA, AWWA studies)
- Adjust for: industrial/commercial use within municipal systems (~20-30%),
  system losses/leakage (~10-15%)
- Net residential fraction × total withdrawal ÷ per-capita = population

Cross-check with EPA wastewater flow data (what goes in must come out,
minus losses). If withdrawal says 400M but wastewater says 350M, investigate
the gap.

### Method B: Wastewater Chemistry (PRIMARY)

```
P = Total_Nitrogen_Load / Per_Capita_Nitrogen_Contribution
P = Total_BOD_Load / Per_Capita_BOD_Contribution
P = Total_Ammonia_Load / Per_Capita_Ammonia_Contribution
```

- EPA NPDES permits require facilities to report discharge loads
- Human waste contributes: ~10-12g total N/person/day, ~4-6g ammonia-N,
  ~60-80g BOD/person/day, ~10-15g TSS/person/day
- Urea is the dominant nitrogen species in urine (~11g N/person/day from
  urea alone)
- Sum all municipal WWTP loads nationally → divide by per-capita → population
- County allocation: by plant service area population (reported) or by
  flow volume proportion

This is the hardest-to-fake indicator. Industrial nitrogen can be separated
(industrial permits are coded separately in NPDES). Human metabolic waste
is a fixed biological constant.

### Method C: Energy Consumption

```
P = Residential_kWh_Sold / Per_Capita_Residential_kWh
P = Total_Residential_Gas_Therms / Per_Capita_Gas_Use
```

- EIA reports electricity sales by sector (residential/commercial/industrial)
- Per-capita residential: ~10,500 kWh/person/year (EIA 2023)
- Adjust for: household size effects, climate zone variation, electrification
  trends
- Natural gas: residential customers × avg household size
- Cross-check: total energy ÷ per-capita total energy use (~300M BTU/person/yr)

### Method D: Waste and Food

```
P = Total_MSW_Generated / Per_Capita_Waste_Rate
P = Total_Food_Supply / Per_Capita_Caloric_Need
```

- EPA: ~4.9 lbs MSW/person/day (2018). Total national tonnage ÷ rate
- USDA ERS: total food availability in kcal. ÷ 2,000-2,500 kcal/person/day
- Grocery sales: total food-at-home spending ÷ ~$4,000/person/year
- SNAP participation ÷ participation rate (~12-14%) as lower bound check

### Method E: Healthcare Utilization

```
P = Total_ER_Visits / Per_Capita_ER_Rate
P = Total_Physician_Visits / Per_Capita_Visit_Rate
P = Total_Hospital_Discharges / Per_Capita_Discharge_Rate
```

- CDC NCHS: ~0.4 ER visits/person/year, ~4 physician visits/person/year
- AHRQ: ~37 hospital discharges per 1000 population
- Total events ÷ rate = population
- Weakness: rates vary by age structure, insurance coverage, access
- Strength: undocumented and uncounted people still go to ERs (EMTALA)

### Method F: Census-Based (LOW weight)

```
P = Census_2020 × (1 + undercount) + births - deaths + net_migration
```

Standard demographic components method. Included for comparison. Weight
capped at 15% of ensemble regardless of its internal precision, because
the base count itself is suspect.

### Method G: Housing and Vehicles

```
P = Housing_Units × Occupancy × Persons_per_Household + Group_Quarters
P = Vehicle_Registrations / Vehicles_per_Adult × Adult_Share
```

- Census housing + permits + USPS growth for unit count
- FHWA registrations: ~283M vehicles. ÷ ~0.85/adult × 0.78 adult share
- Cross-check with EIA residential electric meters

---

## Ensemble Strategy

### Weighting Philosophy

Physical/biological indicators (Methods A-E, G) get 85% of ensemble weight.
Census-based (Method F) gets 15% maximum.

Within the physical methods, weight by:
1. **Independence from census** — methods that use no census input get bonus
2. **Biological fixedness** — per-capita metabolic constants (N, BOD) are
   harder to get wrong than behavioral rates (ER visits, driving)
3. **Coverage completeness** — water/wastewater covers ~99% of population
   (septic systems are the gap); healthcare misses some; food is near-total

### Combination

1. Each method produces: point estimate + uncertainty range per county
2. Precision-weighted mean across methods (with the census cap)
3. Bootstrap uncertainty: resample per-capita rates within published ranges
4. If physical methods cluster at 450-550M and census says 335M, the tool
   reports the physical cluster and flags the discrepancy
5. Hierarchical reconciliation: county → state → national consistency

### Discrepancy Analysis

When methods disagree by >10%, the tool produces a discrepancy report:
- Which methods cluster where
- What per-capita assumptions would reconcile them
- Whether the gap is explainable by known factors (industrial water use,
  commercial electricity, food exports, etc.)

---

## Implementation Phases

### Phase 1: Infrastructure + Water/Wastewater (Methods A, B)
- Project scaffolding
- USGS water use data download (county-level municipal withdrawals)
- EPA NPDES discharge data (facility-level flow + nitrogen/ammonia/BOD)
- EPA ICIS/ECHO facility database
- Per-capita constants with uncertainty ranges
- National + county population from water budget
- National + county population from wastewater chemistry

### Phase 2: Energy and Waste (Methods C, D)
- EIA electricity sales by state/county
- EIA natural gas residential data
- EPA MSW generation data
- USDA ERS food availability
- Population estimates from energy and waste

### Phase 3: Healthcare and Consumption (Method E)
- CDC NCHS hospital/ambulatory utilization
- AHRQ HCUP data
- Pharmacy data
- SNAP participation
- Population from healthcare utilization

### Phase 4: Housing, Vehicles, Geospatial (Method G)
- FHWA vehicle registrations
- Census housing units + permits (used as ratio input, not anchor)
- Building footprints aggregation
- VIIRS nighttime lights

### Phase 5: Census Comparison (Method F)
- Census 2020 + PEP + ACS (low weight)
- Components method for comparison
- Explicit discrepancy report vs physical methods

### Phase 6: Ensemble and Output
- Precision-weighted combination with census cap
- Bootstrap uncertainty
- Hierarchical reconciliation
- Discrepancy analysis
- Final report: CSV + JSON + summary

### Phase 7: Validation and Sensitivity
- Vary per-capita constants ±20%, observe estimate range
- Cross-check: do water and wastewater agree?
- Cross-check: does energy agree with waste?
- Document which assumptions drive the estimate most

---

## Project Structure

```
population-estimator/
├── PLAN.md
├── README.md
├── SOURCE.md
├── pyproject.toml
├── .gitignore
├── config/
│   └── sources.yaml
├── src/
│   └── popest/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── geo.py              # FIPS, crosswalks
│       ├── constants.py        # Per-capita rates with uncertainty
│       ├── water.py            # USGS withdrawals, EPA wastewater
│       ├── energy.py           # EIA electricity, gas
│       ├── waste.py            # EPA MSW, USDA food
│       ├── healthcare.py       # CDC NCHS, AHRQ utilization
│       ├── consumption.py      # SNAP, retail, vehicles
│       ├── census.py           # Census/ACS/PEP (low weight)
│       ├── geospatial.py       # VIIRS, building footprints
│       ├── methods/
│       │   ├── __init__.py
│       │   ├── water_budget.py     # Method A
│       │   ├── wastewater.py       # Method B
│       │   ├── energy.py           # Method C
│       │   ├── waste_food.py       # Method D
│       │   ├── healthcare.py       # Method E
│       │   ├── census_components.py # Method F
│       │   └── housing_vehicles.py  # Method G
│       ├── ensemble.py         # Weighted combination, reconciliation
│       ├── discrepancy.py      # Gap analysis between methods
│       └── report.py           # Output generation
├── data/                       # Raw downloads (gitignored)
├── output/                     # Final estimates (gitignored)
└── tests/
    ├── test_water.py
    ├── test_wastewater.py
    └── test_ensemble.py
```

---

## Key Per-Capita Constants (with uncertainty)

These are the calibration knobs. Each has a published range from engineering
and public health literature.

| Parameter | Central | Range | Source |
|-----------|---------|-------|--------|
| Domestic water use | 90 gal/person/day | 70-120 | EPA, AWWA |
| Wastewater flow | 80 gal/person/day | 60-110 | EPA design manuals |
| Total nitrogen contribution | 11 g N/person/day | 9-14 | Metcalf & Eddy, EPA |
| Ammonia-N contribution | 5 g/person/day | 4-7 | Wastewater engineering texts |
| BOD contribution | 70 g/person/day | 55-90 | Standard design value |
| TSS contribution | 12 g/person/day | 8-18 | Standard design value |
| Residential electricity | 10,500 kWh/person/yr | 9,000-12,500 | EIA |
| MSW generation | 4.9 lbs/person/day | 4.0-5.5 | EPA Facts & Figures |
| Caloric need | 2,200 kcal/person/day | 1,800-2,800 | USDA/WHO |
| ER visit rate | 0.4 visits/person/yr | 0.3-0.5 | CDC NCHS |
| Physician visits | 4.0 visits/person/yr | 3.0-5.0 | CDC NCHS |
| Gasoline use | 390 gal/person/yr | 300-500 | EIA/FHWA |
| Vehicles per adult | 0.85 | 0.75-1.0 | FHWA |

---

## Technical Decisions

- **Language:** Python 3.11+
- **Dependencies:** requests, pandas, numpy, geopandas, rasterio, pyyaml
- **Storage:** Parquet for intermediate data
- **No database.** Files are sufficient.
- **API keys:** Census (free). EPA ECHO (free). USGS (none needed). EIA (free).

---

## Known Limitations

1. **Per-capita constants have real variance** by climate, age structure,
   urbanization. County-level estimates inherit this uncertainty.
2. **Industrial/commercial water and energy** must be separated from
   residential. EIA does this for electricity. USGS partially for water.
3. **Septic systems** (~20% of housing) don't appear in wastewater plant
   data. Must estimate from census housing × septic rate, or from
   groundwater nitrogen studies.
4. **Food exports/imports** complicate the food supply method. USDA ERS
   accounts for this but the data is national only.
5. **Healthcare utilization varies** by insurance status, age, access.
   Undocumented population may underutilize non-emergency care.
6. **Census data used for ratios** (HH size, vacancy, septic rate) still
   introduces some census dependency. Minimize by using engineering defaults
   where possible.
7. **County allocation** of national/state totals requires spatial weights.
   Use water utility service areas and WWTP locations where available.

---

## Success Criteria

- Physical methods (water, wastewater, energy) agree within ±15% of each
  other nationally
- If they agree at a level far above census, report that level with the
  discrepancy flagged
- County estimates sum to state estimates sum to national
- All data fetched programmatically (reproducible)
- Full run completes in <60 minutes
- Output: CSV [FIPS, county, state, estimate, lower_90, upper_90,
  method_contributions]
- Discrepancy report: national summary showing each method's estimate and
  the gap vs census
