"""Artificial regression cases for the real-data design corrections."""
from pathlib import Path
import shutil
import pandas as pd
import pytest
import config as C
from scripts.common import read_raw,sqlite_engine
from scripts.clean_data import clean_frame
from scripts.load_to_db import run as load
from scripts.run_analysis import run as analyze

SAMPLE=Path(__file__).with_name('sample_test_only.csv')

def run_case(rows,tmp_path,monkeypatch):
    for directory in ['sql','outputs/tables','data/processed']:
        (tmp_path/directory).mkdir(parents=True,exist_ok=True)
    for name in ['create_schema.sql','analysis_queries.sql','verification_queries.sql']:
        shutil.copy(C.ROOT/'sql'/name,tmp_path/'sql'/name)
    clean,_,_=clean_frame(pd.DataFrame(rows))
    clean.to_csv(tmp_path/'data/processed/prices_clean.csv',index=False)
    monkeypatch.setattr(C,'ROOT',tmp_path)
    engine=sqlite_engine()
    try: load(engine);analyze(engine)
    finally: engine.dispose()
    return lambda name:pd.read_csv(tmp_path/'outputs/tables'/name)

def test_anomaly_flag_and_nonfood_preservation():
    raw,_=read_raw(SAMPLE);frame=raw.iloc[[0,1,6]].copy()
    frame.iloc[0,frame.columns.get_loc('date')]='1900-08-15'
    frame.iloc[1,frame.columns.get_loc('category')]='non-food'
    clean,_,rejected=clean_frame(frame)
    assert len(clean)==2 and len(rejected)==1
    assert bool(rejected.iloc[0].date_quality_flag)
    assert clean.is_food.sum()==1
    assert 'non-food' in clean.food_class.values

def test_new_expensive_market_does_not_create_inflation(tmp_path,monkeypatch):
    raw,_=read_raw(SAMPLE);base=raw.iloc[0]
    rows=[]
    for i,date in enumerate(pd.date_range('2024-01-01',periods=24,freq='MS')):
        row=base.copy();row['date']=str(date.date());row['price']=100+i;rows.append(row)
    entrant=rows[-1].copy();entrant['market']='NEW EXPENSIVE MARKET';entrant['price']=1000;rows.append(entrant)
    read=run_case(rows,tmp_path,monkeypatch)
    latest=read('04_changes.csv').iloc[-1]
    assert latest.mom_markets==1 and latest.observed_markets==2
    assert latest.mom_pct==pytest.approx((123/122-1)*100)
    assert latest.yoy_pct==pytest.approx((123/111-1)*100)
    risk=read('11_risk_score.csv').iloc[0]
    assert risk.market_count==1 and risk.available_markets==2
    assert risk.avg_price==123
    prices=pd.Series(range(112,124))
    cv=prices.std(ddof=0)/prices.mean()
    expected=100*(0.6*min(cv/0.3,1)+0.4*min(max((123/122-1)/0.2,0),1))
    assert risk.risk_score==pytest.approx(expected)
    assert len(read('risk_panel_members.csv'))==1

def test_yoy_sparse_endpoints_fail_history_gate(tmp_path,monkeypatch):
    raw,_=read_raw(SAMPLE);base=raw.iloc[0];rows=[]
    for i,date in enumerate(pd.date_range('2024-01-01',periods=13,freq='MS')):
        row=base.copy();row['date']=str(date.date());row['price']=100+i;rows.append(row)
    for pos,price in [(0,10),(12,1000)]:
        row=rows[pos].copy();row['market']='SPARSE MARKET';row['price']=price;rows.append(row)
    read=run_case(rows,tmp_path,monkeypatch)
    latest=read('04_changes.csv').iloc[-1]
    assert latest.observed_markets==2 and latest.yoy_markets==1
    assert latest.yoy_pct==pytest.approx(12)

def test_risk_cannot_include_pre2024_window(tmp_path,monkeypatch):
    raw,_=read_raw(SAMPLE);base=raw.iloc[0];rows=[]
    for i,date in enumerate(pd.date_range('2023-01-01',periods=18,freq='MS')):
        row=base.copy();row['date']=str(date.date());row['price']=100+i;rows.append(row)
    read=run_case(rows,tmp_path,monkeypatch)
    assert read('11_risk_score.csv').risk_score.isna().all()
    assert read('risk_panel_members.csv').empty
