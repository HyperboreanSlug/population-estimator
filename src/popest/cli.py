"""CLI entry point for the population estimator.

`popest run` executes the full pipeline (all methods, county ensemble,
bootstrap uncertainty, outputs). Single-method subcommands run one voice
and save its CSV. `popest download` fetches data sources,
`popest verify` checks them, `popest status` reports which numbers are
backed by downloaded files.
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="popest",
        description="Multi-source US population estimation",
    )
    sub = parser.add_subparsers(dest="command")

    for name, help_text in [
        ("run", "Full pipeline: all methods, ensemble, outputs"),
        ("water", "Water budget method"),
        ("wastewater", "Wastewater design-flow method"),
        ("chemistry", "Wastewater chemistry method (EPA DMR loads)"),
        ("energy", "Energy consumption method"),
        ("waste", "Waste/food/vehicle methods"),
        ("healthcare", "Healthcare utilization method"),
        ("housing", "Housing unit method"),
        ("vitals", "Births/deaths vital statistics"),
        ("buildings", "Building footprints method"),
        ("consumption", "SNAP/wireless/grocery method"),
        ("irs", "IRS tax filer method"),
        ("bls", "BLS employment method"),
        ("ensemble", "Alias for run (full ensemble)"),
        ("sensitivity", "Sensitivity analysis"),
        ("download", "Download data sources"),
        ("verify", "Verify downloaded data"),
        ("status", "Which numbers come from downloaded files"),
    ]:
        p = sub.add_parser(name, help=help_text)
        if name in ("run", "ensemble"):
            p.add_argument("--year", type=int, default=2024,
                           help="target estimate year (labels the run)")
            p.add_argument("--api-key", default=None,
                           help="Census API key (optional)")
        if name == "download":
            p.add_argument("--all", action="store_true",
                           help="full PLAN.md catalog (several GB)")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    from popest import runners

    dispatch = {
        "water": runners.water,
        "wastewater": runners.wastewater,
        "chemistry": runners.chemistry,
        "energy": runners.energy,
        "waste": runners.waste,
        "healthcare": runners.healthcare,
        "housing": runners.housing,
        "vitals": runners.vitals,
        "buildings": runners.buildings,
        "consumption": runners.consumption,
        "irs": runners.irs,
        "bls": runners.bls,
    }

    if args.command in dispatch:
        dispatch[args.command]()
    elif args.command in ("run", "ensemble"):
        _run_pipeline(args.year, args.api_key)
    elif args.command == "sensitivity":
        _run_sensitivity()
    elif args.command == "download":
        _run_download(getattr(args, "all", False))
    elif args.command == "verify":
        from popest.verify_downloads import verify_all
        verify_all()
    elif args.command == "status":
        from popest.real_data import report_all
        report_all()


def _run_pipeline(year: int, api_key: str | None) -> None:
    from popest.pipeline import run

    print("=" * 60)
    print(f"  POPULATION ESTIMATOR - FULL RUN (target year {year})")
    print("=" * 60)
    print("  Data years vary by source; each method cites its own.")
    run(year=year, api_key=api_key)


def _run_sensitivity() -> None:
    from popest.sensitivity import sensitivity_table

    table = sensitivity_table()
    print(f"\n  {'Parameter':<28} {'Low':>8} {'Central':>8} "
          f"{'High':>8}  {'Ratio':>6}")
    print(f"  {'-' * 28} {'-' * 8} {'-' * 8} {'-' * 8}  {'-' * 6}")
    for _, row in table.iterrows():
        print(f"  {row['parameter']:<28} {row['low']:>8.1f} "
              f"{row['central']:>8.1f} {row['high']:>8.1f}  "
              f"{row['range_ratio']:>5.2f}x")
    print("\n  Higher ratio = more sensitive to assumption choice.")
    from pathlib import Path
    out = Path("output")
    out.mkdir(exist_ok=True)
    table.to_csv(out / "sensitivity.csv", index=False)
    print(f"  Saved: output/sensitivity.csv")


def _run_download(all_sources: bool) -> None:
    from popest.sources import download_all, download_core

    if all_sources:
        download_all()
    else:
        download_core()


if __name__ == "__main__":
    main()
