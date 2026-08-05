"""Check contents of all downloaded files and extract real numbers."""

import json
import re
from pathlib import Path

DATA = Path("data")


def check_all():
    print("=" * 60)
    print("  CHECKING ALL DOWNLOADED FILES")
    print("=" * 60)

    # CTIA wireless
    print("\n[CTIA Wireless]")
    ctia = DATA / "ctia" / "wireless.html"
    if ctia.exists():
        content = ctia.read_text(errors="replace")
        print(f"  Size: {len(content)} chars")
        nums = re.findall(r"([\d,.]+)\s*million", content, re.I)
        if nums:
            print(f"  Million figures: {nums[:10]}")
        else:
            print(f"  Preview: {content[:300]}")

    # CMS Medicare
    print("\n[CMS Medicare]")
    cms = DATA / "cms" / "medicare_county_api.json"
    if cms.exists():
        content = cms.read_text(errors="replace")
        print(f"  Size: {len(content)} chars")
        print(f"  Content: {content[:300]}")

    # NCES digest
    print("\n[NCES Digest Enrollment]")
    nces = DATA / "nces" / "digest_enrollment.html"
    if nces.exists():
        content = nces.read_text(errors="replace")
        print(f"  Size: {len(content)} chars")
        matches = re.findall(r"([\d,]{7,12})", content)
        if matches:
            print(f"  Large numbers: {matches[:10]}")
        # Look for specific enrollment text
        enroll = re.findall(r"(\d[\d,]*)\s*(?:thousand|million)?[^<]*(?:enroll|student)", content, re.I)
        if enroll:
            print(f"  Enrollment mentions: {enroll[:5]}")

    # EPA CWNS
    print("\n[EPA CWNS]")
    cwns = DATA / "epa" / "cwns.html"
    if cwns.exists():
        content = cwns.read_text(errors="replace")
        print(f"  Size: {len(content)} chars")
        links = re.findall(r'href="([^"]*(?:data|download|report|survey)[^"]*)"', content, re.I)
        if links:
            print(f"  Data links: {links[:8]}")
        # Look for capacity figures
        cap = re.findall(r"([\d,.]+)\s*(?:billion|million)\s*gallons", content, re.I)
        if cap:
            print(f"  Capacity figures: {cap[:5]}")

    # DHS yearbook 2023
    print("\n[DHS Yearbook 2023]")
    dhs = DATA / "dhs" / "yearbook_2023.html"
    if dhs.exists():
        content = dhs.read_text(errors="replace")
        print(f"  Size: {len(content)} chars")
        # Look for table links
        tables = re.findall(r'href="([^"]*table[^"]*)"', content, re.I)
        if tables:
            print(f"  Table links: {tables[:8]}")
        # Look for numbers
        nums = re.findall(r"([\d,]{6,})", content)
        if nums:
            print(f"  Large numbers: {nums[:10]}")

    # CBP encounters
    print("\n[CBP Encounters]")
    cbp = DATA / "cbp" / "encounters.html"
    if cbp.exists():
        content = cbp.read_text(errors="replace")
        print(f"  Size: {len(content)} chars")
        nums = re.findall(r"([\d,]{6,})", content)
        if nums:
            print(f"  Large numbers: {nums[:10]}")

    # MS Building Footprints repo page
    print("\n[MS Building Footprints]")
    ms = DATA / "buildings" / "ms_repo_page.html"
    if ms.exists():
        content = ms.read_text(errors="replace")
        print(f"  Size: {len(content)} chars")
        # Look for state file links
        states = re.findall(r'href="([^"]*\.zip[^"]*)"', content)
        if states:
            print(f"  ZIP links: {states[:5]}")
        # Look for building counts
        counts = re.findall(r"([\d,]+)\s*(?:buildings|structures)", content, re.I)
        if counts:
            print(f"  Building counts: {counts[:5]}")

    # EPA MSW - extract the 292.4 figure with context
    print("\n[EPA MSW - key figure]")
    msw = DATA / "epa" / "msw_national_overview.html"
    if msw.exists():
        content = msw.read_text(errors="replace")
        # Find context around 292.4
        idx = content.find("292.4")
        if idx > 0:
            context = content[max(0, idx-200):idx+200]
            context = re.sub(r"<[^>]+>", " ", context)
            context = re.sub(r"\s+", " ", context)
            print(f"  Context: ...{context.strip()}...")

    # FHWA PDF - check if readable
    print("\n[FHWA Vehicle Registrations PDF]")
    fhwa = DATA / "fhwa" / "vehicle_registrations_2022.pdf"
    if fhwa.exists():
        size = fhwa.stat().st_size
        print(f"  Size: {size // 1024} KB")
        # Check PDF header
        header = fhwa.read_bytes()[:100]
        if header.startswith(b"%PDF"):
            print("  Valid PDF header")
        else:
            print(f"  Header: {header[:50]}")


if __name__ == "__main__":
    check_all()
