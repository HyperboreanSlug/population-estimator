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
    central=10500.0,
    low=9000.0,
    high=12500.0,
    unit="kWh/person/year",
    source="EIA 2023 residential sales / population.",
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

GAL_PER_MGAL = 1_000_000.0
GRAMS_PER_LB = 453.592
MGD_TO_GAL_DAY = 1_000_000.0
