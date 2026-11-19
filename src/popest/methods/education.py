"""Method: public K-12 enrollment population estimate.

P = Public_Enrollment / Enrollment_Share_of_Population

NCES counts every enrolled public school student. The enrollment share
constant is census-informed, so this is an administrative voice with
modest ensemble weight. NSLP and WIC participation are reported
alongside (not ensemble-weighted; they share the school-age
denominator structure).
"""

import pandas as pd

from popest.constants import EDUCATION_ENROLLMENT_SHARE
from popest.education import (
    nslp_participation,
    public_enrollment,
    wic_participation,
)


def estimate() -> dict:
    """National population from public K-12 enrollment."""
    enroll = public_enrollment()
    if enroll.empty:
        return {}
    total = float(enroll["enrollment"].sum())

    results = {}
    for label, share in [
        ("central", EDUCATION_ENROLLMENT_SHARE.central),
        ("low", EDUCATION_ENROLLMENT_SHARE.high),
        ("high", EDUCATION_ENROLLMENT_SHARE.low),
    ]:
        results[f"education_{label}"] = total / share

    nslp = nslp_participation()
    if nslp:
        results["reported_nslp_participants"] = nslp["value"]
        results["reported_nslp_year"] = nslp["year"]
    wic = wic_participation()
    if wic:
        results["reported_wic_participants"] = wic["value"]
        results["reported_wic_year"] = wic["year"]
    results["reported_note"] = (
        "NSLP/WIC participation reported, not weighted (school-age "
        "denominator overlaps the enrollment voice)")
    return results


def national_summary(results: dict) -> dict:
    return {"enrollment_share": EDUCATION_ENROLLMENT_SHARE.central,
            "central": results.get("education_central", 0.0)}


def reported_only() -> dict:
    """Reported child-nutrition voices (no ensemble weight)."""
    out = {}
    nslp = nslp_participation()
    if nslp:
        out[f"NSLP FY{nslp['year']} avg daily participation"] = nslp["value"]
    wic = wic_participation()
    if wic:
        out[f"WIC FY{wic['year']} total participants"] = wic["value"]
    sb = school_breakfast()
    if sb:
        out[f"School Breakfast FY{sb['year']} total participation (M)"] = \
            sb["participation_millions"]
    return out
