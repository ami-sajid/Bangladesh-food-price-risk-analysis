# Source profile

{
  "metadata": {
    "source": "wfp_food_prices_bgd.csv",
    "hxl_rows_skipped": 0,
    "headers": [
      "date",
      "admin1",
      "admin2",
      "market",
      "market_id",
      "latitude",
      "longitude",
      "category",
      "commodity",
      "commodity_id",
      "unit",
      "priceflag",
      "pricetype",
      "currency",
      "price",
      "usdprice"
    ],
    "sha256": "b003cd22f0884c47d7b8c4527041ede4920b59da4dc0d1e4b31b10be4dd03765"
  },
  "rows": 34491,
  "columns": 16,
  "raw_exact_duplicates": 0,
  "valid_date_min": "1900-08-15 00:00:00",
  "valid_date_max": "2026-09-15 00:00:00",
  "invalid_dates": 0,
  "market_name_count": 124,
  "commodity_count": 73
}

| field | loaded_dtype | inferred_dtype | null_count | null_percent |
| --- | --- | --- | --- | --- |
| date | object | string | 0 | 0.00 |
| division | object | string | 0 | 0.00 |
| district | object | string | 0 | 0.00 |
| market | object | string | 0 | 0.00 |
| source_market_id | object | string | 0 | 0.00 |
| latitude | object | string | 0 | 0.00 |
| longitude | object | string | 0 | 0.00 |
| category | object | string | 0 | 0.00 |
| commodity | object | string | 0 | 0.00 |
| source_commodity_id | object | string | 0 | 0.00 |
| unit | object | string | 0 | 0.00 |
| priceflag | object | string | 0 | 0.00 |
| pricetype | object | string | 0 | 0.00 |
| currency | object | string | 0 | 0.00 |
| price | object | string | 0 | 0.00 |
| usdprice | object | string | 0 | 0.00 |

## unit

| unit | rows |
| --- | --- |
| KG | 24777 |
| L | 6314 |
| 1 piece | 2242 |
| 100 KG | 867 |
| 500 G | 74 |
| 12 KG | 74 |
| 1 Roll | 74 |
| 10 pcs | 69 |

## currency

| currency | rows |
| --- | --- |
| BDT | 34491 |

## pricetype

| pricetype | rows |
| --- | --- |
| Retail | 33624 |
| Wholesale | 867 |

## priceflag

| priceflag | rows |
| --- | --- |
| actual | 25283 |
| aggregate | 9205 |
| actual,aggregate | 3 |