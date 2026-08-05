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

    energy_p = sub.add_parser("energy", help="Run energy consumption method")

    waste_p = sub.add_parser("waste", help="Run waste/food/vehicle methods")

    run_p = sub.add_parser("run", help="Run full pipeline")
    run_p.add_argument("--method", choices=["water", "wastewater", "energy", "waste", "all"], default="all")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "water":
        _run_water(not args.no_cache)
    elif args.command == "wastewater":
        _run_wastewater(not args.no_cache)
    elif args.command == "energy":
        _run_energy()
    elif args.command == "waste":
        _run_waste()
    elif args.command == "run":
        _run_water(True)
        _run_energy()
        _run_waste()


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
    from popest.wastewater import download_npdes_part1, load_municipal_flows
    from popest.methods.wastewater import estimate, national_summary

    print("Downloading EPA ICIS-NPDES data...")
    zip_path = download_npdes_part1(use_cache=use_cache)

    print("Loading and joining municipal WWTP data...")
    flow_df = load_municipal_flows(zip_path)

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


def _run_energy():
    from popest.methods.energy import estimate, national_summary

    print("Computing energy consumption population estimate...")
    result = estimate()
    summary = national_summary(result)

    print(f"\n{'='*50}")
    print(f"  ENERGY (ELECTRICITY) POPULATION ESTIMATE")
    print(f"{'='*50}")
    print(f"  States:            {summary.get('states', 0)}")
    print(f"  Central:           {summary.get('central', 0):>15,.0f}")
    print(f"  Low:               {summary.get('low', 0):>15,.0f}")
    print(f"  High:              {summary.get('high', 0):>15,.0f}")
    print(f"{'='*50}")

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "energy_electricity.csv"
    result.to_csv(out_path, index=False)
    print(f"\n  State detail saved: {out_path}")


def _run_waste():
    from popest.methods.waste_food import estimate, summary_table

    print("Computing waste/food/vehicle population estimates...")
    results = estimate()
    table = summary_table(results)

    print(f"\n{'='*60}")
    print(f"  WASTE / FOOD / VEHICLE POPULATION ESTIMATES (national)")
    print(f"{'='*60}")
    for _, row in table.iterrows():
        print(f"  {row['method']:<12} central: {row['central']:>15,.0f}  "
              f"range: {row['low']:,.0f} - {row['high']:,.0f}")
    print(f"{'='*60}")

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "waste_food_vehicle.csv"
    table.to_csv(out_path, index=False)
    print(f"\n  Saved: {out_path}")


if __name__ == "__main__":
    main()
