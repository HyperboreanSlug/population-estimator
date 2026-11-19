"""National-only method collectors.

Each function returns one method's entry {central, low, high, form,
source} or a dict of sub-method results. `add_national`/`add_national_multi`
wrap them with fail-soft handling: a failed source drops that voice and
prints the error, never the run.
"""

from popest.ensemble import METHOD_WEIGHTS


def add_national(methods: dict, name: str, fn) -> None:
    """Run one national method fn() and store it as methods[name]."""
    try:
        entry = fn()
        if entry and entry.get("central", 0) > 0:
            methods[name] = entry
            print(f"  central {entry['central']:,.0f}")
        else:
            print(f"  no data ({name})")
    except Exception as e:
        print(f"  FAILED: {e}")


def add_national_multi(methods: dict, fn, spec: dict) -> None:
    """Run fn() returning {key_central, key_low, key_high} sub-results."""
    try:
        results = fn()
        for name, (key, form, source) in spec.items():
            central = results.get(f"{key}_central", 0)
            if central > 0:
                methods[name] = {
                    "central": central,
                    "low": results.get(f"{key}_low", central),
                    "high": results.get(f"{key}_high", central),
                    "form": form, "source": source,
                }
                print(f"  {name}: {central:,.0f}")
            else:
                print(f"  no data ({name})")
    except Exception as e:
        print(f"  FAILED: {e}")


def energy() -> dict:
    from popest.methods.energy import estimate, national_summary

    s = national_summary(estimate())
    if not s or s.get("central", 0) <= 0:
        return {}
    return {"central": s["central"], "low": s["low"], "high": s["high"],
            "form": "inverse", "source": "EIA SEDS residential kWh 2024"}


def waste_food() -> dict:
    from popest.methods.waste_food import estimate

    return estimate()


def healthcare() -> dict:
    from popest.methods.healthcare import estimate

    r = estimate()
    return {"central": r["er_central"], "low": r["er_low"],
            "high": r["er_high"], "form": "inverse",
            "source": "CDC NCHS ER visits 2021 (published statistics)"}


def vitals() -> dict:
    from popest.methods.vitals import estimate

    r = estimate()
    if not r or r.get("births_central", 0) <= 0:
        return {}
    return {"central": r["births_central"], "low": r["births_low"],
            "high": r["births_high"], "form": "inverse",
            "source": f"births {r['year']}: {r['births_count']:,.0f} "
                      f"({r['births_source']})"}


def consumption() -> dict:
    from popest.consumption import estimate_consumption

    return estimate_consumption()


def irs() -> dict:
    from popest.irs import estimate_from_irs

    r = estimate_from_irs()
    if "error" in r:
        raise RuntimeError(r["error"])
    return {"central": r["irs_central"], "low": r["irs_low"],
            "high": r["irs_high"], "form": "inverse",
            "source": "IRS SOI exemptions TY2022"}


def bls() -> dict:
    from popest.bls import estimate_from_bls

    r = estimate_from_bls()
    if "error" in r:
        raise RuntimeError(r["error"])
    return {"central": r["bls_central"], "low": r["bls_low"],
            "high": r["bls_high"], "form": "inverse",
            "source": "BLS employment (API)"}


def buildings() -> dict:
    from popest.buildings import estimate_from_buildings

    r = estimate_from_buildings()
    return {"central": r["buildings_central"], "low": r["buildings_low"],
            "high": r["buildings_high"], "form": "direct",
            "source": "MS footprints: approximated (Tier-5 validation, "
                      "reported-only)"}


NATIONAL_MULTI_SPEC = {
    "msw": ("msw", "inverse", "EPA MSW 2018 (modeled figure)"),
    "gasoline": ("gasoline", "inverse", "EIA gasoline"),
    "vehicles": ("vehicles", "inverse",
                 "FHWA registrations 2022 (published statistic)"),
    "vmt": ("vmt", "inverse", "FHWA VMT 2024"),
}

CONSUMPTION_SPEC = {
    "snap": ("snap", "inverse", "USDA FNS SNAP FY2025 (annual summary)"),
    "wireless": ("wireless", "inverse",
                 "CTIA 2023 (published estimate, no public dataset)"),
    "grocery": ("grocery", "inverse",
                "Census MARTS 445 food & beverage stores 2025"),
}


def education() -> dict:
    from popest.methods.education import estimate

    r = estimate()
    if not r or r.get("education_central", 0) <= 0:
        return {}
    return {"central": r["education_central"], "low": r["education_low"],
            "high": r["education_high"], "form": "inverse",
            "source": "NCES public K-12 enrollment 2024-25"}


def college() -> dict:
    """Population from IPEDS higher-education enrollment."""
    from popest.constants import COLLEGE_ENROLLMENT_SHARE
    from popest.education import higher_ed_enrollment

    r = higher_ed_enrollment()
    if not r:
        return {}
    return {"central": r["enrollment"] / COLLEGE_ENROLLMENT_SHARE.central,
            "low": r["enrollment"] / COLLEGE_ENROLLMENT_SHARE.high,
            "high": r["enrollment"] / COLLEGE_ENROLLMENT_SHARE.low,
            "form": "inverse",
            "source": f"IPEDS fall {r['year']} enrollment "
                      f"({r['enrollment']:,.0f})"}


def electricity_meters() -> dict:
    from popest.methods.meters import estimate

    r = estimate()
    if not r or r.get("electricity_meters_central", 0) <= 0:
        return {}
    return {"central": r["electricity_meters_central"],
            "low": r["electricity_meters_low"],
            "high": r["electricity_meters_high"], "form": "direct",
            "source": f"EIA-861 meters {r['meters_count']:,.0f} "
                      f"(Bundled+Delivery)"}


def gas_meters() -> dict:
    from popest.methods.meters import estimate

    r = estimate()
    if not r or r.get("gas_meters_central", 0) <= 0:
        return {}
    return {"central": r["gas_meters_central"],
            "low": r["gas_meters_low"],
            "high": r["gas_meters_high"], "form": "direct",
            "source": f"EIA gas customers {r['gas_customers_count']:,.0f} "
                      f"({r['gas_year']})"}


def enplanements() -> dict:
    from popest.methods.travel import estimate

    r = estimate()
    if not r or r.get("enplanements_central", 0) <= 0:
        return {}
    return {"central": r["enplanements_central"],
            "low": r["enplanements_low"],
            "high": r["enplanements_high"], "form": "inverse",
            "source": f"FAA enplanements CY{r['enplanements_year']} "
                      f"({r['enplanements_count']:,.0f})"}


def transit() -> dict:
    from popest.methods.travel import estimate

    r = estimate()
    if not r or r.get("transit_central", 0) <= 0:
        return {}
    return {"central": r["transit_central"],
            "low": r["transit_low"],
            "high": r["transit_high"], "form": "inverse",
            "source": f"NTD unlinked trips {r['transit_year']} "
                      f"({r['transit_trips_count']:,.0f})"}


def library_visits() -> dict:
    from popest.methods.travel import estimate

    r = estimate()
    if not r or r.get("library_visits_central", 0) <= 0:
        return {}
    return {"central": r["library_visits_central"],
            "low": r["library_visits_low"],
            "high": r["library_visits_high"], "form": "inverse",
            "source": f"IMLS visits FY{r['library_fiscal_year']} "
                      f"({r['library_visits_count']:,.0f}); "
                      f"registered borrowers "
                      f"{r['registered_borrowers_reported']:,.0f} reported"}


def medicaid() -> dict:
    """Population from Medicaid+CHIP enrollment."""
    from popest.constants import MEDICAID_ENROLLMENT_SHARE
    from popest.medicaid import medicaid_chip_enrollment

    r = medicaid_chip_enrollment()
    if not r:
        return {}
    return {"central": r["medicaid_chip"] / MEDICAID_ENROLLMENT_SHARE.central,
            "low": r["medicaid_chip"] / MEDICAID_ENROLLMENT_SHARE.high,
            "high": r["medicaid_chip"] / MEDICAID_ENROLLMENT_SHARE.low,
            "form": "inverse",
            "source": f"Medicaid+CHIP {r['year']}-{r['month']:02d}: "
                      f"{r['medicaid_chip']:,.0f} enrolled "
                      f"({r['jurisdictions']} jurisdictions)"}


def hospital_days() -> dict:
    """Population from total hospital inpatient days."""
    from popest.constants import INPATIENT_DAYS_PER_CAPITA
    from popest.healthcare import hospital_cost_report

    r = hospital_cost_report()
    if not r:
        return {}
    return {"central": r["inpatient_days"] / INPATIENT_DAYS_PER_CAPITA.central,
            "low": r["inpatient_days"] / INPATIENT_DAYS_PER_CAPITA.high,
            "high": r["inpatient_days"] / INPATIENT_DAYS_PER_CAPITA.low,
            "form": "inverse",
            "source": f"CMS cost report FY{r['fiscal_year']}: "
                      f"{r['inpatient_days']:,.0f} inpatient days, "
                      f"{r['discharges']:,.0f} discharges (COVID-era year)"}


def drivers() -> dict:
    """Population from FHWA licensed drivers."""
    from popest.constants import ADULT_SHARE, DRIVERS_PER_ADULT
    from popest.drivers import licensed_drivers

    r = licensed_drivers()
    if not r:
        return {}
    return {"central": r["drivers"] / (DRIVERS_PER_ADULT.central
                                       * ADULT_SHARE.central),
            "low": r["drivers"] / (DRIVERS_PER_ADULT.high
                                   * ADULT_SHARE.high),
            "high": r["drivers"] / (DRIVERS_PER_ADULT.low
                                    * ADULT_SHARE.low),
            "form": "inverse",
            "source": f"FHWA licensed drivers {r['year']} "
                      f"({r['drivers']:,.0f})"}


def personal_income() -> dict:
    """Population from BEA total personal income."""
    from popest.bea import national_personal_income
    from popest.constants import PER_CAPITA_INCOME

    r = national_personal_income()
    if not r:
        return {}
    return {"central": r["total_income"] / PER_CAPITA_INCOME.central,
            "low": r["total_income"] / PER_CAPITA_INCOME.high,
            "high": r["total_income"] / PER_CAPITA_INCOME.low,
            "form": "inverse",
            "source": f"BEA personal income {r['year']} "
                      f"(${r['total_income']/1e12:.2f}T)"}


def food_expenditure() -> dict:
    """Population from USDA ERS total food expenditure."""
    from popest.constants import FOOD_EXPENDITURE_PER_CAPITA
    from popest.consumption import food_expenditure as fetch

    r = fetch()
    if not r:
        return {}
    return {"central": r["total_dollars"] / FOOD_EXPENDITURE_PER_CAPITA.central,
            "low": r["total_dollars"] / FOOD_EXPENDITURE_PER_CAPITA.high,
            "high": r["total_dollars"] / FOOD_EXPENDITURE_PER_CAPITA.low,
            "form": "inverse",
            "source": f"ERS food expenditure {r['year']} "
                      f"(${r['total_dollars']/1e12:.2f}T all purchasers)"}


def sdwis() -> dict:
    from popest.methods.sdwis import estimate

    r = estimate()
    if not r or r.get("sdwis_central", 0) <= 0:
        return {}
    return {"central": r["sdwis_central"], "low": r["sdwis_low"],
            "high": r["sdwis_high"], "form": "inverse",
            "source": (f"EPA SDWIS CWS served "
                       f"{r.get('cws_pop_served', 0):,.0f}")}


def deaths() -> dict:
    from popest.methods.vitals import estimate

    r = estimate()
    if not r or r.get("deaths_central", 0) <= 0:
        return {}
    return {"central": r["deaths_central"], "low": r["deaths_low"],
            "high": r["deaths_high"], "form": "inverse",
            "source": f"deaths {r['year']}: {r['deaths_count']:,.0f} "
                      f"({r['deaths_source']})"}


def agi() -> dict:
    """Population from total IRS adjusted gross income."""
    from popest.constants import IRS_AGI_PER_CAPITA
    from popest.irs import load_soi_agi

    r = load_soi_agi()
    if not r or r.get("total_agi", 0) <= 0:
        return {}
    return {"central": r["total_agi"] / IRS_AGI_PER_CAPITA.central,
            "low": r["total_agi"] / IRS_AGI_PER_CAPITA.high,
            "high": r["total_agi"] / IRS_AGI_PER_CAPITA.low,
            "form": "inverse",
            "source": f"IRS SOI total AGI TY2022 (${r['total_agi']:,.0f})"}


def total_energy() -> dict:
    """Population from total primary energy consumption."""
    from popest.constants import TOTAL_ENERGY_PER_CAPITA
    from popest.energy import total_primary_energy

    e = total_primary_energy()
    if not e:
        return {}
    btus = e["quad_btu"] * 1e15
    per_capita = TOTAL_ENERGY_PER_CAPITA.central * 1e6  # million Btu
    low_pc = TOTAL_ENERGY_PER_CAPITA.low * 1e6
    high_pc = TOTAL_ENERGY_PER_CAPITA.high * 1e6
    return {"central": btus / per_capita,
            "low": btus / high_pc,
            "high": btus / low_pc,
            "form": "inverse",
            "source": f"EIA total primary energy {e['year']} "
                      f"({e['quad_btu']:.1f} quad Btu)"}


def gas_volume() -> dict:
    """Population from residential natural gas consumption volume."""
    from popest.constants import GAS_RESIDENTIAL_PER_CAPITA
    from popest.energy import fetch_natural_gas_residential

    g = fetch_natural_gas_residential()
    if g.empty:
        return {}
    cf = g["residential_bcf"].sum() * 1e9
    year = int(g["year"].max())
    return {"central": cf / GAS_RESIDENTIAL_PER_CAPITA.central,
            "low": cf / GAS_RESIDENTIAL_PER_CAPITA.high,
            "high": cf / GAS_RESIDENTIAL_PER_CAPITA.low,
            "form": "inverse",
            "source": f"EIA residential gas {year} "
                      f"({g['residential_bcf'].sum():,.0f} Bcf)"}


def medicare() -> dict:
    from popest.methods.medicare import estimate

    r = estimate()
    if not r or r.get("medicare_central", 0) <= 0:
        return {}
    return {"central": r["medicare_central"], "low": r["medicare_low"],
            "high": r["medicare_high"], "form": "inverse",
            "source": f"CMS Medicare aged beneficiaries {r.get('as_of', '')}"}


def collect_all(methods: dict) -> None:
    """Run every national-only method in order with status echo."""
    add_national(methods, "energy", energy)
    add_national_multi(methods, waste_food, NATIONAL_MULTI_SPEC)
    add_national(methods, "healthcare", healthcare)
    add_national(methods, "vitals", vitals)
    add_national(methods, "vitals_deaths", deaths)
    add_national_multi(methods, consumption, CONSUMPTION_SPEC)
    add_national(methods, "irs", irs)
    add_national(methods, "irs_agi", agi)
    add_national(methods, "bls", bls)
    add_national(methods, "education", education)
    add_national(methods, "college", college)
    add_national(methods, "electricity_meters", electricity_meters)
    add_national(methods, "gas_meters", gas_meters)
    add_national(methods, "enplanements", enplanements)
    add_national(methods, "transit", transit)
    add_national(methods, "library_visits", library_visits)
    add_national(methods, "food_expenditure", food_expenditure)
    add_national(methods, "personal_income", personal_income)
    add_national(methods, "drivers", drivers)
    add_national(methods, "medicaid", medicaid)
    add_national(methods, "hospital_days", hospital_days)
    add_national(methods, "sdwis", sdwis)
    add_national(methods, "medicare", medicare)
    add_national(methods, "total_energy", total_energy)
    add_national(methods, "gas_volume", gas_volume)
    add_national(methods, "buildings", buildings)
