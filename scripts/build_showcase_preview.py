"""Render a static illustration of the overview using real analysis charts (not a browser screenshot)."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dashboards'/'dashboard_showcase_preview.png'
W,H=1600,935
im=Image.new('RGB',(W,H),'#f4f7fb');d=ImageDraw.Draw(im)
regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
f=lambda s,b=False:ImageFont.truetype(bold if b else regular,s)
def rect(x,y,w,h,fill,r=13):d.rounded_rectangle((x,y,x+w,y+h),r,fill=fill)
def tx(x,y,t,size,color,b=False):d.text((x,y),t,font=f(size,b),fill=color)
# Sidebar
d.rectangle((0,0,236,H),fill='#101b31');rect(23,29,38,38,'#11c7b7',10);tx(31,30,'↗',22,'#102c39',True);tx(76,33,'MARKETLENS',18,'#ffffff',True);tx(75,57,'BANGLADESH / WFP',10,'#9caed0')
tx(28,146,'ANALYTICS',11,'#8298b8',True)
for y,label in [(177,'▣   Executive overview'),(238,'◈   Risk watchlist'),(299,'⌁   Commodity explorer'),(360,'◷   Coverage & method')]:
 if y==177:rect(16,y-4,204,49,'#273d57',8)
 tx(28,y+7,label,13,'#ffffff' if y==177 else '#aebbd0',y==177)
d.line((23,845,210,845),fill='#2c3b52',width=2);tx(24,863,'●  Validated snapshot',11,'#66d4b9');tx(24,890,'WFP / HDX · Nominal BDT',10,'#95abc5')
# Header
tx(276,33,'FOOD PRICE INTELLIGENCE / PORTFOLIO ANALYTICS',12,'#06a59a',True);tx(276,63,'Executive overview',34,'#15243e',True);tx(276,110,'A decision-focused monitoring view of commodity price movements and source coverage.',13,'#6a7890')
rect(1387,49,172,42,'#ffffff',9);tx(1403,61,'MAY 2026 · DATA',12,'#425573',True)
rect(276,151,1275,64,'#fff7e8',11);tx(292,167,'ⓘ  Scope notice',14,'#825f2c',True);tx(292,188,'Risk panels: 4 markets in Chittagong. Latest source: Sep 2026. May is the last coverage-eligible month.',12,'#896d3f')
metrics=[('CLEAN OBSERVATIONS','34,490','One record quarantined','#0fadc3'),('ELIGIBLE RISK SERIES','43 / 66','Strict fixed market panel','#806ce8'),('HIGHEST RISK SCORE','100.0 / 100','Capped monitoring index','#07a98d'),('LATEST SOURCE MONTH','Sep 2026','Coverage varies month to month','#e9ad48')]
for i,(l,n,s,c) in enumerate(metrics):
 x=276+i*322;rect(x,231,308,133,'#ffffff');d.rounded_rectangle((x,231,x+4,364),3,fill=c);tx(x+18,247,l,10,'#7789a0',True);tx(x+18,272,n,29,'#13233c',True);tx(x+18,321,s,12,'#788da3')
# Plot images from actual panel charts
for j,(fn,title,desc) in enumerate([('risk_watchlist.png','Top eligible price-risk signals','12-month fixed panel / one series at a time'),('monthly_increases.png','Matched-market monthly increases','May 2026 / same-market endpoints')]):
 x=276+j*643; rect(x,382,627,506,'#ffffff',13);tx(x+24,401,title,16,'#1d2f46',True);tx(x+24,429,desc,12,'#75869e')
 src=Image.open(ROOT/'showcase'/fn).convert('RGB');src.thumbnail((590,420))
 # fit on white
 box=Image.new('RGB',(590,420),'white');box.paste(src,((590-src.width)//2,(420-src.height)//2));im.paste(box,(x+18,455))
im.save(OUT,optimize=True)
print('Wrote',OUT)
