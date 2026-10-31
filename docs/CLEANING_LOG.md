# Cleaning log

```json
{
  "rows_before": 34491,
  "rows_after": 34490,
  "events": [
    {
      "action": "Normalize division",
      "rows": 34491,
      "reason": "Whitespace/case; explicit aliases only"
    },
    {
      "action": "Normalize district",
      "rows": 34491,
      "reason": "Whitespace/case; explicit aliases only"
    },
    {
      "action": "Normalize market",
      "rows": 34491,
      "reason": "Whitespace/case; explicit aliases only"
    },
    {
      "action": "Normalize category",
      "rows": 0,
      "reason": "Whitespace/case; explicit aliases only"
    },
    {
      "action": "Normalize commodity",
      "rows": 34491,
      "reason": "Whitespace/case; explicit aliases only"
    },
    {
      "action": "Normalize unit",
      "rows": 32180,
      "reason": "Whitespace/case; explicit aliases only"
    },
    {
      "action": "Normalize priceflag",
      "rows": 0,
      "reason": "Whitespace/case; explicit aliases only"
    },
    {
      "action": "Normalize pricetype",
      "rows": 34491,
      "reason": "Whitespace/case; explicit aliases only"
    },
    {
      "action": "Normalize currency",
      "rows": 34491,
      "reason": "Whitespace/case; explicit aliases only"
    },
    {
      "action": "Null invalid latitude",
      "rows": 0,
      "reason": "Optional field; never impute coordinates or USD values"
    },
    {
      "action": "Null invalid longitude",
      "rows": 0,
      "reason": "Optional field; never impute coordinates or USD values"
    },
    {
      "action": "Null invalid usdprice",
      "rows": 0,
      "reason": "Optional field; never impute coordinates or USD values"
    },
    {
      "action": "Remove",
      "rows": 0,
      "reason": "Currency missing or not recognized as BDT"
    },
    {
      "action": "Remove",
      "rows": 0,
      "reason": "Invalid or missing date"
    },
    {
      "action": "Remove",
      "rows": 1,
      "reason": "Date before configured source-valid range; flagged and quarantined"
    },
    {
      "action": "Remove",
      "rows": 0,
      "reason": "Price must be finite and positive"
    },
    {
      "action": "Remove",
      "rows": 0,
      "reason": "Missing comparison identity"
    },
    {
      "action": "Fill district",
      "rows": 0,
      "reason": "Optional descriptive field becomes unknown"
    },
    {
      "action": "Fill category",
      "rows": 0,
      "reason": "Optional descriptive field becomes unknown"
    },
    {
      "action": "Fill priceflag",
      "rows": 0,
      "reason": "Optional descriptive field becomes unknown"
    },
    {
      "action": "Remove",
      "rows": 0,
      "reason": "Exact normalized record duplicate"
    },
    {
      "action": "Exclude from food analyses",
      "rows": 842,
      "reason": "Keep non-food/unclassified records in clean data and coverage audits"
    },
    {
      "action": "Flag outliers",
      "rows": 240,
      "reason": "Retained; 3-IQR within market/commodity/unit/type, minimum 8 records; zero IQR unflagged"
    }
  ]
}
```
