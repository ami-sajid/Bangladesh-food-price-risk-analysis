# Methodology — revised for the supplied WFP dataset

## Scope and business use
Investigate where food prices warrant supplier-quote checks, inventory review and closer monitoring. This is descriptive nominal BDT analysis, not official food CPI, a forecast or proven savings. The code never invents a value for an unavailable comparison.

The uploaded CSV remains byte-for-byte intact in data/raw. Cleaning keeps valid non-food records for audit but excludes them from food analyses. Categories listed in FOOD_CATEGORIES are eligible; `non-food` and unknown categories are not. Edit classifications in config.py deliberately if a future source changes its vocabulary. Dates before MIN_VALID_DATE (1998-01-01 for this release) are flagged and quarantined. The reported 1900 petrol record is not silently moved to a guessed year.

## Identity, types and cleaning
A source observation is the fact-table grain. Commodity + unit + price type defines a series. No conversion or pooling across KG, 100 KG, L, pieces or other source units occurs. Retail and wholesale remain separate. Category is descriptive, but if a series contains a non-food classification, the dimension conservatively marks it ineligible.

Market identity is division + district + market label. Optional publisher IDs are preserved. The loader blocks two publisher market IDs that share one label identity, rather than merging them silently. The uploaded release passes this check. A changed label for one publisher ID would still need manual review; source IDs are audit fields, not an undocumented fuzzy name-matching rule.

All source header names are in COLUMN_MAP. Missing optional columns become null. Header whitespace/case is normalized; HXL metadata rows are detected if present. Source text is read as strings before validation. Prices must be finite and positive; required date/currency/identity fields cannot be missing. Only recognized BDT aliases survive. Ambiguous slash dates require DATE_FORMAT. No price imputation occurs.

Exact normalized duplicates are removed. Optional district/category/source flags become unknown, coordinates outside valid ranges become null. Every change is counted, and rejected rows have a reason in data/processed/rejected_rows.csv. The outlier rule is 3×IQR within market/commodity/unit/type with at least eight records. Zero-IQR groups are unflagged. Flags are retained in all primary calculations: unusual prices may be real events. Query 12 reports exclusion sensitivity.

## Source price flags
`actual`, `aggregate` and `actual,aggregate` are preserved exactly after whitespace/case normalization. A mixed-flag row remains ONE observation; it is not split or counted twice. Unknown source flags are visible in the profile. We do not claim to know how the publisher constructed each aggregate from the CSV alone.

Primary analysis retains these source records and exports counts. Query 04 counts actual/aggregate/mixed transitions between compared endpoints. Query 12 shows actual-only and outlier-excluded snapshot prices with surviving market counts. Source flag mix over time appears in source_flags_by_year.csv. A matched geographic panel does not correct a change from aggregate to actual measurement. In particular, the 2022 baseline uses source aggregate records in this release, so its comparisons require that caveat.

## Latest source month versus comparison month
The file's final date is not assumed to represent a complete release. The loader examines the latest twelve calendar months of food retail observations (food of other price types only if no retail exists). It chooses the newest month meeting BOTH:

1. Distinct series count at least COVERAGE_FRACTION × maximum series count in that trailing window.
2. Distinct market count at least COVERAGE_FRACTION × maximum market count in that trailing window.

COVERAGE_FRACTION defaults to 0.50. This is an explicit coverage heuristic, not a statistical guarantee or an official completeness flag. analysis_month_selection.csv discloses every candidate and its counts. analysis_metadata.csv/json records the source horizon, chosen comparison date and rule. ANALYSIS_MONTH can explicitly override the choice, but its selection must be disclosed. No records after the comparison month are deleted: market trends and coverage retain them for inspection. Rankings, regional snapshots and baseline comparisons use the selected date.

## Three kinds of comparison — never confuse them
| Output | Market rule | Valid interpretation |
|---|---|---|
| Market trend / rolling average | One selected market and one series | Same-market history; missing months are gaps |
| MoM / YoY / 2022 baseline | Same market IDs in the two compared periods | Ratio of equal-weight matched-market means for that comparison |
| Risk / volatility | Identical market IDs in every month of one trailing 12-month window | Relative price instability and latest increase within that fixed panel |

There is no temporal comparison of unrestricted all-market averages. v_monthly exists only to compute cross-sectional observed-market ratios and counts. Regional prices and market spread are snapshots of one series, one unit, one price type and one shared month. There is no universal cheapest division across unlike commodities.

## Calendar changes and the history gate
Dense monthly calendars are built separately for each market-series, between its first and last observations. LAG(1) and LAG(12) therefore refer to one and twelve calendar months ago, including missing rows. No gap is treated as a zero price.

MoM: select markets with valid current AND previous-month prices. Average both endpoint prices over those same markets, then compute 100×(current mean / previous mean − 1).

YoY: select markets with valid current AND same-month-last-year prices AND at least twelve nonmissing monthly observations through the current date. Average endpoints over this same set, then compute 100×(current mean / year-ago mean − 1). The twelve-observation gate is cumulative, not a requirement for twelve consecutive months; the risk score uses the stricter consecutive rule. A market with only the two endpoints does not qualify for YoY.

MoM and YoY panels can differ. `mom_markets`, `yoy_markets`, their separate endpoint means and flag-transition counts make that explicit. Panels can also change from one comparison date to the next. Do not compound these pairwise changes and call the result a fixed-panel multi-year index. For multi-year level lines, choose one fixed market using query 02/09.

## Long history, baseline and seasonality
Market trends before 2024 are exported only for configured core staples (rice, wheat flour, specified edible oils and lentils) with at least MIN_LONG_HISTORY_MONTHS=60 observations for that exact market-series. The test is eligibility for a descriptive long-run line, not proof of gap-free coverage. All other series are restricted to 2024 onward. Exact grades/units remain separate even inside the same staple family.

For 2022 comparison, first compute each market's average of available 2022 months. Match only markets observed again at the shared comparison month. Average those market baselines and their matched current prices with equal market weights. Report matched market count, min/max baseline months, and baseline aggregate-source percentage. A missing baseline is null. This baseline comparison does not substitute one market for another.

Seasonality first selects markets complete in all twelve months of a year, uses that fixed cohort for the year's monthly means, and normalizes each month by its year's mean (100 = average). It then averages those indices by calendar month. Yearly cohorts may differ; this is descriptive seasonality, not a fixed-panel cross-year price-level comparison. Pre-2024 seasonality is limited to configured core staples. Ramadan shifts between calendar months and requires separate dated indicators for a festival-effect analysis.

A rolling mean uses one fixed market-series and returns a value only for twelve consecutive calendar observations. Market spread uses at least two markets in the same snapshot series: max−min BDT and 100×(max/min−1). Neither a price gap nor a high score establishes an actionable margin without quality, logistics and supplier checks.

## Risk definition and geographical limitation
Only food series whose full trailing twelve-month window lies on or after RISK_START=2024-01-01 can qualify. First find markets present in ALL twelve months ending at the comparison month. Average those exact markets equally in each month. No changing membership is allowed inside the risk window.

Population CV = sqrt(max(mean(price²) − mean(price)², 0)) / mean(price), applied to the twelve fixed-panel monthly means. SQL clamps tiny negative floating-point variance to zero. This measures price-level dispersion and includes trends; it is not return volatility.

- V = min(CV / VOLATILITY_CAP, 1), default cap 0.30.
- C = min(max(MoM fraction, 0) / RECENT_CHANGE_CAP, 1), default cap 0.20.
- Risk = 100 × [VOLATILITY_WEIGHT × V + (1 − VOLATILITY_WEIGHT) × C], default weight 0.60.

The score is a capped heuristic, not a probability. Different series can tie at 100; that does not establish identical economic risk. Negative changes add no upward-pressure component but may still create unsold-inventory risk outside this score. Eligible panels with fewer than three markets are labeled thin; three markets still do not imply national representation. market_count and available_markets disclose how much evidence survives the strict window.

risk_panel_members.csv names every included market; risk_fixed_panel_monthly.csv exposes the monthly means used for CV. Read their geography before interpreting rankings. For the supplied run, the geography is computed into FINDINGS.md and the risk chart title, rather than hardcoded into future runs. Ineligible series receive null, not a reassuring zero.

## Database and reproducibility
Four star tables contain the facts and dimensions; analysis_settings is a one-row run-configuration table used by views. A refresh recreates only the named project objects inside the dedicated database. PostgreSQL DDL is transactional. SQLite is the runnable fallback, with foreign keys and SQRT enabled. No DROP CASCADE is used, so unrelated dependent objects block a refresh rather than being removed.

Always use a dedicated database. Existing manually added changes inside project-owned tables are overwritten on refresh. The fact count is reconciled with cleaned rows; verification queries check broken references, invalid prices and coverage. All twelve analyses execute through SQLAlchemy and export CSVs. Credentials stay in .env and never appear in reports. Failed runs may leave earlier exports: only trust status=success in outputs/run_status.json.

In pgAdmin, execute individual named analysis blocks after the pipeline loads the schema. For query 11 replace :cv_cap, :change_cap and :vol_weight with values from config.py (defaults 0.30, 0.20, 0.60); Python binds them automatically. Review independent validation and platform limits in docs/VALIDATION.md.
