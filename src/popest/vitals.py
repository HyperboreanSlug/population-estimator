"""Vital statistics client.

Births and deaths for the target year come from the Census PEP county
file (NCHS vital records with Census-vintage adjustments), falling
back to the published NCHS 2022 finals when the file is absent.

Note: PEP 2022 births (3,680,380, BIRTHS2022 SUMLEV 50) differ from the
NCHS 2022 final (3,667,758) by 0.34%; the PEP posting applies
Census-vintage adjustments. The vitals method cites whichever it uses.
The old CDC WONDER live pull is superseded by these columns (same
underlying vital records).
"""

NCHS_2022_BIRTHS_FINAL = 3_667_758  # CDC NCHS final report
NCHS_2022_DEATHS_FINAL = 3_282_114  # CDC NCHS 2022 final


def national_births(year: int = 2024) -> dict:
    """Births for the target year from the PEP county file."""
    from popest.census import fetch_census_pep_vitals

    v = fetch_census_pep_vitals(year)
    if v.get("year_used"):
        return {"count": v["births"], "year": v["year_used"],
                "source": f"Census PEP BIRTHS{v['year_used']} (NCHS-derived)"}
    return {"count": NCHS_2022_BIRTHS_FINAL, "year": 2022,
            "source": "CDC NCHS 2022 final (PEP file not downloaded)"}


def national_deaths(year: int = 2024) -> dict:
    """Deaths for the target year from the PEP county file."""
    from popest.census import fetch_census_pep_vitals

    v = fetch_census_pep_vitals(year)
    if v.get("year_used"):
        return {"count": v["deaths"], "year": v["year_used"],
                "source": f"Census PEP DEATHS{v['year_used']} (NCHS-derived)"}
    return {"count": NCHS_2022_DEATHS_FINAL, "year": 2022,
            "source": "CDC NCHS 2022 final (PEP file not downloaded)"}


def national_births_2022() -> int:
    return NCHS_2022_BIRTHS_FINAL


def national_deaths_2022() -> int:
    return NCHS_2022_DEATHS_FINAL
