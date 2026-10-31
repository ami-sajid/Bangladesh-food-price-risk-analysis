"""Load a repeatable star schema transaction, without replacing constrained tables."""
import logging
import json
import pandas as pd
from sqlalchemy import text
import config as C
from scripts.common import ProjectError

def run(engine):
    df=pd.read_csv(C.ROOT/'data/processed/prices_clean.csv')
    dates=df[['month_id','month']].drop_duplicates().sort_values('month_id')
    dates['year']=pd.to_datetime(dates.month).dt.year
    dates['month_number']=pd.to_datetime(dates.month).dt.month
    # Calendar is dense: lag 12 means twelve calendar months, even with missing observations.
    full=pd.date_range(dates.month.min(),dates.month.max(),freq='MS')
    dates=pd.DataFrame({'month_id':full.year*12+full.month,'month':full.strftime('%Y-%m-%d'),
                        'year':full.year,'month_number':full.month})
    keys=['division','district','market']
    markets=df.groupby(keys,as_index=False,sort=True)[['latitude','longitude']].median()
    if 'source_market_id' in df:
        ids=df.groupby(keys,as_index=False)['source_market_id'].agg(lambda values: str(values.dropna().iloc[0]) if len(values.dropna()) else None)
        if df.groupby(keys).source_market_id.nunique().gt(1).any():
            raise ProjectError('Different source market IDs share the same labels. Resolve market identity before loading.')
        markets=markets.merge(ids,on=keys,validate='one_to_one')
    markets.insert(0,'market_id',range(1,len(markets)+1))
    series_keys=['commodity','unit','pricetype']
    commodities=df.groupby(series_keys,as_index=False,sort=True).agg(category=('category','first'),is_food=('is_food','min'))
    commodities.insert(0,'series_id',range(1,len(commodities)+1))
    commodities['is_staple']=commodities.commodity.apply(lambda x:int(any(k in x for k in C.CORE_STAPLES)))
    facts=df.merge(markets[keys+['market_id']],on=keys,validate='many_to_one').merge(
        commodities[series_keys+['series_id']],on=series_keys,validate='many_to_one')
    facts['observation_id']=range(1,len(facts)+1)
    facts['outlier_flag']=facts.outlier_flag.astype(int)
    facts=facts.rename(columns={'date':'observation_date'})[
      ['observation_id','month_id','market_id','series_id','observation_date','price','outlier_flag','priceflag','source_row']]
    coverage=facts.merge(commodities[['series_id','is_food','pricetype']],on='series_id')
    coverage=coverage[(coverage.is_food==1)&(coverage.pricetype=='retail')]
    if coverage.empty:
        coverage=facts.merge(commodities[['series_id','is_food']],on='series_id')
        coverage=coverage[coverage.is_food==1]
    if coverage.empty:
        raise ProjectError('No classified food records. Review FOOD_CATEGORIES in config.py.')
    coverage=coverage.groupby('month_id').agg(series=('series_id','nunique'),markets=('market_id','nunique')).reset_index()
    latest=int(coverage.month_id.max())
    recent=coverage[coverage.month_id>=latest-11].copy()
    recent['broad_coverage']=(recent.series>=C.COVERAGE_FRACTION*recent.series.max()) & (recent.markets>=C.COVERAGE_FRACTION*recent.markets.max())
    eligible=recent[recent.broad_coverage]
    if eligible.empty:
        raise ProjectError('No broad-coverage month meets both coverage thresholds. Inspect coverage or set ANALYSIS_MONTH explicitly.')
    chosen=int(eligible.month_id.max())
    if C.ANALYSIS_MONTH:
        stamp=pd.Timestamp(C.ANALYSIS_MONTH);chosen=stamp.year*12+stamp.month
        if chosen not in set(coverage.month_id): raise ProjectError('ANALYSIS_MONTH has no food observations.')
    start=pd.Timestamp(C.RISK_START)
    settings=pd.DataFrame([{'analysis_month_id':chosen,'risk_start_id':start.year*12+start.month,
                           'min_risk_months':C.MIN_RISK_MONTHS,'min_long_months':C.MIN_LONG_HISTORY_MONTHS}])
    recent=recent.merge(dates[['month_id','month']],on='month_id')
    recent.to_csv(C.ROOT/'outputs/tables/analysis_month_selection.csv',index=False)
    metadata={'latest_source_month':df.month.max(),
              'analysis_month':dates.set_index('month_id').loc[chosen,'month'],
              'selection':'explicit override' if C.ANALYSIS_MONTH else 'latest month meeting both trailing-12-month coverage thresholds',
              'coverage_fraction':C.COVERAGE_FRACTION,'risk_start':C.RISK_START}
    pd.DataFrame([metadata]).to_csv(C.ROOT/'outputs/tables/analysis_metadata.csv',index=False)
    (C.ROOT/'outputs/analysis_metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    with engine.begin() as conn:
        # These objects belong only to this project. No CASCADE: external dependencies block refresh.
        for view in ['v_risk_monthly','v_risk_members','v_market_changes','v_market_calendar','v_monthly','v_market_month']:
            conn.execute(text('DROP VIEW IF EXISTS '+view))
        for table in ['fact_prices','dim_commodity','dim_market','dim_date','analysis_settings']:
            conn.execute(text('DROP TABLE IF EXISTS '+table))
        for statement in (C.ROOT/'sql/create_schema.sql').read_text().split(';'):
            if engine.dialect.name=='sqlite': statement=statement.replace('CREATE OR REPLACE VIEW','CREATE VIEW')
            if statement.strip(): conn.execute(text(statement))
        settings.to_sql('analysis_settings',conn,if_exists='append',index=False)
        for table,frame in [('dim_date',dates),('dim_market',markets),('dim_commodity',commodities),('fact_prices',facts)]:
            frame.to_sql(table,conn,if_exists='append',index=False,chunksize=1000)
        count=conn.execute(text('SELECT COUNT(*) FROM fact_prices')).scalar_one()
        if count!=len(df): raise ProjectError('Database count does not match cleaned CSV.')
        for table in ['dim_date','dim_market','dim_commodity','fact_prices']:
            pd.read_sql_query(text('SELECT * FROM '+table),conn).to_csv(C.ROOT/f'outputs/tables/{table}.csv',index=False)
    logging.info('Loaded %s observations into %s.',len(facts),engine.dialect.name)
