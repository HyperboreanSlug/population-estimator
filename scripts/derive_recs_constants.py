#!/usr/bin/env python3
"""Derive per-capita constants from RECS 2020 microdata.

Reproduces the survey-derived constants in src/popest/constants.py:

- ELECTRICITY_RESIDENTIAL: weighted total kWh / weighted total persons
  (10,565.8 kWh/hh / 2.44 persons/hh = 4,330.5 kWh/person)
- PERSONS_PER_METER basis: weighted average persons per occupied
  household (2.44); the meter constant applies a separate 0.95
  seasonal/vacant discount that RECS cannot measure.

The naive approach (unweighted mean KWH / unweighted mean household
size, or NUMCHILD+NUMADULT sums instead of NHSLDMEM) gives wrong
answers: this script exists so the derivation is checkable.

Data: data/eia/recs2020_public_v7.csv
Download: https://www.eia.gov/consumption/residential/data/2020/csv/recs2020_public_v7.csv
(56 MB; scanned through the download gate before use)

Usage: python scripts/derive_recs_constants.py
"""
import csv
from pathlib import Path

RECS = Path("data/eia/recs2020_public_v7.csv")


def main() -> int:
    if not RECS.exists():
        print(f"missing {RECS}; download it first (see docstring)")
        return 1

    n = 0
    sum_w = 0.0
    sum_size_w = 0.0
    sum_kwh_w = 0.0
    sum_size_u = 0
    sum_kwh_u = 0.0
    gas_service_n = 0

    with open(RECS, newline="") as f:
        for r in csv.DictReader(f):
            try:
                w = float(r["NWEIGHT"])
                size = int(r["NHSLDMEM"])
                kwh = float(r["KWH"])
                ugas = int(r["UGASHERE"])
            except (ValueError, KeyError):
                continue
            if size <= 0 or size > 20:
                continue
            n += 1
            sum_w += w
            sum_size_w += size * w
            sum_kwh_w += kwh * w
            sum_size_u += size
            sum_kwh_u += kwh
            if ugas == 1:
                gas_service_n += 1

    avg_size_w = sum_size_w / sum_w
    per_capita = sum_kwh_w / sum_size_w

    print(f"n households: {n}")
    print(f"weighted avg household size (NHSLDMEM): {avg_size_w:.4f}")
    print(f"unweighted avg household size:          "
          f"{sum_size_u / n:.4f}")
    print(f"weighted avg kWh per household:          "
          f"{sum_kwh_w / sum_w:,.1f}")
    print(f"unweighted avg kWh per household:       "
          f"{sum_kwh_u / n:,.1f}")
    print()
    print(f"ELECTRICITY_RESIDENTIAL central: {per_capita:,.1f} "
          f"kWh/person/year")
    print(f"PERSONS_PER_METER basis (x0.95 discount): "
          f"{avg_size_w * 0.95:.3f}")
    print()
    print(f"gas SERVICE share (UGASHERE==1): {gas_service_n / n:.4f} "
          f"of households (meter-basis constant NOT derivable from "
          f"RECS: master-metering breaks the household bridge)")

    # cross-check against the constants module
    from popest.constants import (ELECTRICITY_RESIDENTIAL,
                                  PERSONS_PER_METER)
    ok_e = abs(per_capita - ELECTRICITY_RESIDENTIAL.central) < 1.0
    ok_m = abs(avg_size_w * 0.95 - PERSONS_PER_METER.central) < 0.01
    print()
    print(f"ELECTRICITY_RESIDENTIAL matches module: {ok_e}")
    print(f"PERSONS_PER_METER matches module:      {ok_m}")
    return 0 if (ok_e and ok_m) else 1


if __name__ == "__main__":
    raise SystemExit(main())
