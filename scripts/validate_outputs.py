"""Independently reconcile SQL comparisons against cleaned observations in pandas."""
import json
import math
import pandas as pd
import config as C
from scripts.common import ProjectError


def equal_number(left,right,label):
    if pd.isna(left) and pd.isna(right):
        return
    if pd.isna(left) or pd.isna(right) or not math.isclose(float(left),float(right),rel_tol=1e-8,abs_tol=1e-8):
        raise ProjectError('Independent reconciliation failed: '+label)


def run():
    t=C.ROOT/'outputs/tables'
    prices=pd.read_csv(C.ROOT/'data/processed/prices_clean.csv')
    series=pd.read_csv(t/'dim_commodity.csv')
    markets=pd.read_csv(t/'dim_market.csv')
    keys=['commodity','unit','pricetype']
    prices=prices.merge(series[keys+['series_id']],on=keys,validate='many_to_one')
    market_keys=['division','district','market']
    prices=prices.merge(markets[market_keys+['market_id']],on=market_keys,validate='many_to_one')
    food=prices[prices.is_food==1]
    monthly=food.groupby(['series_id','market_id','month_id'],as_index=False).price.mean()
    monthly=monthly.sort_values(['series_id','market_id','month_id'])
    monthly['history_months']=monthly.groupby(['series_id','market_id']).cumcount()+1
    meta=json.loads((C.ROOT/'outputs/analysis_metadata.json').read_text())
    date=pd.Timestamp(meta['analysis_month']);asof=date.year*12+date.month
    start=pd.Timestamp(C.RISK_START);start_id=start.year*12+start.month

    # Independent endpoint joins, not the SQL dense-calendar/LAG implementation.
    keys=['series_id','market_id','month_id']
    previous=monthly[keys+['price']].rename(columns={'price':'previous_price'})
    previous['month_id']+=1
    year_ago=monthly[keys+['price']].rename(columns={'price':'year_ago_price'})
    year_ago['month_id']+=12
    pairs=monthly.merge(previous,on=keys,how='left',validate='one_to_one').merge(year_ago,on=keys,how='left',validate='one_to_one')
    pairs=pairs[pairs.month_id>=start_id].copy()
    mom_ok=pairs.previous_price.notna()
    yoy_ok=pairs.year_ago_price.notna() & pairs.history_months.ge(12)
    pairs['mom_current']=pairs.price.where(mom_ok)
    pairs['yoy_current']=pairs.price.where(yoy_ok)
    pairs['yoy_previous']=pairs.year_ago_price.where(yoy_ok)
    expected=pairs.groupby(['series_id','month_id']).agg(
        observed_markets=('price','count'),mom_markets=('mom_current','count'),
        yoy_markets=('yoy_current','count'),mom_current=('mom_current','mean'),
        previous=('previous_price','mean'),yoy_current=('yoy_current','mean'),
        year_ago=('yoy_previous','mean'))
    expected['mom_pct']=100*(expected.mom_current/expected.previous-1)
    expected['yoy_pct']=100*(expected.yoy_current/expected.year_ago-1)
    exported=pd.read_csv(t/'04_changes.csv').set_index(['series_id','month_id'])
    if set(expected.index)!=set(exported.index):
        raise ProjectError('Independent reconciliation failed: change-row keys differ.')
    for key,row in expected.iterrows():
        for field in ['observed_markets','mom_markets','yoy_markets','mom_pct','yoy_pct']:
            equal_number(row[field],exported.loc[key,field],f'changes {key}, {field}')

    # Rebuild each fixed twelve-month cohort directly from cleaned data.
    window=monthly[(monthly.month_id>=asof-11)&(monthly.month_id<=asof)&(monthly.month_id>=start_id)]
    counts=window.groupby(['series_id','market_id']).size()
    members=counts[counts==12].reset_index()[['series_id','market_id']]
    observed_members=pd.read_csv(t/'risk_panel_members.csv')
    if set(map(tuple,members.values))!=set(map(tuple,observed_members[['series_id','market_id']].values)):
        raise ProjectError('Independent reconciliation failed: risk panel membership differs.')
    risk=pd.read_csv(t/'11_risk_score.csv')
    checked=0
    for row in risk.itertuples():
        ids=members.loc[members.series_id==row.series_id,'market_id']
        if len(ids)==0:
            if pd.notna(row.risk_score):
                raise ProjectError('A risk score exists without a complete market panel.')
            continue
        means=window[(window.series_id==row.series_id)&window.market_id.isin(ids)].groupby('month_id').price.mean().sort_index()
        cv=means.std(ddof=0)/means.mean()
        mom=means.loc[asof]/means.loc[asof-1]-1
        score=100*(C.VOLATILITY_WEIGHT*min(cv/C.VOLATILITY_CAP,1)+(1-C.VOLATILITY_WEIGHT)*min(max(mom/C.RECENT_CHANGE_CAP,0),1))
        for label,value,actual in [('cv',cv,row.cv),('mom_pct',100*mom,row.mom_pct),('score',score,row.risk_score),('market count',len(ids),row.market_count)]:
            equal_number(value,actual,f'risk {row.series_id}, {label}')
        checked+=1

    # Verify retained facts and rejected rows reconcile to the original parsed count.
    log=json.loads((C.ROOT/'outputs/cleaning_log.json').read_text())
    facts=pd.read_csv(t/'fact_prices.csv')
    rejected=pd.read_csv(C.ROOT/'data/processed/rejected_rows.csv')
    if len(facts)!=len(prices) or len(prices)+len(rejected)!=log['rows_before']:
        raise ProjectError('Independent row-count reconciliation failed.')
    summary={'status':'passed','comparison_rows_checked':len(expected),'risk_scores_checked':checked,
             'risk_panel_memberships_checked':len(members),'cleaned_rows':len(prices),
             'food_rows':len(food),'quarantined_rows':len(rejected),'analysis_month':meta['analysis_month']}
    (C.ROOT/'outputs/independent_validation.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary

if __name__=='__main__':
    print(json.dumps(run(),indent=2))
