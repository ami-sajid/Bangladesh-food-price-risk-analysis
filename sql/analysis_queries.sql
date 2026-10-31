-- name: 01_coverage
-- Business question: What evidence exists for each series?
-- How to read: Includes non-food for audit. Food analyses filter is_food=1.
SELECT c.series_id,c.commodity,c.unit,c.pricetype,c.category,c.is_food,
 MIN(d.month) AS first_month,MAX(d.month) AS last_month,COUNT(*) AS observations,
 COUNT(DISTINCT f.market_id) AS markets,COUNT(DISTINCT f.month_id) AS months,
 SUM(f.outlier_flag) AS flagged,
 SUM(CASE WHEN f.priceflag='aggregate' THEN 1 ELSE 0 END) AS aggregate_rows,
 SUM(CASE WHEN f.priceflag='actual,aggregate' THEN 1 ELSE 0 END) AS mixed_rows
FROM fact_prices f JOIN dim_commodity c ON c.series_id=f.series_id
JOIN dim_date d ON d.month_id=f.month_id
GROUP BY c.series_id,c.commodity,c.unit,c.pricetype,c.category,c.is_food
ORDER BY observations DESC;

-- name: 02_monthly_trends
-- Business question: What happened within the same market?
-- How to read: One market-series-month per row. Pre-2024 history is restricted to core staples with 60+ market observations. Select ONE market and series.
WITH history AS (SELECT series_id,market_id,COUNT(*) AS months FROM v_market_month GROUP BY series_id,market_id)
SELECT c.series_id,c.commodity,c.unit,c.pricetype,m.market_id,k.market,k.division,
 d.month,d.month_id,m.price AS avg_price,m.observations,m.flagged,m.aggregate_rows,m.mixed_rows,
 h.months AS history_months,
 CASE WHEN c.is_staple=1 AND h.months>=s.min_long_months THEN 'core long history' ELSE '2024 onward' END AS scope
FROM v_market_month m JOIN dim_commodity c ON c.series_id=m.series_id
JOIN dim_market k ON k.market_id=m.market_id JOIN dim_date d ON d.month_id=m.month_id
JOIN history h ON h.series_id=m.series_id AND h.market_id=m.market_id CROSS JOIN analysis_settings s
WHERE c.is_food=1 AND (m.month_id>=s.risk_start_id OR (c.is_staple=1 AND h.months>=s.min_long_months))
ORDER BY c.series_id,m.market_id,d.month_id;

-- name: 03_volatility
-- Business question: Which comparable food series has higher relative volatility?
-- How to read: Population CV over identical trailing-12-month fixed market panels. Entire window must be 2024 onward. Thin panels must be disclosed.
WITH stats AS (
 SELECT series_id,COUNT(*) AS months,MIN(market_count) AS markets,AVG(avg_price) AS mean_price,
 AVG(avg_price*avg_price)-AVG(avg_price)*AVG(avg_price) AS variance
 FROM v_risk_monthly GROUP BY series_id
)
SELECT c.series_id,c.commodity,c.unit,c.pricetype,d.month AS as_of,s.months,s.markets,s.mean_price,
 SQRT(CASE WHEN variance<0 THEN 0 ELSE variance END)/NULLIF(mean_price,0) AS cv
FROM stats s JOIN dim_commodity c ON c.series_id=s.series_id CROSS JOIN analysis_settings a
JOIN dim_date d ON d.month_id=a.analysis_month_id WHERE s.months=12 ORDER BY cv DESC;

-- name: 04_changes
-- Business question: How much did prices change for the same markets?
-- How to read: MoM and YoY each use their own matched endpoint panel. YoY also needs 12 observed months for each market-series. Counts and flag transitions are explicit.
WITH paired AS (
 SELECT x.*,CASE WHEN x.year_ago_price IS NOT NULL AND x.history_months>=12 THEN 1 ELSE 0 END AS yoy_ok
 FROM v_market_changes x WHERE x.price IS NOT NULL
), grouped AS (
 SELECT series_id,month_id,COUNT(*) AS observed_markets,
 SUM(CASE WHEN previous_price IS NOT NULL THEN 1 ELSE 0 END) AS mom_markets,
 AVG(CASE WHEN previous_price IS NOT NULL THEN price END) AS mom_current_price,
 AVG(previous_price) AS previous_price,
 SUM(yoy_ok) AS yoy_markets,
 AVG(CASE WHEN yoy_ok=1 THEN price END) AS yoy_current_price,
 AVG(CASE WHEN yoy_ok=1 THEN year_ago_price END) AS year_ago_price,
 SUM(CASE WHEN previous_price IS NOT NULL AND (aggregate_rows<>previous_aggregate_rows OR mixed_rows<>previous_mixed_rows) THEN 1 ELSE 0 END) AS mom_flag_transitions,
 SUM(CASE WHEN yoy_ok=1 AND (aggregate_rows<>year_ago_aggregate_rows OR mixed_rows<>year_ago_mixed_rows) THEN 1 ELSE 0 END) AS yoy_flag_transitions
 FROM paired GROUP BY series_id,month_id
)
SELECT c.series_id,c.commodity,c.unit,c.pricetype,d.month,g.month_id,g.observed_markets,
 g.mom_markets,g.mom_current_price,g.previous_price,
 100.0*(g.mom_current_price/g.previous_price-1) AS mom_pct,
 g.yoy_markets,g.yoy_current_price,g.year_ago_price,
 100.0*(g.yoy_current_price/g.year_ago_price-1) AS yoy_pct,
 g.mom_flag_transitions,g.yoy_flag_transitions
FROM grouped g JOIN dim_commodity c ON c.series_id=g.series_id
JOIN dim_date d ON d.month_id=g.month_id CROSS JOIN analysis_settings s
WHERE c.is_food=1 AND g.month_id>=s.risk_start_id ORDER BY c.series_id,g.month_id;

-- name: 05_since_2022
-- Business question: How do core staples compare with 2022 in the same markets?
-- How to read: Each 2022 market baseline is compared only with that same market at the analysis month. Report baseline completeness and aggregate-source share.
WITH baseline AS (
 SELECT m.series_id,m.market_id,AVG(m.price) AS baseline_price,COUNT(*) AS baseline_months,
 SUM(m.aggregate_rows) AS aggregate_rows,SUM(m.observations) AS observations
 FROM v_market_month m JOIN dim_date d ON d.month_id=m.month_id
 WHERE d.year=2022 GROUP BY m.series_id,m.market_id
), matched AS (
 SELECT m.series_id,COUNT(*) AS matched_markets,AVG(b.baseline_price) AS baseline_2022,
 AVG(m.price) AS current_price,MIN(b.baseline_months) AS min_baseline_months,
 MAX(b.baseline_months) AS max_baseline_months,
 100.0*SUM(b.aggregate_rows)/SUM(b.observations) AS baseline_aggregate_pct
 FROM v_market_month m JOIN baseline b ON b.series_id=m.series_id AND b.market_id=m.market_id
 CROSS JOIN analysis_settings a WHERE m.month_id=a.analysis_month_id GROUP BY m.series_id
)
SELECT c.series_id,c.commodity,c.unit,c.pricetype,d.month,
 p.matched_markets,p.baseline_2022,p.current_price,p.min_baseline_months,p.max_baseline_months,
 p.baseline_aggregate_pct,100.0*(p.current_price/p.baseline_2022-1) AS change_pct
FROM dim_commodity c CROSS JOIN analysis_settings a JOIN dim_date d ON d.month_id=a.analysis_month_id
LEFT JOIN matched p ON p.series_id=c.series_id WHERE c.is_food=1 AND c.is_staple=1 ORDER BY change_pct DESC;

-- name: 06_division_comparison
-- Business question: Which divisions are expensive for the same series at the analysis month?
-- How to read: Cross-sectional observed-market averages only. No overall cheapest division or temporal inference from these means.
SELECT c.series_id,c.commodity,c.unit,c.pricetype,d.month,d.month_id,k.division,
 AVG(m.price) AS avg_price,COUNT(*) AS markets,AVG(m.price)/n.avg_price AS national_price_ratio,
 SUM(m.aggregate_rows) AS aggregate_rows,SUM(m.mixed_rows) AS mixed_rows
FROM v_market_month m JOIN dim_market k ON k.market_id=m.market_id
JOIN dim_commodity c ON c.series_id=m.series_id JOIN dim_date d ON d.month_id=m.month_id
JOIN v_monthly n ON n.series_id=m.series_id AND n.month_id=m.month_id CROSS JOIN analysis_settings a
WHERE c.is_food=1 AND m.month_id=a.analysis_month_id
GROUP BY c.series_id,c.commodity,c.unit,c.pricetype,d.month,d.month_id,k.division,n.avg_price
ORDER BY c.series_id,k.division;

-- name: 07_seasonality
-- Business question: Which months are relatively expensive within complete years?
-- How to read: Select fixed markets complete in all 12 months of each year, then normalize annual means. Yearly panels can differ. Ramadan shifts each year.
WITH members AS (
 SELECT m.series_id,m.market_id,d.year FROM v_market_month m JOIN dim_date d ON d.month_id=m.month_id
 JOIN dim_commodity c ON c.series_id=m.series_id CROSS JOIN analysis_settings a
 WHERE c.is_food=1 AND m.month_id<=a.analysis_month_id AND (d.year>=2024 OR c.is_staple=1)
 GROUP BY m.series_id,m.market_id,d.year HAVING COUNT(*)=12
), panel_month AS (
 SELECT m.series_id,d.year,d.month_number,AVG(m.price) AS price,COUNT(*) AS markets
 FROM v_market_month m JOIN dim_date d ON d.month_id=m.month_id
 JOIN members r ON r.series_id=m.series_id AND r.market_id=m.market_id AND r.year=d.year
 GROUP BY m.series_id,d.year,d.month_number
), annual AS (
 SELECT series_id,year,AVG(price) AS mean_price FROM panel_month GROUP BY series_id,year
)
SELECT c.series_id,c.commodity,c.unit,c.pricetype,p.month_number,
 AVG(100.0*p.price/a.mean_price) AS seasonality_index,COUNT(*) AS complete_years,MIN(p.year) AS first_year,MAX(p.year) AS last_year,MIN(p.markets) AS min_year_panel_markets
FROM panel_month p JOIN annual a ON a.series_id=p.series_id AND a.year=p.year
JOIN dim_commodity c ON c.series_id=p.series_id
GROUP BY c.series_id,c.commodity,c.unit,c.pricetype,p.month_number ORDER BY c.series_id,p.month_number;

-- name: 08_market_spread
-- Business question: Where is the widest price range at the analysis month?
-- How to read: Cross-sectional same-series spread, not guaranteed sourcing profit.
SELECT c.series_id,c.commodity,c.unit,c.pricetype,d.month,COUNT(*) AS markets,
 MIN(m.price) AS cheapest_price,MAX(m.price) AS highest_price,MAX(m.price)-MIN(m.price) AS spread_bdt,
 100.0*(MAX(m.price)/MIN(m.price)-1) AS spread_pct
FROM v_market_month m JOIN dim_commodity c ON c.series_id=m.series_id
JOIN dim_date d ON d.month_id=m.month_id CROSS JOIN analysis_settings a
WHERE c.is_food=1 AND m.month_id=a.analysis_month_id
GROUP BY c.series_id,c.commodity,c.unit,c.pricetype,d.month HAVING COUNT(*)>=2 ORDER BY spread_pct DESC;

-- name: 09_rolling_average
-- Business question: What is the smoothed price in one fixed market?
-- How to read: A rolling average requires 12 consecutive calendar prices for the SAME market and series. Long history is limited to core staples with 60+ observations.
WITH history AS (SELECT series_id,market_id,COUNT(*) AS months FROM v_market_month GROUP BY series_id,market_id),
 rolling AS (
 SELECT *,COUNT(price) OVER w AS months_available,
 CASE WHEN COUNT(price) OVER w=12 THEN AVG(price) OVER w END AS rolling_12m
 FROM v_market_calendar WINDOW w AS (PARTITION BY series_id,market_id ORDER BY month_id ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)
)
SELECT c.series_id,c.commodity,c.unit,c.pricetype,x.market_id,k.market,k.division,x.month,x.price AS avg_price,
 x.months_available,x.rolling_12m
FROM rolling x JOIN dim_commodity c ON c.series_id=x.series_id
JOIN dim_market k ON k.market_id=x.market_id
JOIN history h ON h.series_id=x.series_id AND h.market_id=x.market_id CROSS JOIN analysis_settings a
WHERE c.is_food=1 AND (x.month_id>=a.risk_start_id OR (c.is_staple=1 AND h.months>=a.min_long_months))
ORDER BY c.series_id,x.market_id,x.month_id;

-- name: 10_division_rank
-- Business question: Which divisions rank highest and lowest at the common analysis month?
-- How to read: Ranks are within commodity-unit-price type. One division alone yields both rank 1 and is not evidence of a regional difference.
WITH regional AS (
 SELECT m.series_id,m.month_id,k.division,AVG(m.price) AS avg_price,COUNT(*) AS markets
 FROM v_market_month m JOIN dim_market k ON k.market_id=m.market_id CROSS JOIN analysis_settings a
 WHERE m.month_id=a.analysis_month_id GROUP BY m.series_id,m.month_id,k.division
)
SELECT c.series_id,c.commodity,c.unit,c.pricetype,d.month,r.division,r.avg_price,r.markets,
 RANK() OVER(PARTITION BY r.series_id ORDER BY r.avg_price DESC) AS expensive_rank,
 DENSE_RANK() OVER(PARTITION BY r.series_id ORDER BY r.avg_price) AS cheap_rank
FROM regional r JOIN dim_commodity c ON c.series_id=r.series_id JOIN dim_date d ON d.month_id=r.month_id
WHERE c.is_food=1 ORDER BY c.series_id,expensive_rank;

-- name: 11_risk_score
-- Business question: Which food series can be ranked on a fixed recent panel?
-- How to read: Only markets complete for the same trailing 12 months, entirely in 2024 onward. Small panels are weak evidence. Latest source month may differ from analysis month.
WITH stats AS (
 SELECT series_id,COUNT(*) AS months_available,MIN(market_count) AS market_count,
 AVG(avg_price) AS mean_price,AVG(avg_price*avg_price)-AVG(avg_price)*AVG(avg_price) AS variance,
 SUM(aggregate_rows) AS aggregate_rows,SUM(mixed_rows) AS mixed_rows,SUM(flagged) AS flagged
 FROM v_risk_monthly GROUP BY series_id
), metrics AS (
 SELECT s.*,SQRT(CASE WHEN variance<0 THEN 0 ELSE variance END)/NULLIF(mean_price,0) AS cv,
 n.avg_price,p.avg_price AS previous_price,n.avg_price/p.avg_price-1 AS mom_fraction
 FROM stats s CROSS JOIN analysis_settings a
 JOIN v_risk_monthly n ON n.series_id=s.series_id AND n.month_id=a.analysis_month_id
 JOIN v_risk_monthly p ON p.series_id=s.series_id AND p.month_id=a.analysis_month_id-1
), components AS (
 SELECT *,CASE WHEN cv/:cv_cap>1 THEN 1 ELSE cv/:cv_cap END AS v,
 CASE WHEN mom_fraction<0 THEN 0 WHEN mom_fraction/:change_cap>1 THEN 1 ELSE mom_fraction/:change_cap END AS change_component
 FROM metrics
)
SELECT c.series_id,c.commodity,c.unit,c.pricetype,d.month,x.avg_price,x.market_count,
 n.market_count AS available_markets,x.months_available,x.cv,100.0*x.mom_fraction AS mom_pct,
 CASE WHEN x.months_available=12 THEN 100.0*(:vol_weight*x.v+(1.0-:vol_weight)*x.change_component) END AS risk_score,
 x.aggregate_rows,x.mixed_rows,x.flagged,
 CASE WHEN n.avg_price IS NULL THEN 'no observation at analysis month'
 WHEN x.months_available IS NULL THEN 'no complete 12-month market panel since 2024'
 WHEN x.market_count<3 THEN 'eligible - thin panel (fewer than 3 markets)'
 ELSE 'eligible' END AS status
FROM dim_commodity c CROSS JOIN analysis_settings a JOIN dim_date d ON d.month_id=a.analysis_month_id
LEFT JOIN components x ON x.series_id=c.series_id
LEFT JOIN v_monthly n ON n.series_id=c.series_id AND n.month_id=a.analysis_month_id
WHERE c.is_food=1 ORDER BY CASE WHEN x.months_available IS NULL THEN 1 ELSE 0 END,risk_score DESC;

-- name: 12_outlier_sensitivity
-- Business question: How sensitive are snapshot prices to outliers and source flags?
-- How to read: Same selected month and same baseline markets. Exclusions can leave fewer markets: compare counts before interpreting price differences.
WITH market_variants AS (
 SELECT f.series_id,f.market_id,AVG(f.price) AS all_price,
 AVG(CASE WHEN f.outlier_flag=0 THEN f.price END) AS unflagged_price,
 AVG(CASE WHEN f.priceflag='actual' THEN f.price END) AS actual_only_price,
 SUM(f.outlier_flag) AS flagged,
 SUM(CASE WHEN f.priceflag='aggregate' THEN 1 ELSE 0 END) AS aggregate_rows,
 SUM(CASE WHEN f.priceflag='actual,aggregate' THEN 1 ELSE 0 END) AS mixed_rows
 FROM fact_prices f CROSS JOIN analysis_settings a WHERE f.month_id=a.analysis_month_id GROUP BY f.series_id,f.market_id
)
SELECT c.series_id,c.commodity,c.unit,c.pricetype,d.month,COUNT(*) AS all_markets,
 COUNT(m.unflagged_price) AS unflagged_markets,COUNT(m.actual_only_price) AS actual_only_markets,
 AVG(m.all_price) AS all_price,AVG(m.unflagged_price) AS unflagged_price,AVG(m.actual_only_price) AS actual_only_price,
 100.0*(AVG(m.all_price)/AVG(m.unflagged_price)-1) AS impact_pct,
 SUM(m.flagged) AS flagged,SUM(m.aggregate_rows) AS aggregate_rows,SUM(m.mixed_rows) AS mixed_rows
FROM market_variants m JOIN dim_commodity c ON c.series_id=m.series_id
CROSS JOIN analysis_settings a JOIN dim_date d ON d.month_id=a.analysis_month_id WHERE c.is_food=1
GROUP BY c.series_id,c.commodity,c.unit,c.pricetype,d.month ORDER BY c.series_id;
