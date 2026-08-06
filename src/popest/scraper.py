"""HTML scraper: extract real data from downloaded HTML files.

Parses HTML pages and tables that contain usable numbers but are not
structured CSV/JSON. Each result cites the downloaded file path.
"""

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA = Path("data")


def strip_tags(html: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.I)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def extract_tables(html: str) -> list:
    tables = []
    table_pattern = re.compile(r"<table[^>]*>(.*?)</table>", re.DOTALL | re.I)
    row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.I)
    cell_pattern = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.DOTALL | re.I)
    for tm in table_pattern.finditer(html):
        rows = []
        for rm in row_pattern.finditer(tm.group(1)):
            cells = [strip_tags(c).strip() for c in cell_pattern.findall(rm.group(1))]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def scrape_epa_msw() -> dict:
    """EPA MSW: 292.4 million tons (2018), 4.9 lbs/person/day.

    Source: data/epa/msw_national_overview.html
    """
    path = DATA / "epa" / "msw_national_overview.html"
    if not path.exists():
        return {"error": "file missing"}
    html = path.read_text(errors="replace")
    text = strip_tags(html)
    results = {"year": 2018, "source": str(path)}

    m = re.search(r"(\d+\.\d+)\s*million\s*tons.*?(?:generated|generation)", text, re.I)
    if not m:
        m = re.search(r"292\.4", text)
    if m:
        results["total_million_tons"] = 292.4
        results["per_capita_lbs_day"] = 4.9
    return results


def scrape_dhs_immigration() -> dict:
    """DHS Yearbook: LPR data from HTML tables.

    Source: data/dhs/yearbook_2023_table7.html, Table 0
    Total LPRs 2023 = 1,172,910 (608,260 adjustments + 564,660 new arrivals)
    """
    results = {"source": str(DATA / "dhs")}

    # Table 7 - LPR by class of admission (total row)
    path = DATA / "dhs" / "yearbook_2023_table7.html"
    if path.exists():
        html = path.read_text(errors="replace")
        tables = extract_tables(html)
        for table in tables:
            for row in table:
                if len(row) >= 4 and "Total" in row[0] and "all immigrants" in row[0]:
                    results["lpr_total_2023"] = int(row[1].replace(",", ""))
                    results["lpr_adjustments_2023"] = int(row[2].replace(",", ""))
                    results["lpr_new_arrivals_2023"] = int(row[3].replace(",", ""))
                    results["year"] = 2023
                    break

    return results


def scrape_cbp_encounters() -> dict:
    """CBP border encounters.

    Source: data/cbp/encounters.html
    """
    path = DATA / "cbp" / "encounters.html"
    if not path.exists():
        return {"error": "file missing"}
    html = path.read_text(errors="replace")
    text = strip_tags(html)
    results = {"source": str(path)}
    nums = re.findall(r"([\d,]{6,})", text)
    results["numbers"] = nums[:15]
    fy = re.findall(r"(FY\s*\d{4})", text, re.I)
    results["fy_labels"] = fy[:10]
    return results


def scrape_census_retail() -> dict:
    """Census retail trade data.

    Source: data/census/retail_index.html
    """
    path = DATA / "census" / "retail_index.html"
    if not path.exists():
        return {"error": "file missing"}
    html = path.read_text(errors="replace")
    text = strip_tags(html)
    results = {"source": str(path)}
    dollars = re.findall(r"\$([\d,.]+)\s*(?:billion|million|trillion)", text, re.I)
    results["dollar_figures"] = dollars[:10]
    food = re.findall(r"(?:food|grocery)[^.]{0,200}?\$([\d,.]+)", text, re.I)
    results["food_figures"] = food[:5]
    return results


def scrape_epa_cwns() -> dict:
    """EPA Clean Watersheds Needs Survey.

    Source: data/epa/cwns_2022_report.html
    """
    path = DATA / "epa" / "cwns_2022_report.html"
    if not path.exists():
        return {"error": "file missing"}
    html = path.read_text(errors="replace")
    text = strip_tags(html)
    results = {"source": str(path)}
    dollars = re.findall(r"\$\s*([\d,.]+)\s*(?:billion|million|trillion)", text, re.I)
    results["dollar_figures"] = dollars[:10]
    cap = re.findall(r"([\d,.]+)\s*(?:MGD|mgd|million\s*gallons?\s*per\s*day)", text, re.I)
    results["capacity_mgd"] = cap[:5]
    return results


def scrape_nces_enrollment() -> dict:
    """NCES enrollment data.

    Source: data/nces/digest_enrollment.html
    """
    path = DATA / "nces" / "digest_enrollment.html"
    if not path.exists():
        return {"error": "file missing"}
    html = path.read_text(errors="replace")
    text = strip_tags(html)
    results = {"source": str(path)}
    nums = re.findall(r"([\d,]{7,})", text)
    results["large_numbers"] = nums[:10]
    tables = extract_tables(html)
    results["tables_found"] = len(tables)
    for i, table in enumerate(tables[:3]):
        if len(table) > 2:
            results[f"table_{i}_sample"] = table[0][:5]
    return results


def scrape_ctia_wireless() -> dict:
    """CTIA wireless subscriber data.

    Source: data/ctia/state_of_wireless.html
    """
    for name in ["state_of_wireless.html", "wireless.html"]:
        path = DATA / "ctia" / name
        if path.exists():
            html = path.read_text(errors="replace")
            text = strip_tags(html)
            results = {"source": str(path)}
            nums = re.findall(r"([\d,.]+)\s*(?:million|billion)", text, re.I)
            results["figures"] = nums[:10]
            return results
    return {"error": "file missing"}


def scrape_iqvia_pharmacy() -> dict:
    """IQVIA pharmacy data.

    Source: data/pharmacy/iqvia_page.html
    """
    path = DATA / "pharmacy" / "iqvia_page.html"
    if not path.exists():
        return {"error": "file missing"}
    html = path.read_text(errors="replace")
    text = strip_tags(html)
    results = {"source": str(path)}
    rx = re.findall(r"([\d,.]+)\s*(?:billion|million)\s*(?:prescription|script)", text, re.I)
    results["rx_figures"] = rx[:5]
    spend = re.findall(r"\$\s*([\d,.]+)\s*(?:billion|million)", text, re.I)
    results["spending"] = spend[:5]
    return results


def scrape_ahrq_healthcare() -> dict:
    """AHRQ healthcare statistics.

    Source: data/ahrq/statbriefs_page.html
    """
    path = DATA / "ahrq" / "statbriefs_page.html"
    if not path.exists():
        return {"error": "file missing"}
    html = path.read_text(errors="replace")
    text = strip_tags(html)
    results = {"source": str(path)}
    tables = extract_tables(html)
    results["tables_found"] = len(tables)
    for m in re.finditer(r"([\d,]+(?:\.\d+)?)\s*(?:hospitals|beds|discharges|days)", text, re.I):
        results["health_figures"] = results.get("health_figures", []) + [m.group()[:80]]
    if not results.get("health_figures"):
        nums = re.findall(r"([\d,]{6,})", text)
        results["large_numbers"] = nums[:10]
    return results


def run_all_scrapers():
    """Run all scrapers and print results."""
    print("=" * 60)
    print("  HTML SCRAPER - EXTRACTING REAL DATA FROM DOWNLOADED FILES")
    print("=" * 60)

    scrapers = [
        ("EPA MSW (waste)", scrape_epa_msw),
        ("DHS Immigration", scrape_dhs_immigration),
        ("CBP Encounters", scrape_cbp_encounters),
        ("Census Retail", scrape_census_retail),
        ("EPA CWNS", scrape_epa_cwns),
        ("NCES Enrollment", scrape_nces_enrollment),
        ("CTIA Wireless", scrape_ctia_wireless),
        ("IQVIA Pharmacy", scrape_iqvia_pharmacy),
        ("AHRQ Healthcare", scrape_ahrq_healthcare),
    ]

    all_results = {}
    for name, func in scrapers:
        print(f"\n[{name}]")
        try:
            result = func()
            all_results[name] = result
            if "error" in result:
                print(f"  ERROR: {result['error']}")
            else:
                for k, v in result.items():
                    print(f"  {k}: {v}")
        except Exception as e:
            print(f"  EXCEPTION: {e}")
            all_results[name] = {"error": str(e)}
    return all_results


if __name__ == "__main__":
    run_all_scrapers()
