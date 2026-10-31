# Looker Studio — revised four-page dashboard through Google Sheets

Build this from successful real-data exports. This is a manual guide, not a pre-created online report. Google documentation may use Data Studio naming. Do not publish the risk panel as nationally representative: show its member markets and geography.

## Import the data into Sheets
1. Google Drive → **New → Google Sheets → Blank spreadsheet**. Name it `Bangladesh Food Price Analysis`.
2. **File → Import → Upload → Browse**. Select a CSV from outputs/tables. Import location **Insert new sheet(s)**, separator **Detect automatically** → Import data.
3. Rename each imported worksheet as below. Keep one header row, no notes/totals inside the data range. Keep blanks blank.

| File | Worksheet | Meaning |
|---|---|---|
| 02_monthly_trends.csv | Monthly | One market/series/month, not a national mean |
| 04_changes.csv | Changes | Endpoint-matched market comparisons |
| 06_division_comparison.csv | Regional | One shared comparison-month snapshot |
| 11_risk_score.csv | Risk | Fixed-panel score and eligibility |
| risk_panel_members.csv | Members | Exact markets represented by scores |
| analysis_metadata.csv | Run | Latest source month and comparison month |
| analysis_month_selection.csv | Coverage | Counts behind comparison-month selection |

Optional: 09_rolling_average.csv as Rolling, 07_seasonality.csv as Seasonality, 12_outlier_sensitivity.csv as Sensitivity. Each source is separate; do not join summaries or append snapshots to each other.

4. Format month/date columns with **Format → Number → Date**. Numeric prices, scores, CV and changes must remain numbers. If your account's Sheet capacity is exceeded, use a documented smaller period or the File Upload connector; never silently sample while claiming full coverage.

## Connect sources
1. Open https://lookerstudio.google.com/ → **Create → Data source → Google Sheets**.
2. Select the spreadsheet and worksheet Monthly. Use first row as headers → **Connect**.
3. Verify types: month Date, series_id/market_id numeric identifiers, prices and counts Number, labels Text. Name the source `Food Monthly`.
4. **Create report → Add to report**. Name the report after the project.
5. **Resource → Manage added data sources → Add a data source**. Repeat for each worksheet.
6. If using direct CSV instead: **Create → Data source → File Upload** where offered. One exported table per source. Some upload flows append files; remove or replace the prior full export to prevent doubled history.

## Calculated fields and aggregation
Edit each source → Add a field. Enter the name separately; paste only the formula body.

**Series Label**, on Monthly, Changes, Regional, Risk and Members:
```
CONCAT(commodity, " | ", unit, " | ", pricetype)
```
**Market Label**, on Monthly:
```
CONCAT(division, " | ", market)
```
**MoM Fraction**, on Changes:
```
mom_pct / 100
```
**YoY Fraction**, on Changes:
```
yoy_pct / 100
```
Set fractions to Percent. Source values 10 mean 10%, so division prevents a 1000% display. On Risk, cv is already a fraction: format Percent without dividing. risk_score is a Number, not a Percent.

Use Average for one-series/month prices and changes; Max for one-row snapshot scores and counts. Do not sum percentages, CV or risk scores. Do not average prices across units or selected markets for the long-run trend. Use exported CV and risk_score; they already use the exact eligible fixed panel.

Optional `Risk Recalculated` field on Risk, default parameters only:
```
CASE
 WHEN months_available = 12 THEN
  100 * (0.60 * CASE WHEN cv / 0.30 > 1 THEN 1 ELSE cv / 0.30 END
  + 0.40 * CASE WHEN mom_pct < 0 THEN 0 WHEN mom_pct / 20 > 1 THEN 1 ELSE mom_pct / 20 END)
 ELSE NULL
END
```
Change constants if config.py changes. Use the exported score in the displayed report to keep it authoritative.

## Controls must not silently mix data sources
Independent Google Sheets sources can have different internal field IDs even when their column names look the same. Do not assume one dropdown filters every source.

For each panel, create controls using that panel's source, Shift-select the controls and charts → **Arrange → Group**. Label their scope. Use single selections for Series Label and for Market Label on market trends. If your UI lacks single-selection enforcement, use an explicit chart filter for one chosen label. Price scorecards require a fixed single-series filter; tables retaining the series dimension are safer when viewers may clear controls.

Snapshot panels (Regional/Risk) contain one selected comparison month. Do not add a historical date control there. A Market control must not appear to recalculate Risk: the fixed panel is already selected by SQL. Members is an audit table, not a join that changes score calculations.

## Four pages and visual layout
Use **Page → New page**, rename in navigation. **Theme and layout → Layout → Canvas size**: widescreen. Light background #F7F9FC, navy text #18324B, teal #147D92 charts, amber #DF8E32 for coverage notes. Titles 18–24 pt, labels at least 11 pt. Add “Nominal BDT; source flags retained; geographic scope shown” to the footer.

| Page | Panel | Chart/control and fields |
|---|---|---|
| Overview | top | Title; Run source table showing latest_source_month, analysis_month and selection; clearly label source horizon vs comparison month |
| Overview | left 60%, Changes | Series Label and month dropdowns; table Series Label, month, mom_current_price, MoM Fraction, YoY Fraction, mom_markets, yoy_markets; select one month |
| Overview | right 40%, Coverage | Time series dimension month, metrics Max series and Max markets; notes explaining broad_coverage and selected month from Run |
| Commodity Trends | top, Monthly | Series Label AND Market Label single-choice controls, date range control; each price chart must select one market and series |
| Commodity Trends | middle, Monthly | Time series: month, Average avg_price; same-market price title and source unit; no totals across markets |
| Commodity Trends | bottom, Monthly | Table month, avg_price, aggregate_rows, mixed_rows, flagged, scope; explain gaps and pre-2024 core-staple restriction |
| Commodity Trends | optional separate panel, Changes | Its OWN series dropdown, line month/MoM Fraction/YoY Fraction; title explicitly says “matched-market changes”, independent of selected single market |
| Regional Comparison | top, Regional | Comparison date displayed; Series Label single-select; no historical date/market control |
| Regional Comparison | left 60%, Regional | Horizontal bar: division, Average avg_price; descending sort; selected unit/type in title |
| Regional Comparison | right 40%, Regional | Table division, avg_price, markets, national_price_ratio, aggregate_rows; observed-market snapshot, not an overall food-basket ranking |
| Risk Ranking | top | Comparison date from Run; explicit geography copied from computed FINDINGS.md; price-type control from Risk |
| Risk Ranking | left 55%, Risk | Bar Series Label, Max risk_score; filter risk_score Is not null; descending sort; 10 rows; axis 0–100; show capped-score ties |
| Risk Ranking | upper right, Risk | Table Series Label, score, cv, mom_pct, market_count, available_markets, status; include ineligible rows with blank scores |
| Risk Ranking | lower right, Members | Separate series control and table commodity/unit/pricetype/division/district/market; explains exact geographic scope |

For time series, configure missing data as line breaks where offered, never zero-fill or interpolation. For each visual: **Add a chart**, draw a rectangle, select the source, dimension and metrics in Setup; Style sets labels/decimals/colors. The Members dropdown filters only its table; it does not change the scores. If making source horizon/geography static text, update them after every rerun; the Run table itself refreshes automatically with its Sheet.

## Validate and refresh
1. In View mode check one change row and both matched-market counts against 04_changes.csv.
2. Check one trend point against 02_monthly_trends.csv using the same series and market. It need not match the endpoint-panel mean.
3. Check one risk score, panel count and market list against Risk and Members exports. Confirm blank is not presented as zero or low risk.
4. Test every panel's controls. Never assume a matching field name guarantees cross-source filtering.
5. After a pipeline rerun, replace data within the existing worksheet tabs, preserving headers and worksheet identity. Clear old trailing rows; do not append a complete history again. Refresh the report. Refresh source fields if headers changed. Update any manually written dates/geography.

## Make the public link
1. Click **Share → Manage access** (or Sharing settings). Set link/general access to **Anyone with the link** or the available public-view option. Choose **Viewer**, not Editor, and Save.
2. **Copy link**. Open it in an incognito/private window while signed out; confirm the charts load and filters work.
3. If blocked, check report sharing and source credentials. Owner credentials can display the public-source dataset you are authorized to share. Never put .env, credentials or private files in Sheets.
4. Workspace administrators may disable public access. If no option exists, use an allowed personal account for the public-data report or export a PDF/screenshot. Do not call the report public until the signed-out check succeeds.
5. Put the tested URL into README/CV placeholders only after finishing the dashboard. No live report or screenshot has been fabricated in this project package.

Official references:
- https://cloud.google.com/looker/docs/studio/connect-to-google-sheets
- https://cloud.google.com/looker/docs/studio/share-reports-with-viewers-and-editors
