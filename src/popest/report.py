"""Output writers for the full pipeline run.

Files written to output/:
    counties.csv      per-county ensemble with 90% endpoints and
                      per-method contributions
    states.csv        state rollup of covered counties
    national.csv      ensemble, bootstrap 90% CI, census comparison
    discrepancy_report.csv  every method vs census
    summary.txt       human-readable report
"""

from pathlib import Path

import pandas as pd

from popest.geo import STATE_FIPS

OUTPUT = Path("output")


def _ensure_dir() -> Path:
    OUTPUT.mkdir(exist_ok=True)
    return OUTPUT


def write_counties(county_df: pd.DataFrame, names: pd.DataFrame) -> Path:
    """Counties CSV. Names come from USGS county labels or census NAME."""
    df = county_df.copy()
    if not names.empty:
        df = df.merge(names, on="fips", how="left")
    df["state_fips"] = df["fips"].astype(str).str.zfill(5).str[:2]
    df["state"] = df["state_fips"].map(STATE_FIPS)
    front = ["fips", "county", "state", "ensemble_pop",
             "ensemble_low", "ensemble_high", "n_methods"]
    contribs = sorted(c for c in df.columns if c.startswith("contrib_"))
    pops = sorted(c for c in df.columns if c.startswith("pop_"))
    df = df[front + contribs + pops]
    df = df.sort_values("fips").reset_index(drop=True)
    path = _ensure_dir() / "counties.csv"
    df.to_csv(path, index=False)
    return path


def write_states(states_df: pd.DataFrame) -> Path:
    df = states_df.copy()
    df["state"] = df["state_fips"].map(STATE_FIPS)
    df = df.sort_values("state_fips").reset_index(drop=True)
    path = _ensure_dir() / "states.csv"
    df.to_csv(path, index=False)
    return path


def write_national(national: pd.DataFrame) -> Path:
    path = _ensure_dir() / "national.csv"
    national.to_csv(path, index=False)
    return path


def write_discrepancy(disc: pd.DataFrame) -> Path:
    path = _ensure_dir() / "discrepancy_report.csv"
    disc.to_csv(path, index=False)
    return path


def write_reconciliation(rec: pd.DataFrame) -> Path:
    path = _ensure_dir() / "reconciliation.csv"
    rec.to_csv(path, index=False)
    return path


def write_summary(lines: list[str]) -> Path:
    path = _ensure_dir() / "summary.txt"
    path.write_text("\n".join(lines) + "\n")
    return path


def method_table(estimates: dict[str, dict], contributions: dict) -> str:
    """Formatted per-method lines for the summary."""
    out = []
    for name in sorted(contributions,
                       key=lambda m: -contributions[m]["value"]):
        info = estimates.get(name, {})
        value = contributions[name]["value"]
        share = contributions[name]["weighted_share"]
        low = info.get("low", 0.0)
        high = info.get("high", 0.0)
        src = info.get("source", "")
        rng = f" ({low:,.0f} - {high:,.0f})" if low and high else ""
        out.append(f"  {name:<16} {value:>15,.0f}  w={share:.3f}"
                   f"{rng}  {src}")
    return "\n".join(out)
