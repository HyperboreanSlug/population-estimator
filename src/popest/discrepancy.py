"""Phase 5: Discrepancy analysis between methods and census."""

import pandas as pd


def discrepancy_report(estimates: dict[str, float], census: float) -> pd.DataFrame:
    """Produce discrepancy report: each method vs census.

    Args:
        estimates: method name -> central estimate
        census: census official count
    """
    rows = []
    for method, value in sorted(estimates.items()):
        if value <= 0:
            continue
        diff = value - census
        pct = (diff / census * 100) if census > 0 else 0
        rows.append({
            "method": method,
            "estimate": value,
            "census": census,
            "difference": diff,
            "pct_above_census": pct,
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("estimate", ascending=False).reset_index(drop=True)
    return df
