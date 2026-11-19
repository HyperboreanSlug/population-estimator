"""Healthcare utilization data.

- Literature constants for ER/physician/discharge rates (CDC NCHS/
  AHRQ published totals; no bulk source).
- REAL inpatient utilization from the CMS Hospital Provider Cost
  Report (FY2021 final): total inpatient days and discharges across
  6,058 Medicare-certified hospitals. FY2021 is a COVID-utilization
  year (~10-15% below trend); the caveat is carried in the source
  label. Medicare-certified facilities exclude VA/military/IHS
  hospitals; the per-capita constant absorbs that gap.
"""

HCR_CSV = "data/cms/hcr_2021.csv"


def hospital_cost_report() -> dict:
    """Total inpatient days, discharges, and beds, FY2021.

    Source: data/cms/hcr_2021.csv (CMS Hospital Provider Cost Report
    2021 Final, 4.1MB; fetched via the authorized VPS route).
    """
    from pathlib import Path

    import pandas as pd

    path = Path(HCR_CSV)
    if not path.exists():
        return {}
    df = pd.read_csv(path, low_memory=False)
    days = pd.to_numeric(
        df["Total Days (V + XVIII + XIX + Unknown)"],
        errors="coerce").sum()
    discharges = pd.to_numeric(
        df["Total Discharges (V + XVIII + XIX + Unknown)"],
        errors="coerce").sum()
    beds = pd.to_numeric(df["Number of Beds"], errors="coerce").sum()
    return {
        "fiscal_year": 2021,
        "hospitals": int(len(df)),
        "inpatient_days": float(days),
        "discharges": float(discharges),
        "beds": float(beds),
        "source": "data/cms/hcr_2021.csv (CMS Hospital Provider Cost "
                  "Report FY2021 Final)",
    }


def healthcare_utilization_national() -> dict:
    """CDC NCHS / AHRQ healthcare utilization statistics.

    Sources:
    - CDC NCHS Ambulatory Care Visits (2021)
    - AHRQ HCUP National Inpatient Sample (2021)
    - CDC NCHS Hospital Emergency Room Visits (2021)
    """
    return {
        "year": 2021,
        "er_visits_total": 130_000_000,
        "er_visits_source": "CDC NCHS NHAMCS 2021",
        "physician_visits_total": 1_300_000_000,
        "physician_visits_source": "CDC NCHS NAMCS 2021",
        "hospital_discharges_total": 120_000_000,
        "hospital_discharges_source": "AHRQ HCUP NIS 2021",
        "hospital_beds_total": 920_000,
        "hospital_beds_source": "AHA Annual Survey 2021",
    }
