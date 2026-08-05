"""Method E: Healthcare utilization population estimate.

P = Total_ER_Visits / Per_Capita_ER_Rate
P = Total_Physician_Visits / Per_Capita_Visit_Rate
P = Total_Hospital_Discharges / Per_Capita_Discharge_Rate
"""

import pandas as pd

from popest.constants import ER_VISIT_RATE, PHYSICIAN_VISIT_RATE
from popest.healthcare import healthcare_utilization_national

DISCHARGE_RATE_CENTRAL = 0.37
DISCHARGE_RATE_LOW = 0.30
DISCHARGE_RATE_HIGH = 0.45


def estimate() -> dict:
    """Produce national population estimates from healthcare utilization."""
    hc = healthcare_utilization_national()
    results = {}

    for label, rate in [("central", ER_VISIT_RATE.central),
                        ("low", ER_VISIT_RATE.high),
                        ("high", ER_VISIT_RATE.low)]:
        results[f"er_{label}"] = hc["er_visits_total"] / rate

    for label, rate in [("central", PHYSICIAN_VISIT_RATE.central),
                        ("low", PHYSICIAN_VISIT_RATE.high),
                        ("high", PHYSICIAN_VISIT_RATE.low)]:
        results[f"physician_{label}"] = hc["physician_visits_total"] / rate

    for label, rate in [("central", DISCHARGE_RATE_CENTRAL),
                        ("low", DISCHARGE_RATE_HIGH),
                        ("high", DISCHARGE_RATE_LOW)]:
        results[f"discharge_{label}"] = hc["hospital_discharges_total"] / rate

    return results


def summary_table(results: dict) -> pd.DataFrame:
    rows = []
    methods = set(k.rsplit("_", 1)[0] for k in results)
    for method in sorted(methods):
        row = {"method": method}
        for label in ["central", "low", "high"]:
            row[label] = results.get(f"{method}_{label}", 0)
        rows.append(row)
    return pd.DataFrame(rows)
