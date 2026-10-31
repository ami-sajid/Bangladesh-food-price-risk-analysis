"""Execute all twelve named SQL blocks using either backend."""
import logging
import re
import pandas as pd
from sqlalchemy import text
import config as C
from scripts.common import ProjectError

def run(engine):
    if not (C.MIN_RISK_MONTHS==12 and C.VOLATILITY_CAP>0 and C.RECENT_CHANGE_CAP>0
            and 0<=C.VOLATILITY_WEIGHT<=1):
        raise ProjectError('Risk settings invalid: MIN_RISK_MONTHS must equal 12, positive caps, weight 0..1.')
    source=(C.ROOT/'sql/analysis_queries.sql').read_text(encoding='utf-8')
    blocks=re.split(r'^-- name: ',source,flags=re.M)[1:]
    if len(blocks)!=12: raise ProjectError('Expected twelve named SQL blocks.')
    params={'cv_cap':C.VOLATILITY_CAP,'change_cap':C.RECENT_CHANGE_CAP,
            'min_months':C.MIN_RISK_MONTHS,'vol_weight':C.VOLATILITY_WEIGHT}
    with engine.connect() as conn:
        for block in blocks:
            name,query=block.split('\n',1)
            frame=pd.read_sql_query(text(query),conn,params=params)
            frame.to_csv(C.ROOT/f'outputs/tables/{name}.csv',index=False)
            logging.info('Analysis %s: %s rows',name,len(frame))
        # Transparent panel membership and chart-ready risk history are supplemental exports.
        extras={
            'risk_panel_members': 'SELECT c.series_id,c.commodity,c.unit,c.pricetype,k.market_id,k.market,k.division,k.district FROM v_risk_members r JOIN dim_commodity c ON c.series_id=r.series_id JOIN dim_market k ON k.market_id=r.market_id ORDER BY c.series_id,k.market_id',
            'risk_fixed_panel_monthly': 'SELECT r.*,d.month FROM v_risk_monthly r JOIN dim_date d ON d.month_id=r.month_id ORDER BY r.series_id,r.month_id'
        }
        for name,query in extras.items():
            pd.read_sql_query(text(query),conn).to_csv(C.ROOT/f'outputs/tables/{name}.csv',index=False)
        for i,statement in enumerate((C.ROOT/'sql/verification_queries.sql').read_text().split(';'),1):
            if not statement.strip(): continue
            result=pd.read_sql_query(text(statement),conn)
            result.to_csv(C.ROOT/f'outputs/tables/verification_{i}.csv',index=False)
            if i in (2,3) and result.iloc[0,0]!=0:
                raise ProjectError('Database verification failed. See verification CSVs.')
