"""SQL regression tests with artificial prices: calendar gaps and risk eligibility."""
import shutil
from pathlib import Path
import pandas as pd
import pytest
import config as C
from scripts.common import read_raw,sqlite_engine
from scripts.clean_data import clean_frame
from scripts.load_to_db import run as load
from scripts.run_analysis import run as analyze

def test_calendar_gaps_and_scoring(tmp_path,monkeypatch):
    for directory in ['sql','outputs/tables','data/processed']:
        (tmp_path/directory).mkdir(parents=True,exist_ok=True)
    for name in ['create_schema.sql','analysis_queries.sql','verification_queries.sql']:
        shutil.copy(C.ROOT/'sql'/name,tmp_path/'sql'/name)
    base,_=read_raw(Path(__file__).with_name('sample_test_only.csv'))
    rows=[]
    for i,date in enumerate(pd.date_range('2024-01-01',periods=24,freq='MS')):
        for commodity in ['complete','gapped','stale']:
            if commodity=='gapped' and i==22: continue
            if commodity=='stale' and i==23: continue
            row=base.iloc[0].copy();row['date']=date.strftime('%Y-%m-%d')
            row['commodity']=commodity;row['price']=100+i
            rows.append(row)
    clean,_,_=clean_frame(pd.DataFrame(rows));clean.to_csv(tmp_path/'data/processed/prices_clean.csv',index=False)
    monkeypatch.setattr(C,'ROOT',tmp_path)
    engine=sqlite_engine()
    load(engine);analyze(engine)
    # Loading again must not double the fact rows.
    load(engine);analyze(engine)
    changes=pd.read_csv(tmp_path/'outputs/tables/04_changes.csv')
    latest=changes[changes.month=='2025-12-01'].set_index('commodity')
    assert pd.isna(latest.loc['gapped','mom_pct'])
    assert latest.loc['complete','yoy_pct']==pytest.approx((123/111-1)*100)
    risk=pd.read_csv(tmp_path/'outputs/tables/11_risk_score.csv').set_index('commodity')
    assert 0<=risk.loc['complete','risk_score']<=100
    assert pd.isna(risk.loc['gapped','risk_score'])
    assert risk.loc['stale','status'].startswith('no observation')
    engine.dispose()
