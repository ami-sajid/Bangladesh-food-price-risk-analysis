# Power BI Desktop — revised four-page report

Use outputs from a successful run. The supplied exports are real-data results, but this guide is a manual build: no PBIX execution is claimed. Save your completed file as dashboards/Bangladesh_Food_Prices.pbix. Labels can vary slightly across Desktop releases.

## Import each CSV separately
1. Open Power BI Desktop → Blank report → **Home → Get data → Text/CSV**.
2. Select the first file below from `outputs/tables/`, then **Transform Data**. Rename the query in Query Settings to the listed table name.
3. For subsequent files, in Power Query choose **Home → New Source → Text/CSV**. Do not combine the folder into one table: the exports have different grains.
4. Set types with the icon beside each column. All IDs/counts are Whole number; all prices, CV, percentages and scores Decimal number; month fields Date; labels Text. Keep nulls null.
5. **Home → Close & Apply** after adding the following tables.

| CSV | Table name | Grain and key fields |
|---|---|---|
| dim_commodity.csv | Series | One commodity-unit-price-type series; series_id unique |
| dim_market.csv | Market | One market identity; market_id unique |
| dim_date.csv | Month | One calendar month; month_id unique; month Date |
| 02_monthly_trends.csv | Monthly | One market_id + series_id + month; avg_price is same-market price |
| 04_changes.csv | Changes | One series_id + month; matched endpoints across eligible markets |
| 06_division_comparison.csv | Regional | One series_id + division at comparison month |
| 11_risk_score.csv | Risk | One series_id at comparison month, including ineligible statuses |
| risk_fixed_panel_monthly.csv | RiskMonthly | One eligible series + month from the fixed risk panel |
| risk_panel_members.csv | PanelMembers | One eligible series + member market |
| analysis_metadata.csv | Run | One row with source horizon, comparison month and selection rule |

Optional tables: `09_rolling_average.csv` as Rolling (market/series/month); `07_seasonality.csv` as Seasonality (series/calendar-month number); `analysis_month_selection.csv` as Coverage (candidate month); `12_outlier_sensitivity.csv` as Sensitivity (series snapshot).

## Relationships — build them deliberately
1. Select Model view. Delete any automatically created links between fact/summary tables.
2. **Modeling → Manage relationships → New**. Choose the fields below. Set cardinality **One to many**, cross-filter **Single**, relationship active. Dimensions filter summaries, never the reverse.

| One side | Many side |
|---|---|
| Series[series_id] | Monthly[series_id] |
| Series[series_id] | Changes[series_id] |
| Series[series_id] | Regional[series_id] |
| Series[series_id] | Risk[series_id] |
| Series[series_id] | RiskMonthly[series_id] |
| Series[series_id] | PanelMembers[series_id] |
| Market[market_id] | Monthly[market_id] |
| Market[market_id] | PanelMembers[market_id] |
| Month[month_id] | Monthly[month_id] |
| Month[month_id] | Changes[month_id] |

If Risk auto-detects one-to-one, change the summary side to many to keep single-direction filtering. Leave Run disconnected. RiskMonthly, Risk, Regional and PanelMembers deliberately have no historical-date relationship: they describe the fixed snapshot/window. Regional contains only the comparison month.

For optional Rolling, connect Series, Market and Month (Month[month] → Rolling[month]). For Seasonality connect Series only. For Sensitivity connect Series only. Coverage stays disconnected. Do not connect PanelMembers directly to Risk: a market slicer must not pretend to recompute a fixed-panel score.

3. Data view → select Series → **New column**:
```dax
Series Label = Series[commodity] & " | " & Series[unit] & " | " & Series[pricetype]
```
4. Select Market → New column:
```dax
Market Label = Market[division] & " | " & Market[district] & " | " & Market[market]
```
5. Set Month[month] display format `MMM yyyy`. This is a monthly calendar, not a daily Date table. Use the field itself rather than the automatic date hierarchy. The SQL already calculated calendar-correct YoY.

## Measures — paste one at a time
Right-click Monthly → **New measure**, paste a formula, press Enter. Measures can live together in Monthly even when they refer to another table.

```dax
Average Price =
IF(
    HASONEVALUE(Series[series_id]) && HASONEVALUE(Market[market_id]),
    AVERAGE(Monthly[avg_price])
)
```
This is one market's average monthly price over the selected dates. It intentionally returns blank for multiple markets or incompatible series.

```dax
Matched Current Price =
IF(
    HASONEVALUE(Series[series_id]) && HASONEVALUE('Month'[month_id]),
    MAX(Changes[mom_current_price])
)
```
This is the current mean across the exact markets used for MoM, not the same-market Average Price measure.

```dax
MoM % =
IF(
    HASONEVALUE(Series[series_id]) && HASONEVALUE('Month'[month_id]),
    DIVIDE(MAX(Changes[mom_pct]), 100)
)
```
```dax
YoY % =
IF(
    HASONEVALUE(Series[series_id]) && HASONEVALUE('Month'[month_id]),
    DIVIDE(MAX(Changes[yoy_pct]), 100)
)
```
Format these as Percentage, 1 decimal. CSV percentages use 10 to mean 10%; do not display them as 1000%. MoM and YoY can have different matched panels, so show their counts separately.

```dax
MoM Matched Markets =
IF(HASONEVALUE(Series[series_id]) && HASONEVALUE('Month'[month_id]), MAX(Changes[mom_markets]))
```
```dax
YoY Matched Markets =
IF(HASONEVALUE(Series[series_id]) && HASONEVALUE('Month'[month_id]), MAX(Changes[yoy_markets]))
```
```dax
Volatility CV =
VAR Points = FILTER(RiskMonthly, NOT ISBLANK(RiskMonthly[avg_price]))
RETURN IF(
    HASONEVALUE(Series[series_id]) && COUNTROWS(Points) = 12,
    DIVIDE(STDEVX.P(Points, RiskMonthly[avg_price]), AVERAGEX(Points, RiskMonthly[avg_price]))
)
```
Format CV as Percentage. It uses the exact fixed twelve-month panel, independent of historical-date slicers. This agrees with query 03 and Risk[cv].

```dax
Risk Score = IF(HASONEVALUE(Series[series_id]), MAX(Risk[risk_score]))
```
Format score as Number, one decimal, not Percent. Use this exported score in production because it tracks config.py parameters. For learning, the default formula is:

```dax
Risk Score Recalculated =
VAR CV = MAX(Risk[cv])
VAR ChangeFraction = DIVIDE(MAX(Risk[mom_pct]), 100)
RETURN IF(
    HASONEVALUE(Series[series_id]) && NOT ISBLANK(MAX(Risk[risk_score])),
    100 * (0.60 * MIN(DIVIDE(CV, 0.30), 1)
         + 0.40 * MIN(MAX(DIVIDE(ChangeFraction, 0.20), 0), 1))
)
```
Update 0.60, 0.30 and 0.20 if you change the corresponding config values. Leave ineligible scores blank.

```dax
Eligible Series = COUNTROWS(FILTER(Risk, NOT ISBLANK(Risk[risk_score])) )
```
```dax
Regional Price =
IF(HASONEVALUE(Series[series_id]) && HASONEVALUE(Regional[division]), MAX(Regional[avg_price]))
```
```dax
Comparison Month = FORMAT(MAX(Run[analysis_month]), "MMM yyyy")
```
```dax
Latest Source Month = FORMAT(MAX(Run[latest_source_month]), "MMM yyyy")
```
```dax
Panel Geography = CONCATENATEX(VALUES(PanelMembers[division]), PanelMembers[division], ", ")
```
Use a card or text table for Panel Geography. Copying a “Bangladesh-wide” title onto a concentrated panel would be misleading.

## Four pages, with exact fields
Click **+** beneath the canvas, double-click the tab to rename. For each page click blank canvas → **Format page → Canvas settings → 16:9**. Add visuals from Visualizations and drag fields into the named wells. Slicers: Format visual → Slicer settings → dropdown, Single select On where required. Use Series Label from the dimension.

| Page | Position | Visual and fields | Important settings |
|---|---|---|---|
| Overview | top 15% | Title, Comparison Month card, Latest Source Month card; Series Label and Month[month] dropdowns | Single-select series/month; initially choose comparison month |
| Overview | next 20% | Cards Matched Current Price, MoM %, YoY %, MoM Matched Markets, YoY Matched Markets | Caption “matched endpoint means”; no Market slicer here |
| Overview | lower left | Line: X Month[month], Y MoM % and YoY % | Edit interactions: month dropdown → None for this line so history remains visible; series still filters |
| Overview | lower right | Table Changes[month], mom_markets, yoy_markets, mom_flag_transitions, yoy_flag_transitions | Show counts as Max for each month; explain source flag changes |
| Commodity Trends | top | Series Label + Market Label single-select; Month[month] Between date slicer | Choose a market actually present for the series; empty combinations stay empty |
| Commodity Trends | middle 65% | Line: X Month[month], Y Average Price | Optional second line using Rolling[rolling_12m] as Average; same series/market selection |
| Commodity Trends | bottom | Table Monthly[month], avg_price, aggregate_rows, mixed_rows, flagged, scope | One market only; missing months are not zeros; pre-2024 rows exist only for eligible core staples |
| Regional Comparison | top | Comparison Month card + Series Label single-select | No historical date or Market slicer; this is a snapshot |
| Regional Comparison | left 60% | Horizontal bar: Y Regional[division], X Regional Price | Descending price, title includes selected unit/type |
| Regional Comparison | right 40% | Table division, avg_price, markets, national_price_ratio, aggregate_rows | No national cheapest-food-basket claim; markets are observed counts |
| Risk Ranking | top | Comparison Month card, Eligible Series card, Panel Geography card; Series[pricetype] dropdown | No date or Market slicer; title says “complete-panel risk, 2024 onward history” |
| Risk Ranking | left 55% | Bar: Y Series Label, X Risk Score | Filter Risk Score is not blank; Top N 10 by Risk Score; axis 0–100; disclose ties |
| Risk Ranking | upper right | Table Series Label, Risk Score, Volatility CV, Risk[mom_pct], market_count, available_markets, status | Score does not represent all markets; label raw mom_pct “MoM (%)” |
| Risk Ranking | lower right | Table PanelMembers[commodity], unit, pricetype, division, district, market | Exposes included geography; use a series selector to inspect one panel if desired |

Do not synchronize the Commodity Trends market slicer onto Risk Ranking. Do not synchronize Overview's month dropdown onto snapshot pages. National/matched endpoint changes and one-market trends have different scopes: use explicit titles. A card that averages different commodity units must remain blank.

Style: light background #F7F9FC, navy #18324B text, teal #147D92 price series, amber #DF8E32 caveats. Titles 18–24 pt, labels at least 11 pt. Add footer “WFP CSV | nominal BDT | source flags retained | scope shown per panel”. No 3D charts or unexplained red/green performance labels.

## Reconcile, refresh and share
1. Pick one series/month: verify MoM/YoY values AND counts against 04_changes.csv.
2. Pick one market: verify a trend point against 02_monthly_trends.csv. It need not equal a matched-panel mean.
3. Match Risk Score, CV and membership to 11_risk_score.csv, risk_fixed_panel_monthly.csv and risk_panel_members.csv. Check ties and blanks.
4. Confirm both source horizon and comparison month appear. Check that the risk title states the actual geography.
5. **Home → Refresh** after rerunning Python. If the folder moves: **File → Options and settings → Data source settings → Change Source**. Save your PBIX.
6. Export actual screenshots/PDF only after building and checking the report. Power BI online publication depends on your account and administrator settings; a PBIX alone is not a public link. The Looker guide provides a public-link workflow.

Official references:
- https://learn.microsoft.com/en-us/power-bi/desktop-create-and-manage-relationships
- https://learn.microsoft.com/en-us/dax/stdevx-p-function-dax
