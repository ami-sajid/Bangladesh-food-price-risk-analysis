"""Build the static dashboard: one HTML file, inline SVG, no JavaScript, no external files.
Reads only outputs/tables/*.csv, so it works with either database backend."""
from pathlib import Path
import html
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / 'outputs/tables'
OUT = ROOT / 'dashboards/food_price_dashboard.html'
# Staples are looked up by (commodity, unit, pricetype), never by series_id: ids can change on a refresh.
STAPLE_KEYS = {('rice (coarse)', 'kg', 'retail'): 'Coarse rice', ('wheat flour', 'kg', 'retail'): 'Wheat flour',
               ('oil (palm)', 'l', 'retail'): 'Palm oil', ('lentils (masur)', 'kg', 'retail'): 'Masur lentils'}
STAPLES = {}   # series_id -> label, filled by run()
MIN_YOY_MARKETS = 10   # hide YoY points built on fewer matched markets
MIN_CELL_MARKETS = 3   # grey out regional cells built on fewer markets

LIGHT = '--bg:#f7f7f5;--card:#fff;--ink:#1c1c1a;--mute:#6b6b66;--line:#e3e3de;--c0:#2563eb;--c1:#d97706;--c2:#dc2626;--c3:#059669;--warm:#dc2626;--cool:#2563eb;--warn:#fff4d6;--warnink:#6b4a00'
DARK = '--bg:#141413;--card:#1e1e1c;--ink:#ecece8;--mute:#a1a19a;--line:#33332f;--c0:#60a5fa;--c1:#fbbf24;--c2:#f87171;--c3:#34d399;--warm:#f87171;--cool:#60a5fa;--warn:#3a2f10;--warnink:#f5d98a'
CSS = f""":root{{{LIGHT}}}
@media(prefers-color-scheme:dark){{:root:not([data-theme="light"]){{color-scheme:dark;{DARK}}}}}
:root[data-theme="dark"]{{color-scheme:dark;{DARK}}}
*{{box-sizing:border-box}}html{{scroll-padding-top:env(safe-area-inset-top,0px)}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:env(safe-area-inset-top,0px) 16px env(safe-area-inset-bottom,0px)}}
main{{max-width:1040px;margin:0 auto;padding:20px 0 32px}}h1{{font-size:24px;margin:0 0 4px}}h2{{font-size:15px;margin:0 0 2px}}
.sub{{color:var(--mute);margin:0 0 14px}}.note{{background:var(--warn);color:var(--warnink);padding:10px 12px;border-radius:8px;font-size:13px;margin-bottom:14px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(420px,100%),1fr));gap:14px;margin-bottom:14px}}.kpis{{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;min-width:0}}.wide{{grid-column:1/-1}}
.k{{font-size:26px;font-weight:650}}.l{{color:var(--mute);font-size:12px}}.cap{{color:var(--mute);font-size:12px;margin:0 0 8px}}
svg{{width:100%;height:auto;display:block}}.sc{{overflow-x:auto}}text{{fill:var(--mute);font-size:11px}}.g{{stroke:var(--line)}}.z{{stroke:var(--mute)}}
.s0{{stroke:var(--c0)}}.s1{{stroke:var(--c1)}}.s2{{stroke:var(--c2)}}.s3{{stroke:var(--c3)}}.s0.d{{background:var(--c0)}}
.lg{{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12px;margin-bottom:6px}}.lg i{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{padding:5px 8px;text-align:right;border-bottom:1px solid var(--line)}}th:first-child,td:first-child{{text-align:left}}th{{color:var(--mute);font-weight:500}}
td small{{display:block;color:var(--mute);font-size:10px}}.thin{{color:var(--mute);opacity:.55}}ul{{margin:6px 0 0;padding-left:18px}}li{{margin-bottom:6px}}
footer{{color:var(--mute);font-size:12px;margin-top:10px}}a{{color:var(--c0)}}"""

def mon(s): return pd.Timestamp(s).strftime('%b %Y')
def f1(v): return f'{v:+.1f}%'

def line_chart(chg):
    W, H, L, R, TP, B = 640, 250, 40, 14, 10, 24
    wide = chg.pivot(index='month', columns='series_id', values='yoy_pct')
    mk = chg.pivot(index='month', columns='series_id', values='yoy_markets')
    ok = (mk >= MIN_YOY_MARKETS).reindex(columns=list(STAPLES)).fillna(False)
    end = max(m for m in wide.index if ok.loc[m].all())   # later months have thin series coverage
    months = [m for m in sorted(wide.index) if m <= end]
    n = len(months)
    ys = wide.where(mk >= MIN_YOY_MARKETS)
    lo = int(min(-10, (ys.min().min() // 10) * 10)); hi = int(max(10, -(-ys.max().max() // 10) * 10))
    X = lambda i: L + (W - L - R) * i / (n - 1)
    Y = lambda v: TP + (H - TP - B) * (hi - v) / (hi - lo)
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Year-over-year price change for four staples, 2024 to 2026">']
    for g in range(lo, hi + 1, 10):
        o.append(f'<line class="{"z" if g == 0 else "g"}" x1="{L}" x2="{W - R}" y1="{Y(g):.1f}" y2="{Y(g):.1f}"/><text x="{L - 6}" y="{Y(g) + 4:.1f}" text-anchor="end">{g}%</text>')
    for i, m in enumerate(months):
        if m.endswith('-01-01'): o.append(f'<text x="{X(i):.1f}" y="{H - 6}" text-anchor="middle">{m[:4]}</text>')
    for k, sid in enumerate(STAPLES):
        d, pen = '', False
        for i, m in enumerate(months):
            v = ys.at[m, sid] if sid in ys.columns else float('nan')
            if pd.isna(v): pen = False; continue
            d += f'{"L" if pen else "M"}{X(i):.1f} {Y(v):.1f}'; pen = True
        o.append(f'<path class="s{k}" d="{d}" fill="none" stroke-width="2.2"/>')
    return ''.join(o) + '</svg>'

def bar_chart(rows):
    W, H, L = 480, 40 + 34 * len(rows), 100
    vals = [r[1] for r in rows]; lo, hi = min(0, min(vals)), max(vals)
    pad = 120; X = lambda v: L + (W - L - pad) * (v - lo) / (hi - lo)
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Staple price change versus 2022">']
    for i, (name, v, n) in enumerate(rows):
        y = 12 + 34 * i; x0, x1 = sorted((X(0), X(v)))
        col = 'var(--warm)' if v > 0 else 'var(--cool)'
        o.append(f'<text x="{L - 8}" y="{y + 17}" text-anchor="end" style="fill:var(--ink);font-size:12px">{html.escape(name)}</text>'
                 f'<rect x="{x0:.1f}" y="{y}" width="{max(x1 - x0, 1):.1f}" height="24" rx="3" fill="{col}"/>'
                 f'<text x="{(x1 + 6) if v > 0 else (X(0) + 6):.1f}" y="{y + 16}" text-anchor="start">{f1(v)} · {n} mkts</text>')
    o.append(f'<line class="z" x1="{X(0):.1f}" x2="{X(0):.1f}" y1="6" y2="{H - 24}"/>')
    return ''.join(o) + '</svg>'

def coverage_chart(cov):
    cov = cov[cov.year >= 2005]; W, H, L, B = 480, 190, 34, 22
    mx = int(cov.markets.max()); bw = (W - L - 6) / len(cov)
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Markets reporting per year">']
    for g in (0, 50, 100):
        y = H - B - (H - B - 8) * g / mx
        o.append(f'<line class="g" x1="{L}" x2="{W}" y1="{y:.1f}" y2="{y:.1f}"/><text x="{L - 5}" y="{y + 4:.1f}" text-anchor="end">{g}</text>')
    for i, r in enumerate(cov.itertuples()):
        h = (H - B - 8) * r.markets / mx; x = L + i * bw
        o.append(f'<rect x="{x + 2:.1f}" y="{H - B - h:.1f}" width="{bw - 4:.1f}" height="{h:.1f}" fill="var(--c0)" rx="2"/>')
        if r.year % 3 == 2 or r.year in (2026,): o.append(f'<text x="{x + bw / 2:.1f}" y="{H - 6}" text-anchor="middle">{r.year}</text>')
    return ''.join(o) + '</svg>'

def region_table(dv):
    d = dv[dv.series_id.isin(STAPLES)]
    divs = sorted(d.division.unique())
    h = '<table><tr><th>Division</th>' + ''.join(f'<th>{n}</th>' for n in STAPLES.values()) + '</tr>'
    for dvn in divs:
        h += f'<tr><td>{dvn.title()}</td>'
        for sid in STAPLES:
            r = d[(d.series_id == sid) & (d.division == dvn)]
            if r.empty: h += '<td class="thin">–</td>'; continue
            ratio, n = float(r.national_price_ratio.iloc[0]), int(r.markets.iloc[0])
            if n < MIN_CELL_MARKETS: h += f'<td class="thin">{ratio:.2f}<small>{n} mkt{"s" if n > 1 else ""}</small></td>'; continue
            a = min(abs(ratio - 1) / 0.1, 1) * 0.55
            c = '220,38,38' if ratio > 1 else '37,99,235'
            h += f'<td style="background:rgba({c},{a:.2f})">{ratio:.2f}<small>{n} mkts</small></td>'
        h += '</tr>'
    return h + '</table>'

def risk_table(rs):
    r = rs[rs.status == 'eligible'].sort_values(['risk_score', 'cv'], ascending=False).head(8)
    h = '<table><tr><th>Commodity</th><th>Risk score</th><th>Volatility (CV)</th><th>Last MoM</th><th>Markets used</th></tr>'
    for x in r.itertuples():
        h += f'<tr><td>{html.escape(x.commodity)} <small>{x.unit}</small></td><td>{x.risk_score:.0f}</td><td>{x.cv:.2f}</td><td>{x.mom_pct:+.1f}%</td><td>{int(x.market_count)}</td></tr>'
    return h + '</table>'

def run():
    global STAPLES
    meta = pd.read_csv(T / 'analysis_metadata.csv').iloc[0]
    dim = pd.read_csv(T / 'dim_commodity.csv')
    ids = {(r.commodity, r.unit, r.pricetype): int(r.series_id) for r in dim.itertuples()}
    STAPLES = {ids[k]: v for k, v in STAPLE_KEYS.items() if k in ids}   # keeps display order
    SID = {v: k for k, v in STAPLES.items()}
    if len(SID) < len(STAPLE_KEYS): return None   # dataset lacks the four staples: nothing to chart
    chg = pd.read_csv(T / '04_changes.csv'); chg = chg[chg.series_id.isin(STAPLES)].dropna(subset=['yoy_pct'])
    END = max(m for m, g in chg[chg.yoy_markets >= MIN_YOY_MARKETS].groupby('month') if g.series_id.nunique() == len(STAPLES))
    chg = chg[chg.month <= END]
    since = pd.read_csv(T / '05_since_2022.csv').dropna(subset=['change_pct']); since = since[since.series_id.isin(STAPLES)].sort_values('change_pct', ascending=False)
    dv = pd.read_csv(T / '06_division_comparison.csv'); rs = pd.read_csv(T / '11_risk_score.csv')
    cov = pd.read_csv(T / 'source_coverage_year.csv'); fact = pd.read_csv(T / 'fact_prices.csv', usecols=['market_id', 'series_id'])
    bars = [(STAPLES[int(r.series_id)], r.change_pct, int(r.matched_markets)) for r in since.itertuples()]
    last = (chg[chg.yoy_markets >= MIN_YOY_MARKETS].sort_values('month').groupby('series_id').tail(1).set_index('series_id'))
    d = lambda sid: (mon(last.at[sid, 'month']), last.at[sid, 'yoy_pct'])
    top = since.iloc[0]
    palm_peak = chg[(chg.series_id == SID['Palm oil']) & (chg.yoy_markets >= MIN_YOY_MARKETS)].sort_values('yoy_pct').iloc[-1]
    wheat_low = chg[(chg.series_id == SID['Wheat flour']) & (chg.yoy_markets >= MIN_YOY_MARKETS)].sort_values('yoy_pct').iloc[0]
    rr = dv[dv.series_id.isin(STAPLES) & (dv.markets >= MIN_CELL_MARKETS)].national_price_ratio
    gap = max(abs(rr.min() - 1), abs(rr.max() - 1)) * 100
    A, S = mon(meta.analysis_month), mon(meta.latest_source_month)
    legend = ''.join(f'<span><i style="background:var(--c{k})"></i>{n}</span>' for k, n in enumerate(STAPLES.values()))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><title>Bangladesh Food Price &amp; Inflation Risk Dashboard</title><style>{CSS}</style></head><body><main>
<h1>Bangladesh Food Price &amp; Inflation Risk</h1>
<p class="sub">Which staples carry the most price risk for a food retailer or distributor? WFP market prices, matched-market comparisons, comparison month {A}.</p>
<div class="note"><b>Read with care.</b> Descriptive market-price analysis, not the official inflation rate (CPI). Source data runs to {S}, but only {A} and earlier meet the coverage rule. The volatility watchlist rests on 3–4 Chittagong-area markets: a local warning, not a national ranking.</div>
<div class="grid kpis">
<div class="card"><div class="k">{len(fact):,}</div><div class="l">cleaned price observations</div></div>
<div class="card"><div class="k">{fact.market_id.nunique()}</div><div class="l">markets across 8 divisions</div></div>
<div class="card"><div class="k">{int((dim.is_food == 1).sum())}</div><div class="l">food series (commodity, unit, price type)</div></div>
<div class="card"><div class="k">{f1(top.change_pct)}</div><div class="l">{STAPLES[int(top.series_id)].lower()} vs 2022, same {int(top.matched_markets)} markets</div></div></div>
<div class="grid">
<div class="card wide"><h2>Staple prices: year-over-year change, matched markets</h2><p class="cap">Each point compares the same markets a year apart. Points built on fewer than {MIN_YOY_MARKETS} markets are hidden.</p><div class="lg">{legend}</div>{line_chart(chg)}</div>
<div class="card"><h2>Staples versus 2022</h2><p class="cap">{A} price against each market’s own 2022 average.</p>{bar_chart(bars)}</div>
<div class="card"><h2>Regional price ratio to national average</h2><p class="cap">{A}. 1.00 = national average; greyed cells have under {MIN_CELL_MARKETS} markets.</p><div class="sc">{region_table(dv)}</div></div>
<div class="card"><h2>Volatility watchlist (fixed 4-market panel)</h2><p class="cap">Risk score blends volatility and latest monthly change. Chittagong-area markets only.</p><div class="sc">{risk_table(rs)}</div></div>
<div class="card"><h2>Evidence base: markets reporting per year</h2><p class="cap">Coverage was 4–7 markets until 2019, then 63–72 from 2020; 2026 is partial.</p>{coverage_chart(cov)}</div>
<div class="card wide"><h2>What a retailer or distributor should take from this</h2><ul>
<li><b>Watch edible oil.</b> Palm oil is up {top.change_pct:.0f}% on 2022 in the same markets; its year-over-year change peaked at {f1(palm_peak.yoy_pct)} ({mon(palm_peak.month)}) and stood at {f1(d(SID['Palm oil'])[1])} in {d(SID['Palm oil'])[0]}.</li>
<li><b>Wheat flour has swung from deflation to inflation.</b> {f1(wheat_low.yoy_pct)} year over year in {mon(wheat_low.month)}, {f1(d(SID['Wheat flour'])[1])} in {d(SID['Wheat flour'])[0]}: renegotiate supply terms while it is rising.</li>
<li><b>Lentils and coarse rice are cheaper than a year ago</b> ({f1(d(SID['Masur lentils'])[1])} and {f1(d(SID['Coarse rice'])[1])} in their latest well-covered months): a window to build stock.</li>
<li><b>Geography matters less than timing for staples.</b> Where at least {MIN_CELL_MARKETS} markets report, divisional prices sit within about ±{gap:.0f}% of the national average; the risk is in price swings over time, not in where you buy.</li></ul></div></div>
<footer>Source: WFP Food Prices for Bangladesh via HDX. Pipeline: Python, SQL (PostgreSQL/SQLite), pandas cross-checks. 2022–2023 prices are source aggregates, not market-level actuals. Generated by scripts/build_dashboard.py.</footer></main></body></html>"""
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page, encoding='utf-8')
    return OUT

if __name__ == '__main__':
    print(run())
