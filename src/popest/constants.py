"""Per-capita constants with uncertainty ranges.

Each constant has a central value and a plausible range from engineering
and public health literature. These are the calibration knobs for the
physical estimation methods.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PerCapitaConstant:
    central: float
    low: float
    high: float
    unit: str
    source: str


WATER_USE_PUBLIC_SUPPLY_TOTAL = PerCapitaConstant(
    central=120.0,
    low=95.0,
    high=160.0,
    unit="gal/person/day",
    source="Total public supply withdrawal per person served. Includes residential (~65%), commercial (~20%), industrial (~5%), public/losses (~10%). EPA/AWWA/USGS.",
)

WATER_USE_DOMESTIC_SELF_SUPPLIED = PerCapitaConstant(
    central=85.0,
    low=65.0,
    high=110.0,
    unit="gal/person/day",
    source="USGS domestic water use studies. Private wells.",
)

WASTEWATER_FLOW = PerCapitaConstant(
    central=80.0,
    low=60.0,
    high=110.0,
    unit="gal/person/day",
    source="Metcalf & Eddy wastewater engineering. Design basis.",
)

NITROGEN_TOTAL = PerCapitaConstant(
    central=11.0,
    low=9.0,
    high=14.0,
    unit="g N/person/day",
    source="EPA design manuals. Urine dominates (~10g urea-N).",
)

AMMONIA_N = PerCapitaConstant(
    central=5.0,
    low=4.0,
    high=7.0,
    unit="g NH3-N/person/day",
    source="Wastewater engineering texts. Subset of total N.",
)

BOD5 = PerCapitaConstant(
    central=70.0,
    low=55.0,
    high=90.0,
    unit="g BOD5/person/day",
    source="Standard design value. 60-80 typical range.",
)

TSS = PerCapitaConstant(
    central=12.0,
    low=8.0,
    high=18.0,
    unit="g TSS/person/day",
    source="Standard design value.",
)

ELECTRICITY_RESIDENTIAL = PerCapitaConstant(
    central=4200.0,
    low=3500.0,
    high=5200.0,
    unit="kWh/person/year",
    source="EIA RECS 2020: ~10,500 kWh average site consumption per "
           "HOUSEHOLD; average household ~2.5 people (RECS) gives "
           "~4,200 kWh/person. The 10,500 figure is per household, not "
           "per person; using it per person understated population ~2.5x.",
)

MSW_GENERATION = PerCapitaConstant(
    central=4.9,
    low=4.0,
    high=5.5,
    unit="lbs/person/day",
    source="EPA Facts and Figures 2018.",
)

CALORIC_NEED = PerCapitaConstant(
    central=2200.0,
    low=1800.0,
    high=2800.0,
    unit="kcal/person/day",
    source="USDA/WHO dietary reference.",
)

ER_VISIT_RATE = PerCapitaConstant(
    central=0.4,
    low=0.3,
    high=0.5,
    unit="visits/person/year",
    source="CDC NCHS ambulatory care surveys.",
)

PHYSICIAN_VISIT_RATE = PerCapitaConstant(
    central=4.0,
    low=3.0,
    high=5.0,
    unit="visits/person/year",
    source="CDC NCHS.",
)

GASOLINE_USE = PerCapitaConstant(
    central=390.0,
    low=300.0,
    high=500.0,
    unit="gal/person/year",
    source="EIA/FHWA. Total gasoline / population.",
)

VEHICLES_PER_ADULT = PerCapitaConstant(
    central=0.85,
    low=0.75,
    high=1.0,
    unit="vehicles/adult",
    source="FHWA registration data.",
)

PUBLIC_SUPPLY_RESIDENTIAL_FRACTION = PerCapitaConstant(
    central=0.65,
    low=0.55,
    high=0.75,
    unit="fraction",
    source="AWWA. Residential share of public supply deliveries.",
)

EDUCATION_ENROLLMENT_SHARE = PerCapitaConstant(
    central=0.147,
    low=0.140,
    high=0.155,
    unit="fraction of population",
    source="NCES public K-12 enrollment as share of total population, "
           "recent published levels (49.6M / 340M = 14.6% in 2024-25). "
           "Census-informed denominator: administrative voice, modest weight.",
)

CWS_COVERAGE_FRACTION = PerCapitaConstant(
    central=0.85,
    low=0.82,
    high=0.88,
    unit="fraction of population",
    source="USGS National Water Use: population served by community "
           "water systems (~85%); remainder on domestic wells/septic.",
)

MEDICARE_AGED_SHARE = PerCapitaConstant(
    central=0.17,
    low=0.155,
    high=0.185,
    unit="fraction of population",
    source="Population aged 65+ share. Census-informed published range; "
           "Medicare enrollment among 65+ is ~97% (CMS).",
)

VMT_PER_PERSON = PerCapitaConstant(
    central=9700.0,
    low=8500.0,
    high=11000.0,
    unit="miles/person/year",
    source="FHWA vehicle miles traveled per capita. Census-informed "
           "denominator (like gasoline); behavioral voice with modest "
           "weight. 2024 total: 3.294T miles.",
)

IRS_AGI_PER_CAPITA = PerCapitaConstant(
    central=44500.0,
    low=38000.0,
    high=52000.0,
    unit="dollars/person/year",
    source="IRS SOI total AGI / population (~$14.8T / 333M in 2022). "
           "Census-informed denominator; behavioral-administrative voice "
           "with modest weight.",
)

TOTAL_ENERGY_PER_CAPITA = PerCapitaConstant(
    central=284.0,
    low=250.0,
    high=320.0,
    unit="million Btu/person/year",
    source="EIA total primary energy per capita (state energy office "
           "published ~284 MMBtu). Census-informed denominator; "
           "cross-check voice.",
)

GAS_RESIDENTIAL_PER_CAPITA = PerCapitaConstant(
    central=13100.0,
    low=9000.0,
    high=18000.0,
    unit="cubic feet/person/year",
    source="EIA residential natural gas deliveries / population "
           "(4.39 Tcf / 334M in 2024 = ~13,100 cf). Census-informed "
           "denominator; heating-climate variance is wide.",
)

PERSONS_PER_METER = PerCapitaConstant(
    central=2.40,
    low=2.10,
    high=2.70,
    unit="persons/residential meter",
    source="Persons per residential electricity meter (EIA-861 "
           "Bundled+Delivery customers). ~2.5 persons per occupied "
           "household discounted ~5% for seasonal/vacant units with "
           "meters. Census-informed denominator; physical meter count.",
)

GAS_PERSONS_PER_CUSTOMER = PerCapitaConstant(
    central=4.25,
    low=3.50,
    high=5.20,
    unit="persons/gas customer",
    source="Persons per residential gas customer: ~2.5 persons/household "
           "/ ~0.59 share of households with delivered gas (RECS ~61% "
           "use gas). Census-informed denominator; physical meter count.",
)

ENPLANEMENTS_PER_CAPITA = PerCapitaConstant(
    central=2.80,
    low=2.30,
    high=3.40,
    unit="boardings/person/year",
    source="FAA commercial enplanements per capita. Census-informed "
           "denominator; metered security screenings.",
)

TRANSIT_TRIPS_PER_CAPITA = PerCapitaConstant(
    central=22.0,
    low=15.0,
    high=32.0,
    unit="trips/person/year",
    source="NTD unlinked passenger trips per capita. Very wide range "
           "(urbanization); smallest weight.",
)

COLLEGE_ENROLLMENT_SHARE = PerCapitaConstant(
    central=0.056,
    low=0.050,
    high=0.062,
    unit="fraction of population",
    source="IPEDS fall enrollment in degree-granting institutions as "
           "share of population. Census-informed denominator.",
)

FOOD_EXPENDITURE_PER_CAPITA = PerCapitaConstant(
    central=7400.0,
    low=6300.0,
    high=8600.0,
    unit="dollars/person/year",
    source="USDA ERS all-purchaser nominal food expenditure per capita. "
           "Census-informed denominator.",
)

LIBRARY_VISITS_PER_CAPITA = PerCapitaConstant(
    central=2.40,
    low=1.70,
    high=3.10,
    unit="visits/person/year",
    source="IMLS public library visits per capita. Census-informed "
           "denominator; wide local variance.",
)

GAL_PER_MGAL = 1_000_000.0
GRAMS_PER_LB = 453.592
MGD_TO_GAL_DAY = 1_000_000.0
