-- PostgreSQL DDL. Python adapts view syntax for SQLite.
-- A refresh recreates only these project-owned objects in a dedicated database.
CREATE TABLE dim_date (month_id INTEGER PRIMARY KEY, month TEXT NOT NULL UNIQUE,
 year INTEGER NOT NULL,month_number INTEGER NOT NULL);
CREATE TABLE dim_market (market_id INTEGER PRIMARY KEY,division TEXT NOT NULL,
 district TEXT NOT NULL,market TEXT NOT NULL,latitude DOUBLE PRECISION,longitude DOUBLE PRECISION,
 source_market_id TEXT,UNIQUE(division,district,market));
CREATE TABLE dim_commodity (series_id INTEGER PRIMARY KEY,commodity TEXT NOT NULL,unit TEXT NOT NULL,
 pricetype TEXT NOT NULL,category TEXT NOT NULL,is_staple INTEGER NOT NULL,is_food INTEGER NOT NULL,
 UNIQUE(commodity,unit,pricetype));
CREATE TABLE fact_prices (observation_id INTEGER PRIMARY KEY,
 month_id INTEGER NOT NULL REFERENCES dim_date(month_id),market_id INTEGER NOT NULL REFERENCES dim_market(market_id),
 series_id INTEGER NOT NULL REFERENCES dim_commodity(series_id),observation_date TEXT NOT NULL,
 price DOUBLE PRECISION NOT NULL CHECK(price>0),outlier_flag INTEGER NOT NULL CHECK(outlier_flag IN (0,1)),
 priceflag TEXT NOT NULL,source_row INTEGER NOT NULL);
CREATE TABLE analysis_settings (analysis_month_id INTEGER NOT NULL,risk_start_id INTEGER NOT NULL,
 min_risk_months INTEGER NOT NULL,min_long_months INTEGER NOT NULL);
CREATE INDEX idx_prices_series_month ON fact_prices(series_id,month_id);
CREATE INDEX idx_prices_market ON fact_prices(market_id);
CREATE INDEX idx_prices_series_market_month ON fact_prices(series_id,market_id,month_id);
CREATE OR REPLACE VIEW v_market_month AS
SELECT series_id,market_id,month_id,AVG(price) AS price,COUNT(*) AS observations,
 SUM(outlier_flag) AS flagged,
 SUM(CASE WHEN priceflag='aggregate' THEN 1 ELSE 0 END) AS aggregate_rows,
 SUM(CASE WHEN priceflag='actual,aggregate' THEN 1 ELSE 0 END) AS mixed_rows,
 SUM(CASE WHEN priceflag NOT IN ('actual','aggregate','actual,aggregate') THEN 1 ELSE 0 END) AS unknown_rows
FROM fact_prices GROUP BY series_id,market_id,month_id;
CREATE OR REPLACE VIEW v_monthly AS
SELECT series_id,month_id,AVG(price) AS avg_price,COUNT(*) AS market_count,
 SUM(observations) AS observations,SUM(flagged) AS flagged
FROM v_market_month GROUP BY series_id,month_id;
-- Dense market calendars: a missing month stays null before LAG.
CREATE OR REPLACE VIEW v_market_calendar AS
SELECT b.series_id,b.market_id,d.month_id,d.month,m.price,m.observations,m.flagged,
 m.aggregate_rows,m.mixed_rows,m.unknown_rows
FROM (SELECT series_id,market_id,MIN(month_id) AS first_id,MAX(month_id) AS last_id
 FROM v_market_month GROUP BY series_id,market_id) b
JOIN dim_date d ON d.month_id BETWEEN b.first_id AND b.last_id
LEFT JOIN v_market_month m ON m.series_id=b.series_id AND m.market_id=b.market_id AND m.month_id=d.month_id;
CREATE OR REPLACE VIEW v_market_changes AS
SELECT *,
 LAG(price) OVER w AS previous_price,LAG(price,12) OVER w AS year_ago_price,
 COUNT(price) OVER (PARTITION BY series_id,market_id ORDER BY month_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS history_months,
 LAG(aggregate_rows) OVER w AS previous_aggregate_rows,
 LAG(aggregate_rows,12) OVER w AS year_ago_aggregate_rows,
 LAG(mixed_rows) OVER w AS previous_mixed_rows,
 LAG(mixed_rows,12) OVER w AS year_ago_mixed_rows
FROM v_market_calendar WINDOW w AS (PARTITION BY series_id,market_id ORDER BY month_id);
-- The exact same markets must supply every month of the trailing risk window.
CREATE OR REPLACE VIEW v_risk_members AS
SELECT m.series_id,m.market_id
FROM v_market_month m JOIN dim_commodity c ON c.series_id=m.series_id CROSS JOIN analysis_settings s
WHERE c.is_food=1 AND m.month_id BETWEEN s.analysis_month_id-11 AND s.analysis_month_id
 AND m.month_id>=s.risk_start_id
GROUP BY m.series_id,m.market_id HAVING COUNT(*)=12;
CREATE OR REPLACE VIEW v_risk_monthly AS
SELECT m.series_id,m.month_id,AVG(m.price) AS avg_price,COUNT(*) AS market_count,
 SUM(m.observations) AS observations,SUM(m.flagged) AS flagged,
 SUM(m.aggregate_rows) AS aggregate_rows,SUM(m.mixed_rows) AS mixed_rows
FROM v_market_month m JOIN v_risk_members r ON r.series_id=m.series_id AND r.market_id=m.market_id
CROSS JOIN analysis_settings s
WHERE m.month_id BETWEEN s.analysis_month_id-11 AND s.analysis_month_id
GROUP BY m.series_id,m.month_id;
