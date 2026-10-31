"""Six charts from real exports. Never connect changing-market level averages."""
import json
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import config as C

def run():
    t=C.ROOT/'outputs/tables';out=C.ROOT/'outputs/charts'
    read=lambda name:pd.read_csv(t/name)
    metadata=json.loads((C.ROOT/'outputs/analysis_metadata.json').read_text())
    asof=metadata['analysis_month']
    members=read('risk_panel_members.csv')
    panel_divisions=', '.join(sorted(members.division.dropna().unique())) if len(members) else 'no eligible geography'
    risk=read('11_risk_score.csv');trends=read('02_monthly_trends.csv')
    eligible=risk.dropna(subset=['risk_score']).sort_values('risk_score',ascending=False)
    available=risk[risk.available_markets.notna()]
    focus=int(eligible.iloc[0].series_id) if not eligible.empty else int(available.sort_values('available_markets',ascending=False).iloc[0].series_id)
    row=risk[risk.series_id==focus].iloc[0]
    label=f'{row.commodity} / {row.unit} / {row.pricetype}'
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    def save(name,title,draw,empty=False):
        fig,ax=plt.subplots(figsize=(11,6))
        ax.set_title(textwrap.fill(title,70),loc='left',fontweight='bold',pad=15)
        if empty:
            ax.text(.5,.5,'Insufficient eligible data',ha='center',va='center',transform=ax.transAxes);ax.set_axis_off()
        else: draw(ax)
        fig.text(.01,.01,'Uploaded WFP CSV | Nominal BDT | See panel sizes and source-flag caveats in FINDINGS.md',fontsize=8,color='#555555')
        fig.tight_layout(rect=(0,.05,1,1));fig.savefig(out/name,dpi=160);plt.close(fig)
    top=eligible.head(10).iloc[::-1]
    def risk_plot(ax):
        labels=top.apply(lambda r:textwrap.fill(f'{r.commodity} / {r.unit} / {r.pricetype} (n={int(r.market_count)} markets)',40),axis=1)
        ax.barh(labels,top.risk_score,color='#147d92');ax.set_xlim(0,100);ax.set_xlabel('Heuristic risk score (0–100); complete fixed 12-month panels only')
    save('01_risk.png',f'Food-price risk at {asof}: {panel_divisions} panels only (2024 onward history)',risk_plot,top.empty)
    core=trends[trends.scope=='core long history']
    pool=core if not core.empty else trends
    if pool.empty:
        save('02_trend.png','Same-market trend',lambda ax:None,True)
    else:
        sid,mid=pool.groupby(['series_id','market_id']).size().idxmax()
        chosen=pool[(pool.series_id==sid)&(pool.market_id==mid)].iloc[0]
        rolling=read('09_rolling_average.csv');rolling=rolling[(rolling.series_id==sid)&(rolling.market_id==mid)]
        def trend_plot(ax):
            ax.plot(pd.to_datetime(rolling.month),rolling.avg_price,label='Same-market price',color='#147d92')
            ax.plot(pd.to_datetime(rolling.month),rolling.rolling_12m,label='Complete 12-month average',color='#df8e32')
            ax.set_ylabel('BDT per '+chosen.unit);ax.legend();ax.tick_params(axis='x',rotation=30)
        save('02_trend.png',f'{chosen.commodity} / {chosen.unit} / {chosen.pricetype}: fixed market {chosen.market}',trend_plot)
    regions=read('10_division_rank.csv')
    comparison_ids=regions.groupby('series_id').division.nunique()
    comparison_ids=comparison_ids[comparison_ids>=2].index
    candidates=eligible[eligible.series_id.isin(comparison_ids)]
    regional_focus=int(candidates.iloc[0].series_id) if len(candidates) else (int(comparison_ids[0]) if len(comparison_ids) else focus)
    region=regions[regions.series_id==regional_focus].sort_values('avg_price')
    rr=risk[risk.series_id==regional_focus].iloc[0]
    regional_label=f'{rr.commodity} / {rr.unit} / {rr.pricetype}'
    save('03_divisions.png',f'Division snapshot: {regional_label}, {asof}',
         lambda ax:(ax.barh(region.division,region.avg_price,color='#147d92'),ax.set_xlabel('BDT per '+rr.unit)),len(region)<2)
    seasons=read('07_seasonality.csv')
    if len(seasons):
        sr=seasons.sort_values(['complete_years','series_id'],ascending=[False,True]).iloc[0]
        season=seasons[seasons.series_id==sr.series_id]
        seasonal_label=f'{sr.commodity} / {sr.unit} / {sr.pricetype}, {int(sr.first_year)}–{int(sr.last_year)} ({int(sr.complete_years)} complete years)'
    else:
        season=seasons;seasonal_label='no complete years'
    save('04_seasonality.png','Within-year fixed-panel seasonality: '+seasonal_label,
         lambda ax:(ax.plot(season.month_number,season.seasonality_index,marker='o'),ax.axhline(100,color='grey',ls='--'),
                    ax.set_xticks(range(1,13)),ax.set_xlabel('Calendar month (Ramadan shifts between years)'),ax.set_ylabel('Year mean = 100')),season.empty)
    coverage=read('analysis_month_selection.csv')
    def coverage_plot(ax):
        ax.plot(pd.to_datetime(coverage.month),coverage.series,label='Food series',marker='o')
        ax.plot(pd.to_datetime(coverage.month),coverage.markets,label='Markets',marker='o')
        ax.axvline(pd.Timestamp(asof),color='#df8e32',ls='--',label='Selected analysis month')
        ax.set_ylabel('Count (retail where available)');ax.legend();ax.tick_params(axis='x',rotation=30)
    save('05_coverage.png','Why the newest source month is not automatically the comparison month',coverage_plot)
    changes=read('04_changes.csv');changes=changes[(changes.series_id==focus)&(changes.month<=asof)]
    if len(changes):
        changes['month']=pd.to_datetime(changes.month)
        changes=changes.set_index('month').reindex(pd.date_range(changes.month.min(),changes.month.max(),freq='MS')).rename_axis('month').reset_index()
    save('06_changes.png','Matched-market changes: '+label,
         lambda ax:(ax.plot(pd.to_datetime(changes.month),changes.mom_pct,label='MoM: matched endpoints'),
                    ax.plot(pd.to_datetime(changes.month),changes.yoy_pct,label='YoY: matched endpoints + history gate'),
                    ax.axhline(0,color='grey',lw=.7),ax.legend(),ax.set_ylabel('Percent change'),ax.tick_params(axis='x',rotation=30)),changes.empty)
