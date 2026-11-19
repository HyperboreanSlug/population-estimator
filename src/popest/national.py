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
            "source": "CDC NCHS ER visits 2021"}


def vitals() -> dict:
    from popest.methods.vitals import estimate

    r = estimate()
    return {"central": r["births_central"], "low": r["births_low"],
            "high": r["births_high"], "form": "inverse",
            "source": "CDC NCHS births 2022"}


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
            "source": "MS building footprints (5 states verified)"}


NATIONAL_MULTI_SPEC = {
    "msw": ("msw", "inverse", "EPA MSW 2018"),
    "gasoline": ("gasoline", "inverse", "EIA gasoline"),
    "vehicles": ("vehicles", "inverse", "FHWA registrations 2022"),
    "vmt": ("vmt", "inverse", "FHWA VMT 2024"),
}

CONSUMPTION_SPEC = {
    "snap": ("snap", "inverse", "USDA FNS SNAP FY2025 (annual summary)"),
    "wireless": ("wireless", "inverse", "CTIA survey 2023"),
    "grocery": ("grocery", "inverse", "census retail 2023"),
}


def education() -> dict:
    from popest.methods.education import estimate

    r = estimate()
    if not r or r.get("education_central", 0) <= 0:
        return {}
    return {"central": r["education_central"], "low": r["education_low"],
            "high": r["education_high"], "form": "inverse",
            "source": "NCES public K-12 enrollment 2024-25"}


def sdwis() -> dict:
    from popest.methods.sdwis import estimate

    r = estimate()
    if not r or r.get("sdwis_central", 0) <= 0:
        return {}
    return {"central": r["sdwis_central"], "low": r["sdwis_low"],
            "high": r["sdwis_high"], "form": "inverse",
            "source": (f"EPA SDWIS CWS served "
                       f"{r.get('cws_pop_served', 0):,.0f}")}


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
    add_national_multi(methods, consumption, CONSUMPTION_SPEC)
    add_national(methods, "irs", irs)
    add_national(methods, "bls", bls)
    add_national(methods, "education", education)
    add_national(methods, "sdwis", sdwis)
    add_national(methods, "medicare", medicare)
    add_national(methods, "buildings", buildings)
