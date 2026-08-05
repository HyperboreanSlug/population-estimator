"""Phase 3: Healthcare utilization data.

National-level statistics from CDC NCHS and AHRQ.
"""


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
