"""CLI entry point for population estimator."""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="popest",
        description="Multi-source US population estimation",
    )
    sub = parser.add_subparsers(dest="command")

    water_p = sub.add_parser("water", help="Run water budget method")
    water_p.add_argument("--no-cache", action="store_true")

    ww_p = sub.add_parser("wastewater", help="Run wastewater flow method")
    ww_p.add_argument("--no-cache", action="store_true")

    run_p = sub.add_parser("run", help="Run full pipeline")
    run_p.add_argument("--method", choices=["water", "wastewater", "all"], default="all")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "water":
        _run_water(not args.no_cache)
    elif args.command == "wastewater":
        _run_wastewater(not args.no_cache)
    elif args.command == "run":
        _run_water(True)
        _run_wastewater(True)


def _run_water(use_cache: bool):
    from popest.water import fetch_water_use_2015
    from popest.methods.water_budget import estimate, national_summary

    print("Fetching USGS county water use data (2015)...")
    raw = fetch_water_use_2015(use_cache=use_cache)
    print(f"  Loaded {len(raw)} county records")

    print("Computing water budget population estimate...")
    result = estimate(raw)
    summary = national_summary(result)

    print(f"\n{'='*50}")
    print(f"  WATER BUDGET POPULATION ESTIMATE (2015 data)")
    print(f"{'='*50}")
    print(f"  Counties analyzed:  {summary['counties']}")
    print(f"  Total PS withdraw:  {summary['total_ps_mgal_d']:,.0f} Mgal/d")
    print(f"  Total DOM withdraw: {summary['total_dom_mgal_d']:,.0f} Mgal/d")
    print(f"  Avg USGS implied per-capita: {summary['avg_usgs_implied_gpcd']:.1f} gal/person/day")
    print(f"")
    print(f"  Our estimate (central):  {summary['central']:>15,.0f}")
    print(f"  Our estimate (low):      {summary['low_pop']:>15,.0f}")
    print(f"  Our estimate (high):     {summary['high_pop']:>15,.0f}")
    print(f"  USGS official:           {summary['usgs_official']:>15,.0f}")
    print(f"{'='*50}")

    if summary["usgs_official"] > 0:
        ratio = summary["central"] / summary["usgs_official"]
        print(f"\n  Ratio (ours / USGS): {ratio:.3f}")

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "water_budget_2015.csv"
    result.to_csv(out_path, index=False)
    print(f"\n  County detail saved: {out_path}")


def _run_wastewater(use_cache: bool):
    from popest.wastewater import (
        download_npdes_part1,
        extract_municipal_wwtps,
        get_design_flow,
        load_npdes_facilities,
    )
    from popest.methods.wastewater import estimate, national_summary

    print("Downloading EPA ICIS-NPDES data...")
    zip_path = download_npdes_part1(use_cache=use_cache)

    print("Loading facility and permit tables...")
    fac_df, permit_df, names = load_npdes_facilities(zip_path)
    print(f"  Facility rows: {len(fac_df)}, Permit rows: {len(permit_df)}")
    print(f"  Files in ZIP: {names[:10]}")

    print("Filtering municipal WWTPs...")
    wwtps = extract_municipal_wwtps(fac_df, permit_df)
    print(f"  Municipal WWTPs found: {len(wwtps)}")

    print("Extracting design flows...")
    flow_df = get_design_flow(wwtps, permit_df)
    print(f"  Facilities with flow data: {len(flow_df)}")

    print("Computing wastewater population estimate...")
    result = estimate(flow_df)
    summary = national_summary(result)

    print(f"\n{'='*50}")
    print(f"  WASTEWATER FLOW POPULATION ESTIMATE")
    print(f"{'='*50}")
    print(f"  Counties:          {summary.get('counties', 0)}")
    print(f"  Central:           {summary.get('central', 0):>15,.0f}")
    print(f"  Low:               {summary.get('low', 0):>15,.0f}")
    print(f"  High:              {summary.get('high', 0):>15,.0f}")
    print(f"{'='*50}")

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "wastewater_flow.csv"
    result.to_csv(out_path, index=False)
    print(f"\n  County detail saved: {out_path}")


if __name__ == "__main__":
    main()
