"""Profile the source before dropping or imputing any observations."""
import json
import pandas as pd
import config as C
from scripts.common import read_raw, parse_dates, markdown_table

def run():
    df, meta = read_raw()
    dates = parse_dates(df.date)
    summary = {'metadata': meta, 'rows': len(df), 'columns': len(df.columns),
               'raw_exact_duplicates': int(df.duplicated().sum()),
               'valid_date_min': str(dates.min()), 'valid_date_max': str(dates.max()),
               'invalid_dates': int(dates.isna().sum()),
               'market_name_count': int(df.market.nunique()),
               'commodity_count': int(df.commodity.nunique())}
    (C.ROOT/'outputs/profile.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    fields = pd.DataFrame({'field':df.columns, 'loaded_dtype':df.dtypes.astype(str).values,
                           'inferred_dtype':[pd.api.types.infer_dtype(df[c].dropna()) for c in df],
                           'null_count':df.isna().sum().values,
                           'null_percent':(df.isna().mean()*100).values})
    fields.to_csv(C.ROOT/'outputs/tables/profile_fields.csv',index=False)
    report = '# Source profile\n\n'+json.dumps(summary,indent=2)+'\n\n'+markdown_table(fields,100)
    for col in ['unit','currency','pricetype','priceflag']:
        counts=df[col].fillna('(missing)').value_counts().rename_axis(col).reset_index(name='rows')
        counts.to_csv(C.ROOT/f'outputs/tables/profile_{col}.csv',index=False)
        report+='\n\n## '+col+'\n\n'+markdown_table(counts,100)
    (C.ROOT/'docs/PROFILING_REPORT.md').write_text(report,encoding='utf-8')
    meanings = {'date':'Source observation date; retained, then grouped by month.',
      'division':'First administrative level; required for regional comparisons.',
      'district':'Second administrative level; Unknown if absent.',
      'market':'Market label; identity also includes division and district.',
      'commodity':'Exact commodity/grade; never combined across units.',
      'unit':'Quoted unit, retained unchanged except whitespace/case and explicit aliases.',
      'pricetype':'Retail, wholesale or other source type; kept separate.',
      'price':'Positive nominal BDT per source unit; no inflation adjustment.',
      'currency':'Only configured BDT aliases retained.',
      'priceflag':'Source flag, retained independently from our outlier flag.',
      'category':'Source commodity category, Unknown if unavailable.',
      'latitude':'Optional decimal degrees; invalid values become null.',
      'longitude':'Optional decimal degrees; invalid values become null.',
      'usdprice':'Optional source USD price; not used in BDT analysis.',
      'source_market_id':'Optional publisher market identifier, preserved and checked against market labels.',
      'source_commodity_id':'Optional publisher commodity identifier, preserved in clean data.'}
    dictionary = pd.DataFrame([{'canonical':k,'source_header':str(v),'required':k in C.REQUIRED_COLUMNS,
                               'meaning':meanings[k]} for k,v in C.COLUMN_MAP.items()])
    text='# Data dictionary\n\n'+markdown_table(dictionary,100)
    text+='\n\nDerived: source_row = source record position after metadata removal; month = first day; '
    text+='month_id = year*12+month; outlier_flag = within-series 3-IQR flag (minimum 8 observations); '
    text+='series_id = commodity-unit-price type key; market_id = division-district-market key. '
    text+='is_food = explicit category eligibility for food analyses; food_class = food/non-food/unclassified; '
    text+='source_flag_class = actual/aggregate/mixed/unknown source label; date_quality_flag = pre-range anomaly (true in rejected audit). '
    text+='Missing optional fields are not evidence that a source did not collect them.\n'
    (C.ROOT/'docs/DATA_DICTIONARY.md').write_text(text,encoding='utf-8')

    valid=df.copy()
    valid['year']=dates.dt.year
    valid['month']=dates.dt.to_period('M').astype(str)
    for period in ['year','month']:
        counts=valid.groupby(period).agg(rows=('price','size'),markets=('market','nunique'),commodities=('commodity','nunique'))
        counts.to_csv(C.ROOT/f'outputs/tables/source_coverage_{period}.csv')
    flags=valid.groupby(['year','priceflag']).size().reset_index(name='rows')
    flags.to_csv(C.ROOT/'outputs/tables/source_flags_by_year.csv',index=False)
    valid.groupby(['category','commodity','unit','pricetype']).size().reset_index(name='rows').to_csv(C.ROOT/'outputs/tables/source_inventory.csv',index=False)
