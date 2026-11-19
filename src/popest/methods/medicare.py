"""Method: Medicare aged-beneficiary population estimate.

P = Aged_Beneficiaries / (Aged_Share x Enrollment_Rate)

CMS Medicare enrollment counts nearly all of the 65+ population
(~97% enrollment). The aged-share constant is census-informed, so this
is an administrative voice with modest weight.
"""

from popest.constants import MEDICARE_AGED_SHARE
from popest.medicare import MEDICARE_ENROLLMENT_RATE, national_aged_beneficiaries


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
