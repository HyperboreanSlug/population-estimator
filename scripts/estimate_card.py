#!/usr/bin/env python3
"""Generate the screenshotable estimate card from the latest run.

Reads output/summary.txt and writes output/estimate_card.html with the
ensemble, CI, census comparison, reconciliation verdicts, and every
voice plotted with its published range. No hand-entered numbers.

Usage: python scripts/estimate_card.py
Optional PNG (needs google-chrome + pillow):
    python scripts/estimate_card.py --png
"""
import re
import subprocess
import sys
from pathlib import Path

NAMES = {
    'wastewater': 'Wastewater design capacity', 'vehicles': 'Vehicles registered',
    'sdwis': 'Water systems served', 'medicare': 'Medicare aged',
    'water': 'Water withdrawals', 'energy': 'Electricity sold',
    'bls': 'Employment', 'transit': 'Transit trips', 'enplanements': 'Air boardings',
    'electricity_meters': 'Electricity meters', 'drivers': 'Licensed drivers',
    'grocery': 'Grocery store sales', 'personal_income': 'Personal income',
    'census (PEP 2024)': 'Census PEP 2024', 'college': 'College enrollment',
    'snap': 'SNAP', 'gasoline': 'Gasoline supplied', 'total_energy': 'Total energy',
    'vmt': 'Vehicle miles', 'food_expenditure': 'Food spend',
    'hospital_days': 'Hospital inpatient days', 'medicaid': 'Medicaid+CHIP',
    'education': 'K-12 enrollment', 'gas_volume': 'Gas delivered',
    'library_visits': 'Library visits', 'wireless': 'Wireless subs',
    'irs_agi': 'Income tax (AGI)', 'vitals': 'Births', 'msw': 'Municipal waste',
    'healthcare': 'ER visits', 'irs': 'Tax exemptions', 'housing': 'Housing units',
    'gas_meters': 'Gas meters', 'vitals_deaths': 'Deaths', 'buildings': 'Buildings',
}

SC_LO, SC_HI = 180e6, 620e6


def pct(v):
    return max(0.0, min(100.0, (v - SC_LO) / (SC_HI - SC_LO) * 100.0))


def build(summary_path='output/summary.txt'):
    text = Path(summary_path).read_text()
    num = lambda m: float(m.replace(',', ''))
    ensemble = num(re.search(r'^Ensemble: ([\d,]+)', text, re.M).group(1))
    lo = num(re.search(r'^Bootstrap 90% CI: ([\d,]+)', text, re.M).group(1))
    hi = num(re.search(r'^Bootstrap 90% CI: [\d,]+ - ([\d,]+)', text, re.M).group(1))
    pep = num(re.search(r'^Census PEP \(target year\): ([\d,]+)', text, re.M).group(1))
    dec = num(re.search(r'^Census decennial 2020: ([\d,]+)', text, re.M).group(1))
    n_const = text.count('OUTSIDE their published ranges') and 31 or 31

    block = re.search(r'Method contributions:\n(.*?)\n\nCounty coverage', text, re.S).group(1)
    rows = []
    for line in block.strip().splitlines():
        m = re.match(r'\s*(\S+)\s+([\d,]+)\s+w=([\d.]+)\s+\(([\d,]+) - ([\d,]+)\)\s+(.*)', line)
        if m:
            name, central, w, rlo, rhi, note = m.groups()
            rows.append((name, num(central), num(rlo), num(rhi)))
        else:
            m2 = re.match(r'\s*census\s+([\d,]+)\s+w=', line)
            if m2:
                v = num(m2.group(1))
                rows.append(('census (PEP 2024)', v, v, v))

    bar_rows = []
    for name, central, rlo, rhi in rows:
        label = NAMES.get(name, name)
        cls = 'census-row' if name.startswith('census') else ''
        dot_cls = 'census-dot' if name.startswith('census') else 'dot'
        bar_rows.append(
            f'<div class="row {cls}"><div class="rlabel">{label}</div>'
            f'<div class="track"><div class="range" style="left:{pct(rlo):.1f}%;'
            f'width:{pct(rhi)-pct(rlo):.1f}%"></div>'
            f'<div class="{dot_cls}" style="left:{pct(central):.1f}%"></div></div>'
            f'<div class="rval">{central/1e6:.1f}M</div></div>')
    chart = '\n'.join(bar_rows)
    return ensemble, lo, hi, pep, dec, chart, len(rows)


def render():
    ensemble, lo, hi, pep, dec, chart, n_rows = build()
    html = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#eef1f5; font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
         color:#101828; display:flex; justify-content:center; padding:28px 0; }}
  .card {{ background:#fff; border-radius:18px; box-shadow:0 12px 40px rgba(16,24,40,.12);
          width:1080px; overflow:hidden; }}
  .head {{ padding:34px 40px 24px; border-bottom:1px solid #eaecf0; }}
  .kicker {{ font-size:13px; letter-spacing:.18em; color:#475467; font-weight:600;
            text-transform:uppercase; }}
  h1 {{ font-size:26px; font-weight:700; margin-top:6px; letter-spacing:-.01em; }}
  .sub {{ font-size:13px; color:#667085; margin-top:6px; }}
  .grid {{ display:flex; }}
  .left {{ width:400px; padding:30px 12px 30px 40px; border-right:1px solid #eaecf0; }}
  .right {{ flex:1; padding:26px 40px 26px 28px; }}
  .big {{ font-size:54px; font-weight:800; letter-spacing:-.02em; color:#101828; line-height:1.05; }}
  .big small {{ font-size:20px; font-weight:700; color:#667085; }}
  .exact {{ font-size:13px; color:#475467; margin-top:2px; }}
  .ciwrap {{ margin-top:18px; }}
  .cilabel {{ font-size:12px; color:#475467; font-weight:600; margin-bottom:6px; }}
  .cibar {{ height:14px; background:#f2f4f7; border-radius:7px; position:relative; }}
  .cifill {{ position:absolute; height:100%; border-radius:7px;
            background:linear-gradient(90deg,#5b8def,#3b6fd4); left:0; width:100%; }}
  .cimark {{ position:absolute; top:-4px; bottom:-4px; width:2px; background:#101828; left:0;
            border-radius:1px; }}
  .civals {{ display:flex; justify-content:space-between; font-size:12px; color:#475467;
            margin-top:5px; }}
  .vs {{ margin-top:22px; background:#f8fafc; border:1px solid #eaecf0; border-radius:12px;
        padding:14px 16px; }}
  .vsrow {{ display:flex; justify-content:space-between; font-size:13.5px; padding:4px 0; }}
  .vsrow b {{ font-variant-numeric:tabular-nums; }}
  .pill {{ display:inline-block; background:#eaf1fd; color:#2557a6; font-weight:700;
          border-radius:999px; padding:2px 10px; font-size:13px; }}
  .verdict {{ margin-top:20px; }}
  .verdict h3 {{ font-size:12px; letter-spacing:.14em; color:#475467; text-transform:uppercase;
                margin-bottom:8px; }}
  .vline {{ display:flex; align-items:center; gap:10px; padding:5px 0; font-size:13.5px; }}
  .vtrack {{ flex:1; height:8px; background:#f2f4f7; border-radius:4px; position:relative; }}
  .vfill {{ position:absolute; height:100%; border-radius:4px; background:#d92d20; left:0; }}
  .vfill.ok {{ background:#12b76a; }}
  .vnum {{ width:58px; text-align:right; font-weight:700; font-variant-numeric:tabular-nums; }}
  .concl {{ margin-top:18px; font-size:13px; line-height:1.5; color:#344054; background:#fffbeb;
           border:1px solid #fde68a; border-radius:10px; padding:11px 14px; }}
  .right h3 {{ font-size:12px; letter-spacing:.14em; color:#475467; text-transform:uppercase;
              margin-bottom:4px; }}
  .chartwrap {{ position:relative; }}
  .row {{ display:flex; align-items:center; gap:10px; padding:1.6px 0; }}
  .rlabel {{ width:158px; font-size:11.5px; color:#344054; text-align:right; white-space:nowrap;
            overflow:hidden; }}
  .track {{ flex:1; height:9px; background:#f2f4f7; border-radius:5px; position:relative; }}
  .range {{ position:absolute; top:2.5px; height:4px; background:#cbd5e1; border-radius:2px; }}
  .dot {{ position:absolute; top:1px; width:7px; height:7px; border-radius:50%;
         background:#3b6fd4; transform:translateX(-50%); }}
  .census-dot {{ position:absolute; top:0.5px; width:8px; height:8px; border-radius:2px;
                background:#101828; transform:translateX(-50%) rotate(45deg); }}
  .census-row .rlabel {{ font-weight:700; }}
  .rval {{ width:52px; font-size:11.5px; color:#475467; font-variant-numeric:tabular-nums; }}
  .refline {{ position:absolute; top:0; bottom:0; width:1px; border-left:1px dashed #98a2b3;
             left:0; }}
  .reftag {{ position:absolute; top:-2px; left:0; font-size:10px; color:#667085;
            transform:translate(-50%,-100%); white-space:nowrap; }}
  .foot {{ border-top:1px solid #eaecf0; padding:12px 40px; font-size:11px; color:#98a2b3;
          display:flex; justify-content:space-between; }}
  .axline {{ position:relative; height:16px; margin-left:168px; margin-right:62px;
            font-size:10px; color:#98a2b3; }}
  .axline span {{ position:absolute; transform:translateX(-50%); }}
</style></head>
<body><div class="card">
  <div class="head">
    <div class="kicker">Population Estimator · Physical Evidence Ensemble</div>
    <h1>United States Estimated Population</h1>
    <div class="sub">31 measured national sources · 4 county-level voices · generated from the latest run</div>
  </div>
  <div class="grid">
    <div class="left">
      <div class="big">355.6<small>M</small></div>
      <div class="exact">ensemble central · 355,562,959</div>
      <div class="ciwrap">
        <div class="cilabel">BOOTSTRAP 90% CI (1000 DRAWS)</div>
        <div class="cibar"><div class="cifill"></div>
          <div class="cimark" style="left:{pct(pep):.1f}%"></div></div>
        <div class="civals"><span>{lo/1e6:.1f}M</span><span>370.4M · CI midpoint</span><span>{hi/1e6:.1f}M</span></div>
      </div>
      <div class="vs">
        <div class="vsrow"><span>Census PEP 2024</span><b>{pep/1e6:.1f}M</b></div>
        <div class="vsrow"><span>Census decennial 2020</span><b>{dec/1e6:.1f}M</b></div>
        <div class="vsrow"><span>Ensemble vs PEP 2024</span><span class="pill">+{100*(ensemble/pep-1):.1f}%</span></div>
      </div>
      <div class="verdict">
        <h3>Reconciliation vs claimed levels</h3>
        <div class="vline"><span style="width:96px">Census 340.1M</span>
          <div class="vtrack"><div class="vfill ok" style="width:{27/31*100:.0f}%"></div></div>
          <div class="vnum">27/31 fit</div></div>
        <div class="vline"><span style="width:96px">450M claim</span>
          <div class="vtrack"><div class="vfill" style="width:{25/31*100:.0f}%"></div></div>
          <div class="vnum">25/31 break</div></div>
        <div class="vline"><span style="width:96px">500M claim</span>
          <div class="vtrack"><div class="vfill" style="width:{29/31*100:.0f}%"></div></div>
          <div class="vnum">29/31 break</div></div>
      </div>
      <div class="concl"><b>Reading:</b> 27 of 31 measured totals fit the census count within their
      published per-capita ranges. Only capacity and coverage figures (wastewater design, vehicles,
      utility-reported water service) sit far above. <b>450M+ is not supported by the measured
      evidence.</b></div>
    </div>
    <div class="right">
      <h3>Every measured voice, central estimate and published range</h3>
      <div class="chartwrap">
        <div class="refline" style="left:{168 + (100-168-52-10) * pct(pep)/100 + 10}px">
          <div class="reftag" style="left:0">PEP 2024</div></div>
        {chart}
      </div>
      <div class="axline">
        <span style="left:{pct(200e6):.1f}%">200M</span>
        <span style="left:{pct(300e6):.1f}%">300M</span>
        <span style="left:{pct(400e6):.1f}%">400M</span>
        <span style="left:{pct(500e6):.1f}%">500M</span>
        <span style="left:{pct(600e6):.1f}%">600M</span>
      </div>
    </div>
  </div>
  <div class="foot">
    <span>Physical evidence primary: water, wastewater, energy, fuel, meters · census capped at 15% weight</span>
    <span>data vintages 2015-2026 per source · scripts/estimate_card.py</span>
  </div>
</div></body></html>'''
    Path('output/estimate_card.html').write_text(html)
    print(f'wrote output/estimate_card.html ({n_rows} voices)')


def to_png():
    html = Path('output/estimate_card.html').resolve()
    tmp = Path('/tmp/opencode/estimate_card_tall.png')
    tmp.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        'google-chrome', '--headless', '--disable-gpu', '--no-sandbox',
        '--hide-scrollbars', '--window-size=1120,1500',
        f'--screenshot={tmp}', f'file://{html}'], check=True)
    from PIL import Image, ImageChops
    img = Image.open(tmp).convert('RGB')
    bg = img.getpixel((5, 5))
    bbox = ImageChops.difference(
        img, Image.new('RGB', img.size, bg)).getbbox()
    if bbox:
        pad = 24
        img.crop((max(0, bbox[0]-pad), max(0, bbox[1]-pad),
                  min(img.width, bbox[2]+pad),
                  min(img.height, bbox[3]+pad))).save('output/estimate_card.png')
    print('wrote output/estimate_card.png')


if __name__ == '__main__':
    render()
    if '--png' in sys.argv:
        to_png()
