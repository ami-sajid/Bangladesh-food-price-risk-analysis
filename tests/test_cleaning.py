"""Artificial data only. No row here is evidence about Bangladesh food prices."""
from pathlib import Path
import pandas as pd
import pytest
import config as C
from scripts.common import read_raw,ProjectError
from scripts.clean_data import clean_frame
SAMPLE=Path(__file__).with_name('sample_test_only.csv')

def test_hxl_and_cleaning():
    raw,meta=read_raw(SAMPLE)
    result,log,rejected=clean_frame(raw)
    assert meta['hxl_rows_skipped']==1
    assert len(raw)==7 and len(result)==3 and len(rejected)==4
    assert log['rows_before']-log['rows_after']==len(rejected)
    assert set(result.currency)=={'BDT'}
    assert set(result.market)=={'test market'}
    assert set(result.unit)=={'kg','100 kg'}
    assert result.loc[result.unit=='100 kg','price'].iloc[0]==5000

def test_friendly_missing_columns(tmp_path):
    file=tmp_path/'broken.csv';file.write_text('date,price\n2022-01-01,10\n')
    with pytest.raises(ProjectError,match='Missing required columns:.*division'):
        read_raw(file)

def test_custom_column_map_and_trimmed_headers(tmp_path,monkeypatch):
    content=SAMPLE.read_text().replace('date,admin1',' When , Province ',1)
    file=tmp_path/'custom.csv';file.write_text(content)
    monkeypatch.setitem(C.COLUMN_MAP,'date','when');monkeypatch.setitem(C.COLUMN_MAP,'division','province')
    frame,_=read_raw(file)
    assert 'date' in frame and 'division' in frame

def test_outlier_retained():
    raw,_=read_raw(SAMPLE)
    frame=pd.concat([raw.iloc[[0]]]*12,ignore_index=True)
    frame['date']=pd.date_range('2022-01-01',periods=12,freq='MS').strftime('%Y-%m-%d')
    frame['price']=[49,50,51,50,52,49,50,51,50,52,49,1000]
    result,_,_=clean_frame(frame)
    assert len(result)==12
    assert result.iloc[-1].outlier_flag

def test_ambiguous_dates_require_format(monkeypatch):
    raw,_=read_raw(SAMPLE);raw=raw.iloc[[0]].copy();raw['date']='03/04/2022'
    with pytest.raises(ProjectError,match='Slash dates'):
        clean_frame(raw)
    monkeypatch.setattr(C,'DATE_FORMAT','%d/%m/%Y')
    result,_,_=clean_frame(raw)
    assert result.date.iloc[0]=='2022-04-03'

def test_missing_identity_and_infinite_price():
    raw,_=read_raw(SAMPLE);raw=raw.iloc[[0,1,6]].copy()
    raw.iloc[0,raw.columns.get_loc('price')]='inf'
    raw.iloc[1,raw.columns.get_loc('market')]=pd.NA
    result,_,rejected=clean_frame(raw)
    assert len(result)==1 and len(rejected)==2

def test_optional_columns_absent(tmp_path):
    raw=pd.read_csv(SAMPLE,dtype=str).iloc[1:]
    raw=raw.drop(columns=['admin2','latitude','longitude','category','priceflag','usdprice'])
    file=tmp_path/'optional.csv';raw.to_csv(file,index=False)
    frame,_=read_raw(file);result,_,_=clean_frame(frame)
    assert set(result.district)=={'unknown'}
    assert result.latitude.isna().all()
