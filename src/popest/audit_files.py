"""Check which downloaded files are real data vs HTML garbage."""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA = Path("data")

files_to_check = [
    ("eia/gasoline_weekly.csv", "EIA gasoline weekly"),
    ("eia/gasoline_history_v2.csv", "EIA gasoline history"),
    ("eia/seds_data_complete_us.html", "EIA SEDS complete"),
    ("eia/state_emissions.xlsx", "EIA state emissions"),
    ("eia/electricity_sales_v2.xlsx", "EIA elec sales"),
    ("eia/total_energy_monthly.csv", "EIA total energy"),
    ("census/retail_api_v2.json", "Census retail API"),
    ("census/retail_economic.json", "Census economic"),
    ("cms/medicare_enrollment_v2.json", "CMS Medicare v2"),
    ("ctia/state_of_wireless.html", "CTIA wireless"),
    ("epa/msw_national_overview.html", "EPA MSW"),
    ("irs/soi_zip_2022.csv", "IRS SOI"),
    ("usgs/usco2015.csv", "USGS water"),
    ("bls/total_employed.json", "BLS employed"),
]

print("=" * 60)
print("  FILE FORMAT AUDIT")
print("=" * 60)

real_data = []
html_garbage = []

for rel_path, label in files_to_check:
    p = DATA / rel_path
    if not p.exists():
        print(f"  [MISSING] {label}")
        continue

    content = p.read_bytes()
    size = len(content)
    head = content[:500].decode("utf-8", errors="replace")
    head_stripped = head.strip()

    is_html = head_stripped.startswith("<") or head_stripped.startswith("<!")
    is_json = head_stripped.startswith("{") or head_stripped.startswith("[")
    is_csv = "," in head_stripped[:200] and not is_html

    if is_html:
        fmt = "HTML"
        html_garbage.append((label, rel_path, size))
    elif is_json:
        fmt = "JSON"
        real_data.append((label, rel_path, size))
    elif is_csv:
        fmt = "CSV"
        real_data.append((label, rel_path, size))
    else:
        fmt = "UNKNOWN"
        # Check if it might be a BOM-prefixed CSV
        if content[:3] == b"\xef\xbb\xbf":
            fmt = "CSV (BOM)"
            real_data.append((label, rel_path, size))
        else:
            html_garbage.append((label, rel_path, size))

    print(f"  [{fmt:>7}] {label:<25} {size//1024:>6} KB")

print(f"\n  REAL DATA: {len(real_data)} files")
print(f"  HTML/GARBAGE: {len(html_garbage)} files")

print("\n" + "=" * 60)
print("  HTML FILES (need re-download or parsing)")
print("=" * 60)
for label, path, size in html_garbage:
    print(f"  {label:<25} {path}")

print("\n" + "=" * 60)
print("  REAL DATA FILES (usable)")
print("=" * 60)
for label, path, size in real_data:
    print(f"  {label:<25} {path:<40} {size//1024} KB")
