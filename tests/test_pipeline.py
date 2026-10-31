"""End-to-end check in an isolated copy. All values are TEST DATA ONLY."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import pandas as pd
import pytest
import config as C

@pytest.mark.parametrize('long_history',[False,True])
def test_entire_pipeline(tmp_path,long_history):
    project=tmp_path/'project'
    shutil.copytree(C.ROOT,project,ignore=shutil.ignore_patterns('.venv','__pycache__','.pytest_cache','outputs','data','.env'))
    for d in ['data/raw','data/processed','outputs/tables','outputs/charts']:
        (project/d).mkdir(parents=True,exist_ok=True)
    base=pd.read_csv(Path(__file__).with_name('sample_test_only.csv'),dtype=str).iloc[1].to_dict()
    rows=[]
    for i,date in enumerate(pd.date_range('2024-01-01',periods=24 if long_history else 2,freq='MS')):
        for commodity in ['TEST Rice','TEST Lentils']:
            for division,market,offset in [('TEST North','TEST A',0),('TEST North','TEST B',3),('TEST South','TEST C',7)]:
                row=base.copy();row.update(date=str(date.date()),commodity=commodity,
                    admin1=division,market=market,price=50+i+offset+(10 if commodity=='TEST Lentils' else 0))
                rows.append(row)
    pd.DataFrame(rows).to_csv(project/'data/raw/TEST_ONLY.csv',index=False)
    env=os.environ.copy();env['DB_BACKEND']='sqlite';env['RAW_FILE']='TEST_ONLY.csv'
    result=subprocess.run([sys.executable,str(project/'run_all.py')],cwd=project,env=env,
                          capture_output=True,text=True,timeout=120)
    assert result.returncode==0, result.stdout+result.stderr
    status=json.loads((project/'outputs/run_status.json').read_text())
    assert status['status']=='success'
    assert len(list((project/'outputs/charts').glob('*.png')))==6
    assert len(list((project/'outputs/tables').glob('[01][0-9]_*.csv')))==12
    report=(project/'docs/FINDINGS.md').read_text()
    assert 'Eligible food-risk series:' in report
    assert 'Cleaned observations:' in report
    readme=(project/'README.md').read_text()
    assert 'Not run on real data yet' not in readme
    assert len(pd.read_csv(project/'outputs/tables/fact_prices.csv'))==len(rows)
