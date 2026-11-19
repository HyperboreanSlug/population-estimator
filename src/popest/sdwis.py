"""EPA SDWIS community water system data client.

Population served by community water systems (CWS): utility-reported
estimated population served per public water system. Summing CWS gives
the population on piped community water; dividing by the published
coverage fraction backs out the total population.

Caveat: utilities estimate served population from connections and
household-size assumptions, so this voice is partially informed by
census-derived household sizes. Physical coverage, administrative
denominator.

Source: data/epa/SDWA_system_search_download.zip -> SDWA_SYSTEM_SEARCH.csv
(columns POPULATION_SERVED_COUNT, PWS_TYPE_CODE, STATE_CODE).
"""

import zipfile
from pathlib import Path

import pandas as pd

SDWIS_ZIP = Path("data/epa/SDWA_system_search_download.zip")


def cws_population_served() -> pd.DataFrame:
    """Community water system population served, by state.

    Returns DataFrame [state, pop_served, n_systems]. PWS_TYPE_CODE
    "CWS" = community water system (year-round residents).
    """
    if not SDWIS_ZIP.exists():
        return pd.DataFrame(columns=["state", "pop_served", "n_systems"])

    with zipfile.ZipFile(SDWIS_ZIP) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".csv"))
        with zf.open(name) as f:
            df = pd.read_csv(f, dtype=str, low_memory=False)

    df["POPULATION_SERVED_COUNT"] = pd.to_numeric(
        df["POPULATION_SERVED_COUNT"], errors="coerce")
    df["PWS_TYPE_CODE"] = df["PWS_TYPE_CODE"].str.strip()
    cws = df[(df["PWS_TYPE_CODE"] == "CWS")
             & df["POPULATION_SERVED_COUNT"].notna()].copy()
    # The search export includes inactive, merged, and converted systems;
    # only Active (A) systems represent currently served population.
    if "PWS_ACTIVITY_CODE" in cws.columns:
        cws = cws[cws["PWS_ACTIVITY_CODE"].str.strip() == "A"]

    state_col = "STATE_CODE" if "STATE_CODE" in cws.columns else "STATE"
    grouped = cws.groupby(state_col, as_index=False).agg(
        pop_served=("POPULATION_SERVED_COUNT", "sum"),
        n_systems=("PWSID", "count"),
    )
    return grouped.rename(columns={state_col: "state"})
