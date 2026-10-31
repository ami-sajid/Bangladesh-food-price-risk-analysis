"""Generate reproducible case study HTML, publication PNGs and PDF from analysis CSV exports."""
from pathlib import Path
import base64, html
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

ROOT=Path(__file__).resolve().parents[1]; T=ROOT/'outputs/tables'; OUT=ROOT/'showcase';OUT.mkdir(exist_ok=True)
navy='#12233c';teal='#0fa89a';coral='#e9696e';slate='#5e7287';blue='#4e89db'

def read(name):return pd.read_csv(T/(name+'.csv'))
risk=read('11_risk_score'); ch=read('04_changes');st=read('05_since_2022'); cov=read('analysis_month_selection');meta=read('analysis_metadata').iloc[0]
r=risk[risk.risk_score.notna()].sort_values('risk_score',ascending=False)
month=meta['analysis_month']; move=ch[(ch.month==month)&(ch.mom_markets>=3)&ch.mom_pct.notna()].nlargest(8,'mom_pct')
stap=st[st.change_pct.notna()].sort_values('change_pct')
latest=meta['latest_source_month']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':slate,'text.color':navy,'axes.edgecolor':'#d9e1ea','xtick.color':slate,'ytick.color':slate,'figure.facecolor':'white','axes.facecolor':'white'})

def make_bar(df,labelcol,valcol,out,percent=False):
    vals=df[valcol].to_numpy(); names=df[labelcol].str.capitalize().str.replace(' (','\n(',regex=False)
    fig,ax=plt.subplots(figsize=(9.4,4.5)); y=range(len(df)); ax.barh(y, vals,color=[coral if x>=60 else teal for x in vals] if not percent else [coral if x>0 else teal for x in vals],height=.65)
    ax.set_yticks(list(y), names); ax.invert_yaxis();ax.grid(axis='x',color='#eff3f7');ax.set_axisbelow(True)
    ax.tick_params(axis='both',length=0);ax.set_xlim(min(0,min(vals)*1.2),max(vals)*1.20)
    for i,v in enumerate(vals):ax.text(v+max(vals)*.02,i,f'{v:+.1f}%' if percent else f'{v:.1f}',va='center',fontsize=9,color=navy,fontweight='bold')
    ax.set_xlabel('Matched-market MoM (%)' if percent else 'Price risk score (0–100)',labelpad=9)
    fig.tight_layout(pad=2.0);fig.savefig(OUT/out,dpi=180,bbox_inches='tight');plt.close(fig)

make_bar(r.head(10),'commodity','risk_score','risk_watchlist.png')
make_bar(move,'commodity','mom_pct','monthly_increases.png',True)
fig,ax=plt.subplots(figsize=(9.3,3.3)); clrs=[coral if x>0 else teal for x in stap.change_pct]; ax.barh(stap.commodity.str.capitalize(),stap.change_pct,color=clrs,height=.55);ax.axvline(0,color=slate,lw=.8);ax.invert_yaxis();ax.grid(axis='x',color='#eff3f7');ax.set_axisbelow(True);ax.tick_params(length=0);ax.set_xlabel('Change from matched 2022 market baselines (%)',labelpad=12)
for i,v in enumerate(stap.change_pct):ax.text(v+(0.6 if v>0 else -.6),i,f'{v:+.1f}%',va='center',ha='left' if v>0 else 'right',fontweight='bold',fontsize=9)
fig.tight_layout(pad=2);fig.savefig(OUT/'staples_vs_2022.png',dpi=180,bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(9.3,3.5));cov1=cov.tail(12);x=range(len(cov1)); ax.bar(x,cov1.series,color=blue,alpha=.8,label='Series observed');ax2=ax.twinx();ax2.plot(x,cov1.markets,color=teal,linewidth=2.3,marker='o',markersize=4,label='Markets observed'); ax.set_xticks(list(x),[pd.to_datetime(v).strftime('%b %y') for v in cov1.month],rotation=45);ax.tick_params(length=0);ax2.tick_params(length=0);ax.set_ylabel('Food series',color=blue);ax2.set_ylabel('Markets',color=teal)
ax.grid(axis='y',color='#eff3f7');ax.set_axisbelow(True); fig.tight_layout(pad=2);fig.savefig(OUT/'coverage_timeline.png',dpi=180,bbox_inches='tight');plt.close(fig)

styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name='KickerX',fontName='Helvetica-Bold',fontSize=9,leading=13,textColor=colors.HexColor(teal),spaceAfter=12));styles.add(ParagraphStyle(name='HeroX',fontName='Helvetica-Bold',fontSize=29,leading=35,textColor=colors.HexColor(navy),spaceAfter=15));styles.add(ParagraphStyle(name='TitleX',fontName='Helvetica-Bold',fontSize=19,leading=23,textColor=colors.HexColor(navy),spaceAfter=11));styles.add(ParagraphStyle(name='SecX',fontName='Helvetica-Bold',fontSize=11.5,leading=16,textColor=colors.HexColor(navy),spaceBefore=13,spaceAfter=6));styles.add(ParagraphStyle(name='BodyX',fontName='Helvetica',fontSize=9.5,leading=15,textColor=colors.HexColor('#405469'),spaceAfter=9));styles.add(ParagraphStyle(name='SmallX',fontName='Helvetica',fontSize=8,leading=12,textColor=colors.HexColor('#53667a'),spaceAfter=7));styles.add(ParagraphStyle(name='WhiteX',fontName='Helvetica-Bold',fontSize=11,leading=16,textColor=colors.white));styles.add(ParagraphStyle(name='NumberX',fontName='Helvetica-Bold',fontSize=21,leading=26,textColor=colors.HexColor(navy)));styles.add(ParagraphStyle(name='TableX',fontName='Helvetica',fontSize=8,leading=12,textColor=colors.HexColor(navy)))
P=lambda text,style='BodyX':Paragraph(text,styles[style])

def foot(canvas,doc):
    canvas.saveState();w,h=A4
    canvas.setFillColor(colors.HexColor('#edf2f6'));canvas.rect(0,h-12*mm,w,12*mm,fill=1,stroke=0)
    canvas.setFillColor(colors.HexColor(navy));canvas.setFont('Helvetica-Bold',7.5);canvas.drawString(19*mm,h-8.2*mm,'MARKETLENS   /   FOOD PRICE INTELLIGENCE')
    canvas.setStrokeColor(colors.HexColor('#e1e8f0'));canvas.line(19*mm,17*mm,w-19*mm,17*mm)
    canvas.setFillColor(colors.HexColor(slate));canvas.setFont('Helvetica',7);canvas.drawString(19*mm,11.5*mm,'Portfolio case study  |  WFP / HDX source data  |  Not official CPI')
    canvas.drawRightString(w-19*mm,11.5*mm,f'{doc.page:02d}')
    canvas.restoreState()

doc=SimpleDocTemplate(str(OUT/'Food_Price_Analysis_Report.pdf'), pagesize=A4, topMargin=25*mm,bottomMargin=23*mm,leftMargin=19*mm,rightMargin=19*mm, title='Bangladesh Food Price & Inflation Risk Analysis — Case Study',author='Portfolio Analytics')
story=[]

def image(name,maxh=75):
    from PIL import Image as PIL
    p=OUT/name;w,h=PIL.open(p).size;ratio=min((172*mm)/w,(maxh*mm)/h);return Image(str(p),width=w*ratio,height=h*ratio)

def page_title(k,t,desc):story.extend([P(k,'KickerX'),P(t,'TitleX'),P(desc)])

story += [Spacer(1,10*mm),P('DATA ANALYTICS  /  BANGLADESH','KickerX'),P('Food price intelligence<br/>&amp; risk analysis','HeroX'),P('From raw market observations to a decision-focused commodity monitoring system.', 'BodyX'),Spacer(1,8*mm)]
rows=[[P('34,490','NumberX'),P('43 / 66','NumberX'),P('May 2026','NumberX')],[P('Clean records','SmallX'),P('Eligible risk series','SmallX'),P('Comparison month','SmallX')]]
tb=Table(rows,colWidths=[57*mm]*3,rowHeights=[14*mm,11*mm]);tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#eff6f8')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),10),('LINEBELOW',(0,-1),(-1,-1),0.5,colors.HexColor('#d8e7ec'))]));story+=[tb,Spacer(1,9*mm),P('The business problem','SecX'),P('A food retailer or distributor needs early signals about unusual prices and where to recheck suppliers. Raw market data mixes different products, market locations, measurement units and time periods, so naive averages can mislead decision-makers.'),P('What I built','SecX'),P('A reproducible Python &rarr; SQL pipeline with quality checks, matched-market monthly comparisons, fixed-panel risk scoring, an interactive dashboard and an independently validated results layer.'),P('Critical interpretation note','SecX'),P('<b>The 12-month risk watchlist represents four markets in the Chittagong area.</b> Its ranks are local warnings, not national commodity rankings. September 2026 is the latest source month; May 2026 is the last month meeting the pipeline&#39;s comparison coverage rule.'),Spacer(1,5*mm),P('SOURCE: WFP Bangladesh food prices via the Humanitarian Data Exchange (HDX). This is nominal BDT price analysis, not CPI or a causal impact assessment.','SmallX')]
story += [PageBreak()]
page_title('01  /  SIGNAL DETECTION','Where prices need attention','Each score is computed for one commodity, unit and price type, using twelve consecutive months with identical panel markets.')
story += [image('risk_watchlist.png',94),P('Top-ranked carrots, green chili and red tomatoes reach the 100-point cap; equal capped values do not imply equal risk. Each of the top-ranking series requires careful review of panel sizes, source flags, and local applicability.','SmallX'),P('Latest matched-market monthly increases','SecX'),image('monthly_increases.png',78),P('May 2026 observed sharp matched-market increases for carrots, milk and red tomatoes. Results reflect eligible same-market comparisons, not a national inflation index.','SmallX')]
story += [PageBreak()]
page_title('02  /  STAPLE CONTEXT','Longer-term prices and data coverage','Matched markets reduce composition bias; they do not remove measurement differences between source aggregates and direct observations.')
story += [image('staples_vs_2022.png',76),P('Compared with matched market-level 2022 baselines, palm oil was approximately +18.4%, wheat flour +8.7%, coarse rice +5.3% and masur lentils -5.3% at the May 2026 snapshot. Baselines use available months and include source aggregate flags.','SmallX'),P('Why the reference month is not the latest source month','SecX'),image('coverage_timeline.png',75),P('The pipeline selects the latest month reaching at least half the trailing-year maximum for both food-series counts and market counts. Later months are retained in source coverage and trends but not used for the ranked snapshot. This is a documented heuristic, not proof that any month is complete.','SmallX')]
story += [PageBreak()]
page_title('03  /  REPRODUCIBLE PIPELINE','From data to a decision','An analytical workflow designed to make the output auditable, explainable, and repeatable.')
for hdr,txt in [
 ('01  Ingest and profile','Download the original WFP CSV manually. Profile columns, date coverage, unit labels, price types, missing values and measurement flags. Preserve the original source unchanged.'),
 ('02  Clean and validate','Standardize fields, check dates, prices and currencies, remove exact duplicates, quarantine invalid records, and keep suspicious outliers with flags rather than silently removing them.'),
 ('03  Build the SQL model','Load fact prices and commodity, market and calendar dimensions into SQLite or PostgreSQL. Execute 12 SQL analyses and export the explicit comparison cohorts.'),
 ('04  Calculate careful comparisons','Use endpoint-matched markets for MoM/YoY. Use identical market membership for all 12 months of the risk panel. Never mix unlike measurement units or wholesale and retail.'),
 ('05  Verify and present','Run automated tests plus independent calculations, then generate findings, static figures, an interactive offline dashboard and this case-study report.')]:
 story += [P(hdr,'SecX'),P(txt)]
story += [Spacer(1,5*mm),P('Data quality is part of the finding','SecX'),P('34,491 raw records become 34,490 cleaned observations; 1 record is quarantined. Of 66 candidate food-risk series, 43 qualify for the strict panel. Excluded series are <b>unscored</b>, not low risk.')]
story += [PageBreak()]
page_title('04  /  ACTIONS & LIMITS','Recommended business decisions','The dashboard supports prioritized investigation; it does not substitute for procurement verification or a forecasting model.')
for hdr,txt in [
 ('Priority 1 — check local suppliers','For high-scoring products, compare current quotations across the same local markets. Reconfirm product grade, season, transportation cost and unit before changing purchasing terms.'),
 ('Priority 2 — monitor before committing','Follow matched-market monthly increases and price dispersion. For produce with sharp spikes, schedule earlier checks; do not automatically bulk-buy from a capped risk score.'),
 ('Priority 3 — broaden market evidence','Before making national distribution decisions, add broader geographic coverage and verify measurement consistency across WFP releases.'),
 ('Priority 4 — operationalize refresh','Run the Windows batch file when a new WFP CSV is available. Revalidate records, update the analysis month selection, rerun comparisons and regenerate dashboard files.')]:
 story += [P(hdr,'SecX'),P(txt)]
story += [P('What this report does not claim','SecX'),P('No official national inflation series, no validated price forecast, no causal proof, no verified procurement savings, no assumption that ineligible markets are safe, and no claim that the dashboard&#39;s four-market risk score describes the whole country.')]
story += [P('Project stack','SecX'),P('<b>Python / pandas</b> for profiling and cleaning &nbsp; &bull; &nbsp; <b>SQL</b> for monthly comparisons and ranking &nbsp; &bull; &nbsp; <b>SQLite / PostgreSQL</b> for reproducible storage &nbsp; &bull; &nbsp; <b>Plotly</b> for interactive reporting &nbsp; &bull; &nbsp; <b>Power BI</b> build assets for Windows Desktop.')]
story += [P('Source and reproducibility','SecX'),P('Source: World Food Programme (WFP), Bangladesh Food Prices, distributed through HDX. <link href="https://data.humdata.org/dataset/wfp-food-prices-for-bangladesh" color="#0fa89a">Open source dataset listing</link>. License for the precise downloaded release must be verified before redistributing the source dataset. Code, queries and validation controls are documented in the project repository.'),P('This case study is an independent portfolio exercise and is not affiliated with or endorsed by WFP or HDX.','SmallX')]
doc.build(story,onFirstPage=foot,onLaterPages=foot)

# Case study HTML: original narrative inspired by professional portfolio layout (not copying referenced repository).
seccards=''.join(f'<article class="step"><span>{i:02}</span><div><h3>{h}</h3><p>{t}</p></div></article>' for i,(h,t) in enumerate([
('Ingest & profile','Load the user-downloaded WFP release, inspect units, source flags, history and completeness.'),('Clean & validate','Repair labels, quarantine invalid dates, retain possible real-world outliers with flags.'),('Model & analyze','Build SQLite/PostgreSQL star tables, matched-market MoM/YoY analyses and 12-month fixed market risk scores.'),('Test & publish','Recalculate indicators independently and build the dashboard, figures, case study and report.')],1))
HTML=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MarketLens — Bangladesh Food Price Case Study</title><style>
:root{{--navy:#101e34;--ink:#1b2b43;--teal:#12b6a5;--muted:#6c8198;--bg:#f5f8fc}}*{{box-sizing:border-box}}body{{margin:0;font-family:Inter,'Segoe UI',Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.7}}
nav{{display:flex;justify-content:space-between;align-items:center;padding:20px max(5%,calc((100% - 1160px)/2));background:#0f2038;color:#fff;gap:20px}}nav b{{letter-spacing:-.5px}}nav a{{color:#dceef5;text-decoration:none;font-size:12px;margin-left:18px}}a:hover{{text-decoration:underline}}
.hero{{background:linear-gradient(125deg,#10233f,#173d55);color:white;padding:80px max(5%,calc((100% - 1160px)/2)) 75px}}.wrap{{max-width:1160px;margin:auto;padding:0 30px}}.label{{color:#31d4bf;letter-spacing:2.5px;font-size:11px;font-weight:900}}h1{{font-size:clamp(38px,6vw,67px);line-height:1.08;letter-spacing:-2.2px;max-width:870px;margin:22px 0}}h2{{font-size:32px;letter-spacing:-.8px;line-height:1.15}}h3{{margin:0 0 9px;font-size:18px}}.hero p{{color:#bbcedb;max-width:735px;font-size:17px}}
.actions{{display:flex;gap:12px;flex-wrap:wrap;margin-top:30px}}.btn{{background:#22c7b2;color:#08293b;text-decoration:none;padding:12px 22px;border-radius:8px;font-weight:850;font-size:12px}}.btn.sec{{background:transparent;border:1px solid #4c7182;color:white}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:-35px;position:relative}}.stat{{background:white;border:1px solid #e5edf4;box-shadow:0 10px 25px #091d2e0e;padding:26px;border-radius:11px}}.stat strong{{font-size:28px;color:#10223c;display:block}}.stat small{{text-transform:uppercase;letter-spacing:.8px;font-size:10px;color:var(--muted);font-weight:800}}
section{{padding:65px 0 15px}}section p{{color:#536983}}.lead{{max-width:780px}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:25px}}.panel{{background:white;border:1px solid #e4eaf0;border-radius:15px;padding:26px;box-shadow:0 8px 26px #092a3b08}}.panel img{{display:block;width:100%;height:auto;border-radius:5px}}.panel .meta{{font-size:11px;color:#8394a8;letter-spacing:.8px;font-weight:850;text-transform:uppercase}}.callout{{background:#e7f4f2;border-left:4px solid #13ab9b;padding:20px 25px;border-radius:7px;color:#385c66;margin:22px 0}}.warning{{background:#fff7e9;border-color:#e7ac51}}
.steps{{display:grid;grid-template-columns:1fr 1fr;gap:15px}}.step{{display:flex;gap:20px;border:1px solid #e5eaf1;background:white;padding:26px;border-radius:12px}}.step span{{color:#13ae9d;font-size:23px;font-weight:950}}.step p{{margin:0;font-size:13px}}.findings li{{margin-bottom:12px}}footer{{margin-top:90px;padding:30px; background:#101e34;color:#aec1d5;font-size:12px;text-align:center}}footer a{{color:#49d6c5}}@media(max-width:760px){{.stats,.two,.steps{{grid-template-columns:1fr}}.hero{{padding:50px 24px}}h1{{letter-spacing:-1px}}nav{{padding:17px}}nav a{{margin-left:7px}}.wrap{{padding:0 16px}}}}
</style></head><body><nav><b>↗ MARKET<span style="color:#33d5bd">LENS</span></b><div><a href="dashboards/interactive_dashboard.html">Dashboard</a><a href="showcase/Food_Price_Analysis_Report.pdf">PDF report</a><a href="README.md">README</a></div></nav>
<div class="hero"><div class="label">PORTFOLIO CASE STUDY · PYTHON / SQL / BI</div><h1>Bangladesh Food Price &amp; Inflation Risk Analysis</h1><p>Turning 34,490 cleaned WFP market observations into explainable price monitoring, commodity signals, and procurement questions worth investigating.</p><div class="actions"><a class="btn" href="dashboards/interactive_dashboard.html">Explore interactive dashboard ↗</a><a class="btn sec" href="showcase/Food_Price_Analysis_Report.pdf">Read analytical report ↗</a></div></div>
<div class="wrap"><div class="stats"><div class="stat"><strong>34,490</strong><small>Clean observations</small></div><div class="stat"><strong>43 / 66</strong><small>Eligible risk series</small></div><div class="stat"><strong>4</strong><small>Risk panel markets</small></div><div class="stat"><strong>May 2026</strong><small>Comparison month</small></div></div>
<section><div class="label">01 / PROBLEM & SOLUTION</div><h2>From market records to clearer decisions</h2><p class="lead">Retail buyers need to know which commodities are moving unusually, without confusing measurement units, regions or time periods. This project implements an auditable data pipeline and monitoring dashboard that separates descriptive price signals from business claims.</p><div class="callout warning"><b>Scope safeguard:</b> The latest source observation is September 2026, but May 2026 is the last month meeting the project's comparison-coverage heuristic. The strict risk rankings describe four markets in the Chittagong area—not Bangladesh as a whole.</div></section>
<section><div class="label">02 / FINDINGS</div><h2>What the supplied data shows</h2><div class="two"><div class="panel"><div class="meta">Local fixed-panel risk</div><h3>Commodity risk watchlist</h3><img src="showcase/risk_watchlist.png" alt="Local food commodity risk watchlist chart"><p>Carrots, green chili and red tomatoes reach the 100-point cap. Equal scores may be caused by the scoring cap; the score is not a forecast or probability.</p></div><div class="panel"><div class="meta">Matched markets · May 2026</div><h3>Short-term price increases</h3><img src="showcase/monthly_increases.png" alt="Matched market monthly price increase chart"><p>Carrots, milk and red tomatoes have the strongest eligible month-on-month increases in the comparison snapshot.</p></div><div class="panel"><div class="meta">Longer-term context</div><h3>Core staples versus 2022</h3><img src="showcase/staples_vs_2022.png" alt="Staples compared with matched market price baseline"><p>Palm oil: +18.4%; wheat flour: +8.7%; coarse rice: +5.3%; masur lentils: -5.3%. The 2022 baselines include aggregate source flags.</p></div><div class="panel"><div class="meta">Data completeness matters</div><h3>Markets and series observed</h3><img src="showcase/coverage_timeline.png" alt="Coverage series and markets by month"><p>The pipeline's coverage heuristic favors May 2026 over later months. Unavailable measurements are not silently filled or treated as stable prices.</p></div></div></section>
<section><div class="label">03 / ENGINEERING</div><h2>How the pipeline works</h2><div class="steps">{seccards}</div><div class="callout"><b>Design principle:</b> compare the same market IDs at both endpoints; for the risk score compare the identical panel in all twelve months. Keep BDT/kg, BDT/litre and BDT/piece separate.</div></section>
<section><div class="label">04 / BUSINESS RESPONSE</div><h2>Where the insights help</h2><div class="two"><div class="panel"><h3>Supplier quote reviews</h3><p>Start with the high-scoring local commodities. Confirm pricing changes against quotes, quality, transport costs and seasonality before ordering.</p></div><div class="panel"><h3>Purchasing cadence</h3><p>Watch repeated matched-market increases and volatility. More frequent checks may be justified, but this dataset cannot verify savings or predict future prices.</p></div><div class="panel"><h3>Evidence quality</h3><p>Disclose geographic sample sizes, actual versus aggregate source flags, and missing comparisons before making operational recommendations.</p></div><div class="panel"><h3>Refresh discipline</h3><p>Download a fresh release, run the pipeline, rerun validation, and rebuild the dashboard with the newest eligible comparison month.</p></div></div></section>
<section><div class="label">05 / SOURCE &amp; LIMITATIONS</div><h2>Responsible interpretation</h2><p>This independent portfolio analysis uses original World Food Programme Bangladesh food-price observations obtained from the Humanitarian Data Exchange. It is not official CPI, a national inflation forecast, or a measured business improvement. Redistribution of source materials depends on verifying the license for the exact WFP/HDX release.</p><div class="actions"><a class="btn" href="dashboards/interactive_dashboard.html">Open dashboard</a><a class="btn" href="showcase/Food_Price_Analysis_Report.pdf">Download report</a></div></section></div>
<footer>Bangladesh Food Price &amp; Inflation Risk Analysis · Independent portfolio project · <a href="https://data.humdata.org/dataset/wfp-food-prices-for-bangladesh">WFP source via HDX</a> · Not endorsed by WFP or HDX</footer></body></html>'''
for figure in ['risk_watchlist.png','monthly_increases.png','staples_vs_2022.png','coverage_timeline.png']:
    uri='data:image/png;base64,' + base64.b64encode((OUT/figure).read_bytes()).decode('ascii')
    HTML=HTML.replace('src="showcase/'+figure+'"','src="'+uri+'"')
(ROOT/'case-study.html').write_text(HTML,encoding='utf-8')
print('Case study and report created:',OUT/'Food_Price_Analysis_Report.pdf')

if __name__=='__main__': pass
