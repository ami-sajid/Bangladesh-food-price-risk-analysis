-- Fact rows must equal data/processed/prices_clean.csv data rows.
SELECT COUNT(*) AS fact_rows FROM fact_prices;
-- Must be zero: broken references.
SELECT COUNT(*) AS orphan_rows FROM fact_prices f
LEFT JOIN dim_date d ON d.month_id=f.month_id
LEFT JOIN dim_market m ON m.market_id=f.market_id
LEFT JOIN dim_commodity c ON c.series_id=f.series_id
WHERE d.month_id IS NULL OR m.market_id IS NULL OR c.series_id IS NULL;
-- Must be zero: invalid prices.
SELECT COUNT(*) AS invalid_prices FROM fact_prices WHERE price<=0 OR price IS NULL;
-- Review coverage, repeated dates need not be duplicates.
SELECT series_id,COUNT(*) AS observations,COUNT(DISTINCT market_id) AS markets
FROM fact_prices GROUP BY series_id;
