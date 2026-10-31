"""Generate findings only from real exported tables and audit metadata."""
import json
from datetime import datetime,timezone
import pandas as pd
import config as C
from scripts.common import markdown_table

def run():
    t=C.ROOT/'outputs/tables';read=lambda name:pd.read_csv(t/name)
    meta=json.loads((C.ROOT/'outputs/analysis_metadata.json').read_text())
    log=json.loads((C.ROOT/'outputs/cleaning_log.json').read_text())
    asof=meta['analysis_month']
    risk=read('11_risk_score.csv');eligible=risk.dropna(subset=['risk_score']).sort_values('risk_score',ascending=False)
    changes=read('04_changes.csv');current=changes[changes.month==asof]
    coverage=read('01_coverage.csv');source_inventory=read('source_inventory.csv')
    source_nonfood=int(source_inventory.loc[source_inventory.category.isin(C.NON_FOOD_CATEGORIES),'rows'].sum())
    food_rows=int(coverage.loc[coverage.is_food==1,'observations'].sum())
    report='# Findings generated from your CSV\n\n'
    report+=f'Generated UTC: {datetime.now(timezone.utc).isoformat()}. Latest source month: **{meta["latest_source_month"]}**. '
    report+=f'Comparison month: **{asof}**, selected by **{meta["selection"]}**. '
    report+=f'The coverage rule requires at least {meta["coverage_fraction"]:.0%} of each trailing-year maximum for food-series count and market count. This is an explicit heuristic, not a source completeness guarantee.\n\n'
    report+=f'Cleaned observations: **{log["rows_after"]:,}** from **{log["rows_before"]:,}** source records; '
    report+=f'**{food_rows:,}** cleaned food records. The raw inventory contains **{source_nonfood:,}** non-food records. '
    report+=f'**{log["rows_before"]-log["rows_after"]:,}** records were quarantined. '
    report+=f'Eligible food-risk series: **{len(eligible)} of {len(risk)}**. Ineligible does not mean low risk.\n\n'
    def section(title,frame,limit=10):
        nonlocal report
        report+='## '+title+'\n\n'+markdown_table(frame,limit)+'\n\n'
    section('Coverage near the source endpoint',read('analysis_month_selection.csv'),12)
    section('Highest eligible food-risk scores (fixed markets, 2024 onward)',eligible[
        ['commodity','unit','pricetype','month','market_count','available_markets','cv','mom_pct','risk_score','status']])
    members=read('risk_panel_members.csv')
    geography=members.groupby(['division','district','market']).series_id.nunique().reset_index(name='eligible_series')
    section('Geography represented by the fixed risk panels',geography,30)
    if len(members):
        divisions_text=', '.join(sorted(members.division.dropna().unique()))
        report+=f'**Risk-panel geographic scope: {divisions_text}. These panels contain {members.market_id.nunique()} distinct markets in total; they are not nationally representative.**\n\n'
    report+='Score uses the same markets in all twelve months. CV is a fraction; MoM is percent. '
    report+='A high score from one market is a local warning, not a national commodity ranking. Series without the required panel are excluded from scoring.\n\n'
    cols=['commodity','unit','pricetype','month','mom_pct','mom_markets','yoy_pct','yoy_markets','yoy_flag_transitions']
    section('Biggest matched-market monthly increases at comparison month',current[current.mom_pct>0].nlargest(10,'mom_pct')[cols])
    section('Biggest matched-market monthly decreases at comparison month',current[current.mom_pct<0].nsmallest(10,'mom_pct')[cols])
    report+='MoM and YoY use separate endpoint-matched market sets. The latest price in the MoM calculation can therefore differ from that in the YoY calculation. '
    report+='YoY requires the same market at both endpoints and at least twelve observed months through the current month. It does not imply every intervening month is present. '
    report+='Source-flag transitions are disclosed and are a remaining measurement limitation.\n\n'
    divisions=read('10_division_rank.csv')
    multi=divisions.groupby('series_id').filter(lambda g:len(g)>1)
    extremes=multi[(multi.expensive_rank==1)|(multi.cheap_rank==1)].copy()
    extremes['position']=extremes.apply(lambda r:'tied' if r.expensive_rank==1 and r.cheap_rank==1 else ('highest' if r.expensive_rank==1 else 'lowest'),axis=1)
    section('Within-series division extrema (first ten rows, full table exported)',extremes[
        ['commodity','unit','pricetype','month','division','position','avg_price','markets']])
    section('Core staples versus 2022: matched markets only',read('05_since_2022.csv'))
    section('Source flags by year (last rows)',read('source_flags_by_year.csv').tail(12),12)
    sensitivity=read('12_outlier_sensitivity.csv').assign(abs_impact=lambda d:d.impact_pct.abs())
    section('Largest snapshot outlier sensitivity',sensitivity.nlargest(10,'abs_impact')[
        ['commodity','unit','pricetype','month','impact_pct','flagged','all_markets','unflagged_markets','actual_only_markets']])
    report+='## Proposed business actions\n\n'
    if len(eligible):
        r=eligible.iloc[0]
        tied=eligible[eligible.risk_score.round(8)==round(r.risk_score,8)]
        if len(tied)>1:
            report+=f'The top score is tied across {len(tied)} series; the first is an example, not a unique winner.\n\n'
        report+=f'1. Review fresh supplier quotes for **{r.commodity} ({r.unit}, {r.pricetype})**: score **{r.risk_score:.2f}**, '
        report+=f'based on **{int(r.market_count)}** complete-panel market(s). Verify local coverage before changing inventory; this is not evidence of national risk or achieved savings.\n'
    else:
        report+='1. No complete fixed-panel score qualifies. Collect comparable recent market observations before ranking inventory priorities.\n'
    if len(multi):
        # Pick the series with the widest relative division range, rather than an arbitrary row.
        spreads=multi.groupby('series_id').avg_price.agg(['min','max'])
        sid=(spreads['max']/spreads['min']).idxmax();g=multi[multi.series_id==sid]
        lo=g.loc[g.avg_price.idxmin()];hi=g.loc[g.avg_price.idxmax()]
        report+=f'2. Investigate the observed **{hi.commodity} ({hi.unit}, {hi.pricetype})** division gap in **{hi.month}**: '
        report+=f'**{lo.division} {lo.avg_price:.2f} BDT** versus **{hi.division} {hi.avg_price:.2f} BDT**. '
        report+='Validate grade, transport, availability and supplier terms before treating it as a sourcing opportunity.\n'
    else:
        report+='2. Regional comparison lacks multiple divisions for comparable series; collect more quotes.\n'
    report+='3. Monitor the coverage table before refreshing business decisions. A new date with only a few commodities is not an updated view of the whole food market.\n\n'
    report+='## Limitations\n\nMonthly observations miss daily spikes. Uneven coverage limits representation even after matching markets. '
    report+='Retail and wholesale remain separate, as do source units and commodity grades. Aggregate and actual,aggregate source flags are retained, counted, and never described as equivalent to raw observations. '
    report+='The 2022 baseline may use aggregate prices while current values use actual prices; matched geography does not resolve that measurement change. '
    report+='Most commodities have only a short window beginning in 2024. Long-run lines are limited to core staples in one fixed market with at least sixty observed months. '
    report+='The raw date anomaly is quarantined, not silently repaired. Non-food and unclassified records are excluded from food analyses. '
    report+='Flagged price outliers remain in primary results, with separate sensitivity results. Ramadan shifts across calendar months, and seasonality is descriptive. '
    report+='The score and broad-coverage cutoff are transparent unvalidated heuristics. No official CPI, forecast, causal effect, cost saving or realized business impact is claimed.\n'
    (C.ROOT/'docs/FINDINGS.md').write_text(report,encoding='utf-8')
    p=C.ROOT/'README.md';content=p.read_text(encoding='utf-8')
    start='<!-- RESULTS_START -->';end='<!-- RESULTS_END -->'
    p.write_text(content.split(start)[0]+start+'\n'+report.replace('# Findings generated from your CSV','### Computed results',1)+'\n'+end+content.split(end)[1],encoding='utf-8')
