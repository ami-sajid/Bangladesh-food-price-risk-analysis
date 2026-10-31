"""Create editable Power BI PBIP/PBIR project from the verified analysis snapshot.

Power BI Desktop is Windows-only and unavailable in this build environment. This
source file is a best-effort native PBIP export; open in Desktop and check visuals
before treating it as a validated PBIX. There are no fake screenshot claims.
"""
from pathlib import Path
import json, hashlib, uuid, math, re
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]; T=ROOT/'outputs/tables';BASE=ROOT/'powerbi'
N='Bangladesh_Food_Price_Intelligence';R=BASE/(N+'.Report');M=BASE/(N+'.SemanticModel')

SC='https://developer.microsoft.com/json-schemas/fabric/'
def write(path,obj):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def id20(s):return hashlib.sha1(s.encode()).hexdigest()[:20]
def load(name):return pd.read_csv(T/(name+'.csv'))

def literal(v,kind):
 if pd.isna(v):return 'null'
 if kind=='string':return '"'+str(v).replace('"','""').replace('\n',' ')+'"'
 if kind=='int64':return str(int(v))
 if kind=='double':return format(float(v),'.12g')
 raise ValueError(kind)

def mk_table(name,df,cols,measures=None):
 typemap={'string':'text','int64':'number','double':'number'}
 types=', '.join(f'{col} = nullable {typemap[t]}' for col,t in cols)
 data='\n        '.join('{'+', '.join(literal(getattr(row,col),t) for col,t in cols)+'},' for row in df.itertuples(index=False))
 if data.endswith(','):data=data[:-1]
 m='let\n    Source = #table(type table ['+types+'], {\n        '+data+'\n    })\nin\n    Source'
 table={'name':name,'columns':[{'name':c,'dataType':t,'sourceColumn':c} for c,t in cols], 'partitions':[{'name':name+'-snapshot','mode':'import','source':{'type':'m','expression':m}}]}
 if measures: table['measures']=[{'name':n,'expression':e,'formatString':f} for n,e,f in measures]
 return table

def prepare():
 risk=load('11_risk_score');risk=risk[risk.risk_score.notna()].copy(); risk['series_label']=risk.commodity.str.title()+' | '+risk.unit+' | '+risk.pricetype
 risk=risk[['series_id','series_label','commodity','unit','pricetype','risk_score','mom_pct','cv','market_count']]
 changes=load('04_changes');meta=load('analysis_metadata').iloc[0];changes=changes[changes.month==meta['analysis_month']].copy();changes['series_label']=changes.commodity.str.title()+' | '+changes.unit+' | '+changes.pricetype
 changes=changes[changes.mom_pct.notna()][['series_label','mom_pct','mom_markets','yoy_pct','yoy_markets']]
 staple=load('05_since_2022');staple=staple[staple.change_pct.notna()][['commodity','matched_markets','change_pct']]
 cov=load('analysis_month_selection').tail(12)[['month','series','markets','broad_coverage']].copy();cov['month']=cov.month.str[:7];cov['broad_coverage']=cov['broad_coverage'].astype(str)
 monthly=load('risk_fixed_panel_monthly');monthly=monthly.merge(risk[['series_id','series_label']],on='series_id',how='inner');monthly['month']=monthly.month.str[:7];monthly=monthly[['series_id','series_label','month','avg_price','market_count']]
 chili=monthly[monthly.series_label.str.startswith('Chili (Green)')].copy();
 if chili.empty:chili=monthly[monthly.series_id==monthly.series_id.iloc[0]]
 ret=[
  mk_table('Risk',risk,[('series_id','int64'),('series_label','string'),('commodity','string'),('unit','string'),('pricetype','string'),('risk_score','double'),('mom_pct','double'),('cv','double'),('market_count','int64')],[('Eligible Series','COUNTROWS(Risk)','0'),('Highest Risk','MAX(Risk[risk_score])','0.0')]),
  mk_table('Changes',changes,[('series_label','string'),('mom_pct','double'),('mom_markets','int64'),('yoy_pct','double'),('yoy_markets','int64')]),
  mk_table('Staples',staple,[('commodity','string'),('matched_markets','int64'),('change_pct','double')]),
  mk_table('Coverage',cov,[('month','string'),('series','int64'),('markets','int64'),('broad_coverage','string')]),
  mk_table('RiskMonthly',monthly,[('series_id','int64'),('series_label','string'),('month','string'),('avg_price','double'),('market_count','int64')]),
  mk_table('ChiliPrice',chili,[('series_id','int64'),('series_label','string'),('month','string'),('avg_price','double'),('market_count','int64')])]
 return ret


def file_schema(rel):return SC+rel

def prop_col(table,col):
 return {'field':{'Column':{'Expression':{'SourceRef':{'Entity':table}},'Property':col}},'queryRef':f'{table}.{col}','nativeQueryRef':col}
def prop_sum(table,col,fn=1):
 names={0:'Sum',1:'Average',2:'DistinctCount',3:'Min',4:'Max',5:'Count'}
 return {'field':{'Aggregation':{'Expression':{'Column':{'Expression':{'SourceRef':{'Entity':table}},'Property':col}},'Function':fn}},'queryRef':f'{names[fn]}({table}.{col})','nativeQueryRef':col}
def prop_measure(table,col):return {'field':{'Measure':{'Expression':{'SourceRef':{'Entity':table}},'Property':col}},'queryRef':f'{table}.{col}','nativeQueryRef':col}
def e(v):return {'expr':{'Literal':{'Value':v}}}

def visual(page,slug,vtype,x,y,w,h,fields,title,sort=None):
 name=id20(page+slug);qs={role:{'projections':vals} for role,vals in fields.items()}
 v={'$schema':file_schema('item/report/definition/visualContainer/2.7.0/schema.json'),'name':name,'position':{'x':x,'y':y,'z':0,'width':w,'height':h,'tabOrder':0}, 'visual':{'visualType':vtype,'query':{'queryState':qs},'drillFilterOtherVisuals':True}}
 if sort:v['visual']['query']['sortDefinition']=sort
 if title:
  v['visual']['visualContainerObjects']={'title':[{'properties':{'show':e('true'),'text':e("'"+title.replace("'","''")+"'")}}]}
 write(R/'definition/pages'/id20(page)/'visuals'/name/'visual.json',v)

def build():
 model={'name':N,'compatibilityLevel':1600,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','tables':prepare()}}
 write(M/'model.bim',model)
 write(M/'definition.pbism',{'$schema':file_schema('item/semanticModel/definitionProperties/1.0.0/schema.json'),'version':'1.0','settings':{}})
 write(BASE/(N+'.pbip'),{'$schema':file_schema('pbip/pbipProperties/1.0.0/schema.json'),'version':'1.0','artifacts':[{'report':{'path':N+'.Report'}}], 'settings':{'enableAutoRecovery':True}})
 write(R/'definition.pbir',{'$schema':file_schema('item/report/definitionProperties/2.0.0/schema.json'),'version':'4.0','datasetReference':{'byPath':{'path':'../'+N+'.SemanticModel'}}})
 write(R/'definition/version.json',{'$schema':file_schema('item/report/definition/versionMetadata/1.0.0/schema.json'),'version':'2.0.0'})
 theme='MarketLensBase'
 # BaseTheme is registered as a physical resource as required by PBIR, with simple JSON theme properties.
 write(R/f'StaticResources/SharedResources/BaseThemes/{theme}.json',{'name':theme,'dataColors':['#12B6A5','#4E89DB','#EA777E','#F4B75B','#766BDD'],'background':'#FFFFFF','foreground':'#14243A','tableAccent':'#12B6A5'})
 write(R/'definition/report.json',{'$schema':file_schema('item/report/definition/report/3.2.0/schema.json'),'themeCollection':{'baseTheme':{'name':theme,'reportVersionAtImport':{'visual':'2.6.0','report':'3.1.0','page':'2.3.0'},'type':'SharedResources'}},'resourcePackages':[{'name':'SharedResources','type':'SharedResources','items':[{'name':theme,'path':f'BaseThemes/{theme}.json','type':'BaseTheme'}]}],'settings':{'useStylableVisualContainerHeader':True,'exportDataMode':'AllowSummarized','defaultDrillFilterOtherVisuals':True,'useEnhancedTooltips':True}})
 pages=[('Executive Risk Overview','High-scoring commodities in the Chittagong four-market panel'),('Commodity Price Explorer','Green chili: 12-month matched-panel price history'),('Market Moves and Staples','May 2026 matched-market changes and 2022 baseline'),('Coverage and Methods','Reporting coverage and measurement caveats')]
 names=[]
 for page,description in pages:
  pid=id20(page); names.append(pid)
  write(R/'definition/pages'/pid/'page.json',{'$schema':file_schema('item/report/definition/page/2.1.0/schema.json'),'name':pid,'displayName':page,'displayOption':'FitToPage','height':720,'width':1280})
 write(R/'definition/pages/pages.json',{'$schema':file_schema('item/report/definition/pagesMetadata/1.0.0/schema.json'),'pageOrder':names,'activePageName':names[0]})
 p=pages[0][0]
 visual(p,'eligible','cardVisual',45,45,350,140,{'Data':[prop_measure('Risk','Eligible Series')]},'Eligible risk series (43)')
 visual(p,'high','cardVisual',425,45,350,140,{'Data':[prop_measure('Risk','Highest Risk')]},'Maximum score (capped at 100)')
 visual(p,'bar','clusteredBarChart',45,218,1200,448,{'Category':[prop_col('Risk','series_label')],'Y':[prop_sum('Risk','risk_score',1)]},'Risk priority by commodity · Chittagong local fixed panel')
 p=pages[1][0]
 visual(p,'trend','lineChart',45,80,1190,590,{'Category':[prop_col('ChiliPrice','month')],'Y':[prop_sum('ChiliPrice','avg_price',1)]},'Green chili (retail, BDT/kg) · fixed markets · Jun 2025–May 2026')
 p=pages[2][0]
 visual(p,'mom','clusteredBarChart',50,75,595,580,{'Category':[prop_col('Changes','series_label')],'Y':[prop_sum('Changes','mom_pct',1)]},'May 2026 matched-market MoM (%)')
 visual(p,'baseline','clusteredBarChart',680,75,565,580,{'Category':[prop_col('Staples','commodity')],'Y':[prop_sum('Staples','change_pct',1)]},'Core staples versus 2022 (%) · matched markets')
 p=pages[3][0]
 visual(p,'series','clusteredColumnChart',50,70,580,580,{'Category':[prop_col('Coverage','month')],'Y':[prop_sum('Coverage','series',1)]},'Series coverage by month')
 visual(p,'markets','lineChart',665,70,580,580,{'Category':[prop_col('Coverage','month')],'Y':[prop_sum('Coverage','markets',1)]},'Markets covered by month')
 print('Generated unverified Power BI project:',BASE/(N+'.pbip'))

if __name__=='__main__':build()
