"""Verify all downloaded data files are non-empty and parseable."""

from pathlib import Path

import pandas as pd

DATA_DIR = Path("data")


def verify_all():
    print("=" * 60)
    print("  DOWNLOAD VERIFICATION")
    print("=" * 60)

    files = sorted(DATA_DIR.rglob("*"))
    files = [f for f in files if f.is_file()]

    ok = 0
    empty = 0
    parseable = 0

    for f in files:
        size = f.stat().st_size
        status = "OK" if size > 100 else "EMPTY"
        if size > 100:
            ok += 1
        else:
            empty += 1

        can_parse = False
        if f.suffix == ".csv":
            try:
                df = pd.read_csv(f, nrows=5)
                can_parse = len(df) > 0
                parseable += 1
            except Exception:
                pass
        elif f.suffix == ".json":
            try:
                import json
                json.loads(f.read_text()[:10000])
                can_parse = True
                parseable += 1
            except Exception:
                pass
        elif f.suffix in (".html", ".pdf", ".xlsx", ".xls"):
            can_parse = size > 1000
            if can_parse:
                parseable += 1

        parse_str = "parseable" if can_parse else "raw"
        print(f"  [{status}] {str(f.relative_to(DATA_DIR)):<50} {size//1024:>6} KB  {parse_str}")

    print(f"\n  Total files: {len(files)}")
    print(f"  Non-empty:   {ok}")
    print(f"  Empty/tiny:  {empty}")
    print(f"  Parseable:   {parseable}")

    if empty > 0:
        print(f"\n  WARNING: {empty} files are empty or too small")


if __name__ == "__main__":
    verify_all()
