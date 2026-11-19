"""CMS state Medicaid and CHIP enrollment client.

Applications, Eligibility Determinations, and Enrollment Data: monthly
enrollment by jurisdiction. No national row; the national total is the
sum over the 51 jurisdictions for the latest reporting period.

Source: data/medicaid/pi_october2026.csv (fetched through the
operator-authorized VPS route; download.medicaid.gov is DNS-blocked on
the local resolver). Columns 'Total Medicaid and CHIP Enrollment',
'Total Medicaid Enrollment', 'Total CHIP Enrollment',
'Reporting Period' (YYYYMM).
"""

from pathlib import Path

import pandas as pd

PI_CSV = Path("data/medicaid/pi_october2026.csv")


def medicaid_chip_enrollment() -> dict:
    """National Medicaid+CHIP enrollment, latest reporting period."""
    if not PI_CSV.exists():
        return {}
    df = pd.read_csv(PI_CSV, dtype={"Reporting Period": str})
    latest = df["Reporting Period"].max()
    sub = df[df["Reporting Period"] == latest]
    if sub.empty:
        return {}
    year = int(latest[:4])
    month = int(latest[4:])
    return {
        "year": year,
        "month": month,
        "medicaid_chip": float(sub["Total Medicaid and CHIP Enrollment"].sum()),
        "medicaid": float(sub["Total Medicaid Enrollment"].sum()),
        "chip": float(sub["Total CHIP Enrollment"].sum()),
        "jurisdictions": int(len(sub)),
        "source": "data/medicaid/pi_october2026.csv "
                  "(CMS state enrollment data)",
    }
