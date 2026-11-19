"""Method: Medicare aged-beneficiary population estimate.

P = Aged_Beneficiaries / (Aged_Share x Enrollment_Rate)

CMS Medicare enrollment counts nearly all of the 65+ population
(~97% enrollment). The aged-share constant is census-informed, so this
is an administrative voice with modest weight.
"""

import pandas as pd

from popest.constants import MEDICARE_AGED_SHARE
from popest.medicare import MEDICARE_ENROLLMENT_RATE, national_aged_beneficiaries


def estimate_county(county_df: pd.DataFrame) -> pd.DataFrame:
    """County-level population from aged Medicare beneficiaries.

    Same constants as the national voice: aged share 0.155-0.185 x 0.97
    enrollment rate. Returns [fips, pop_medicare_central, low, high].
    """
    if county_df.empty:
        return pd.DataFrame(columns=["fips", "pop_medicare_central",
                                     "pop_medicare_low",
                                     "pop_medicare_high"])
    work = county_df.copy()
    for label, share in [("central", MEDICARE_AGED_SHARE.central),
                         ("low", MEDICARE_AGED_SHARE.high),
                         ("high", MEDICARE_AGED_SHARE.low)]:
        work[f"pop_medicare_{label}"] = (
            work["aged_benes"] / (share * MEDICARE_ENROLLMENT_RATE))
    return work[["fips", "pop_medicare_central", "pop_medicare_low",
                 "pop_medicare_high"]]


def estimate() -> dict:
    """National population from aged Medicare beneficiaries."""
    benes = national_aged_beneficiaries()

    results = {}
    for label, share in [
        ("central", MEDICARE_AGED_SHARE.central),
        ("low", MEDICARE_AGED_SHARE.high),
        ("high", MEDICARE_AGED_SHARE.low),
    ]:
        results[f"medicare_{label}"] = (
            benes["aged_benes"] / (share * MEDICARE_ENROLLMENT_RATE))

    results["aged_benes"] = benes["aged_benes"]
    results["total_benes"] = benes["total_benes"]
    results["as_of"] = f"{benes['year']}-{benes['month']:02d}"
    results["source"] = benes["source"]
    return results
