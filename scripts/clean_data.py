"""Conservative cleaning: no price imputation and no automatic unit conversions."""
import json
import pandas as pd
import config as C
from scripts.common import read_raw, parse_dates, ProjectError

def clean_frame(raw):
    df=raw.copy()
    events=[]
    def note(action, count, reason):
        events.append({'action':action,'rows':int(count),'reason':reason})
    before=len(df)
    df['source_row']=range(1,len(df)+1)
    for col in ['division','district','market','category','commodity','unit','priceflag','pricetype','currency']:
        old=df[col].copy()
        df[col]=df[col].astype('string').str.strip().str.replace(r'\s+',' ',regex=True).str.lower()
        df[col]=df[col].replace('',pd.NA).replace(C.NAME_ALIASES.get(col,{}))
        note('Normalize '+col, (old.fillna('')!=df[col].fillna('')).sum(), 'Whitespace/case; explicit aliases only')
    df['date']=parse_dates(df.date)
    df['price']=pd.to_numeric(df.price,errors='coerce')
    for col, low, high in [('latitude',-90,90),('longitude',-180,180),('usdprice',0,float('inf'))]:
        values=pd.to_numeric(df[col],errors='coerce')
        invalid=values.notna() & (~values.between(low,high) | values.isin([float('inf'),-float('inf')]))
        note('Null invalid '+col,invalid.sum(),'Optional field; never impute coordinates or USD values')
        df[col]=values.mask(invalid)
    rejected=[]
    def remove(mask, reason):
        nonlocal df
        dropped=df.loc[mask].copy();dropped['rejection_reason']=reason;rejected.append(dropped)
        note('Remove',len(dropped),reason);df=df.loc[~mask].copy()
    remove(~df.currency.isin(C.BDT_ALIASES),'Currency missing or not recognized as BDT')
    df['currency']='BDT'
    remove(df.date.isna(),'Invalid or missing date')
    df['date_quality_flag']=df.date.lt(pd.Timestamp(C.MIN_VALID_DATE))
    remove(df.date_quality_flag,'Date before configured source-valid range; flagged and quarantined')
    remove(df.price.isna() | (df.price<=0) | df.price.isin([float('inf'),-float('inf')]),'Price must be finite and positive')
    remove(df[['division','market','commodity','unit','pricetype']].isna().any(axis=1),'Missing comparison identity')
    for col in ['district','category','priceflag']:
        note('Fill '+col,df[col].isna().sum(),'Optional descriptive field becomes unknown')
        df[col]=df[col].fillna('unknown')
    comparable=[k for k in C.COLUMN_MAP if k in df]
    remove(df.duplicated(subset=comparable),'Exact normalized record duplicate')
    if df.empty:
        raise ProjectError('No usable BDT records remain. Inspect currency, date format, required values and COLUMN_MAP.')
    df['is_food']=df.category.isin(C.FOOD_CATEGORIES).astype(int)
    df['food_class']=df.category.map(lambda value: 'food' if value in C.FOOD_CATEGORIES else ('non-food' if value in C.NON_FOOD_CATEGORIES else 'unclassified'))
    df['source_flag_class']=df.priceflag.map(lambda value: value if value in {'actual','aggregate','actual,aggregate'} else 'unknown')
    note('Exclude from food analyses', (df.is_food==0).sum(), 'Keep non-food/unclassified records in clean data and coverage audits')
    df['outlier_flag']=False
    group=['division','district','market','commodity','unit','pricetype']
    for _, idx in df.groupby(group).groups.items():
        values=df.loc[idx,'price']
        if len(values)<8: continue
        q1,q3=values.quantile([.25,.75]);iqr=q3-q1
        if iqr>0:
            df.loc[idx,'outlier_flag']=(values<q1-C.OUTLIER_IQR_MULTIPLIER*iqr)|(values>q3+C.OUTLIER_IQR_MULTIPLIER*iqr)
    note('Flag outliers',df.outlier_flag.sum(),'Retained; 3-IQR within market/commodity/unit/type, minimum 8 records; zero IQR unflagged')
    df['month']=df.date.dt.to_period('M').dt.to_timestamp().dt.strftime('%Y-%m-%d')
    df['month_id']=df.date.dt.year*12+df.date.dt.month
    df['date']=df.date.dt.strftime('%Y-%m-%d')
    log={'rows_before':before,'rows_after':len(df),'events':events}
    return df.reset_index(drop=True),log,pd.concat(rejected,ignore_index=True)

def run():
    raw,_=read_raw()
    df,log,rejected=clean_frame(raw)
    df.to_csv(C.ROOT/'data/processed/prices_clean.csv',index=False)
    rejected.to_csv(C.ROOT/'data/processed/rejected_rows.csv',index=False)
    (C.ROOT/'outputs/cleaning_log.json').write_text(json.dumps(log,indent=2),encoding='utf-8')
    (C.ROOT/'docs/CLEANING_LOG.md').write_text('# Cleaning log\n\n```json\n'+json.dumps(log,indent=2)+'\n```\n',encoding='utf-8')
