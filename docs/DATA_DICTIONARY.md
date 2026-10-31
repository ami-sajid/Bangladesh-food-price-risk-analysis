# Data dictionary

| canonical | source_header | required | meaning |
| --- | --- | --- | --- |
| date | date | True | Source observation date; retained, then grouped by month. |
| division | admin1 | True | First administrative level; required for regional comparisons. |
| district | admin2 | False | Second administrative level; Unknown if absent. |
| market | market | True | Market label; identity also includes division and district. |
| latitude | latitude | False | Optional decimal degrees; invalid values become null. |
| longitude | longitude | False | Optional decimal degrees; invalid values become null. |
| category | category | False | Source commodity category, Unknown if unavailable. |
| commodity | commodity | True | Exact commodity/grade; never combined across units. |
| unit | unit | True | Quoted unit, retained unchanged except whitespace/case and explicit aliases. |
| priceflag | priceflag | False | Source flag, retained independently from our outlier flag. |
| pricetype | pricetype | True | Retail, wholesale or other source type; kept separate. |
| currency | currency | True | Only configured BDT aliases retained. |
| price | price | True | Positive nominal BDT per source unit; no inflation adjustment. |
| usdprice | usdprice | False | Optional source USD price; not used in BDT analysis. |
| source_market_id | market_id | False | Optional publisher market identifier, preserved and checked against market labels. |
| source_commodity_id | commodity_id | False | Optional publisher commodity identifier, preserved in clean data. |

Derived: source_row = source record position after metadata removal; month = first day; month_id = year*12+month; outlier_flag = within-series 3-IQR flag (minimum 8 observations); series_id = commodity-unit-price type key; market_id = division-district-market key. is_food = explicit category eligibility for food analyses; food_class = food/non-food/unclassified; source_flag_class = actual/aggregate/mixed/unknown source label; date_quality_flag = pre-range anomaly (true in rejected audit). Missing optional fields are not evidence that a source did not collect them.
