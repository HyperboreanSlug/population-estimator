"""Method B: Wastewater chemistry population estimate.

P = Monitored_Pollutant_Load / Per_Capita_Contribution

Municipal WWTPs report monitored effluent loads (BOD5, TSS, nitrogen,
ammonia) under NPDES DMRs. Human metabolic contributions are fixed
biological constants, so the load backs out the population the plant
serves. Industrial dischargers (non-SIC 4952) are excluded.

Primary parameter: BOD5 (largest reporting base). County allocation via
the ICIS_FACILITIES permit -> county crosswalk. This measures only the
population connected to load-reporting municipal plants; it is a partial
coverage method by construction.
"""

import pandas as pd

from popest.constants import (
    AMMONIA_N,
    BOD5,
    GRAMS_PER_LB,
    NITROGEN_TOTAL,
    TSS,
)


def _pop_from_loads(loads_lb_d: float, pc: object) -> float:
    """Population from total load (lb/d) given per-capita grams/day."""
    return loads_lb_d * GRAMS_PER_LB / pc.central


def estimate(facility_loads: pd.DataFrame,
             county_map: pd.DataFrame,
             municipal_ids: set[str]) -> pd.DataFrame:
    """County-level population from municipal BOD5 loads.

    Args:
        facility_loads: from dmr.facility_loads() [EXTERNAL_PERMIT_NMBR,
            BOD5_lb_d, ...]
        county_map: from dmr.facility_county_map() [EXTERNAL_PERMIT_NMBR,
            fips]
        municipal_ids: from dmr.municipal_permit_ids()

    Returns DataFrame [fips, bod_lb_d, n_facilities,
    pop_chem_central, pop_chem_low, pop_chem_high].
    """
    if facility_loads.empty or "BOD5_lb_d" not in facility_loads.columns:
        return pd.DataFrame(columns=[
            "fips", "bod_lb_d", "n_facilities",
            "pop_chem_central", "pop_chem_low", "pop_chem_high",
        ])

    muni = facility_loads[
        facility_loads["EXTERNAL_PERMIT_NMBR"].isin(municipal_ids)
    ].copy()
    muni = muni.merge(county_map, on="EXTERNAL_PERMIT_NMBR", how="inner")
    muni = muni.dropna(subset=["BOD5_lb_d"])
    muni = muni[muni["BOD5_lb_d"] > 0]
    if muni.empty:
        return pd.DataFrame(columns=[
            "fips", "bod_lb_d", "n_facilities",
            "pop_chem_central", "pop_chem_low", "pop_chem_high",
        ])

    g = muni.groupby("fips", as_index=False).agg(
        bod_lb_d=("BOD5_lb_d", "sum"),
        n_facilities=("EXTERNAL_PERMIT_NMBR", "count"),
    )
    # low/high populations invert the per-capita range: more waste per
    # person -> fewer people implied by the same load.
    g["pop_chem_central"] = g["bod_lb_d"] * GRAMS_PER_LB / BOD5.central
    g["pop_chem_low"] = g["bod_lb_d"] * GRAMS_PER_LB / BOD5.high
    g["pop_chem_high"] = g["bod_lb_d"] * GRAMS_PER_LB / BOD5.low
    return g


def national_summary(county_df: pd.DataFrame,
                    facility_loads: pd.DataFrame,
                    municipal_ids: set[str]) -> dict:
    """National totals per parameter, each against its own constant."""
    summary = {"counties": int(len(county_df)),
               "bod_facilities": int(county_df["n_facilities"].sum())
               if not county_df.empty else 0}
    if not county_df.empty:
        summary["bod_lb_d"] = float(county_df["bod_lb_d"].sum())
        summary["bod_pop"] = float(county_df["pop_chem_central"].sum())

    muni = facility_loads[
        facility_loads["EXTERNAL_PERMIT_NMBR"].isin(municipal_ids)
    ]
    for col, const in [
        ("BOD5_lb_d", BOD5), ("TSS_lb_d", TSS),
        ("Total N_lb_d", NITROGEN_TOTAL), ("Ammonia-N_lb_d", AMMONIA_N),
    ]:
        if col in muni.columns:
            total = float(muni[col].dropna().clip(lower=0).sum())
            n = int(muni[col].notna().sum())
            if total > 0 and n > 0:
                name = col.replace("_lb_d", "")
                summary[f"{name}_lb_d"] = total
                summary[f"{name}_pop"] = total * GRAMS_PER_LB / const.central
                summary[f"{name}_facilities"] = n
    return summary
