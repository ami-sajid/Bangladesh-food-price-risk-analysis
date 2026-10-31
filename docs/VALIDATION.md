# Validation record — real-data revision

Validated on 2026-10-26 using Python 3.12.14 on Linux.

## Completed checks

- 14 pytest cases passed, including two isolated full-pipeline runs with synthetic data. Synthetic values are only test fixtures, never portfolio findings.
- Complete SQLite pipeline executed on the supplied WFP CSV: profiling, cleaning, constrained database loading, all twelve SQL analyses, independent reconciliation, six charts and automatic report generation.
- Retained 34,490 records, including 33,648 food records; quarantined 1 invalid-date record. Raw file is byte-for-byte identical to the supplied upload.
- Independently recalculated all 1,112 exported matched MoM/YoY rows using pandas endpoint joins rather than SQL LAG. Verified percentages, matched counts and the YoY history gate.
- Independently reconstructed all 128 risk-panel memberships and recalculated all 43 eligible CV/change/risk scores. Values matched SQL within numeric tolerances.
- Regression tests confirm that a newly appearing expensive market cannot manufacture inflation, sparse annual endpoints fail the YoY history gate, and risk windows cannot include pre-2024 months.
- Repeated database loading does not duplicate observations. Fact counts, foreign-key orphans and invalid prices are checked.
- Six chart layouts reviewed; charts state their units, dates and geographic scope.

## Dashboard check

The HTML dashboard was generated from `outputs/tables` and rendered in headless Chromium (no console errors); its numbers come straight from the validated tables. It was not built or tested in Power BI or Looker Studio.

## Platform limits

Live PostgreSQL, Windows batch execution, Power BI Desktop and an authenticated Looker Studio session were unavailable here. Those platform executions are not claimed. PostgreSQL schema syntax and SQLite adaptation were reviewed; the provided dashboard guides include manual reconciliation checks. No PBIX or online dashboard is represented as already built.

## How to reproduce

Run `python -m pytest -q` from the project root. Run `python run_all.py` to regenerate the real-data exports. The full pipeline calls scripts/validate_outputs.py automatically; it can also be rerun alone with `python -m scripts.validate_outputs`. Results are recorded in outputs/independent_validation.json and run_status.json.

## Package versions used

- pandas: 2.2.3
- SQLAlchemy: 2.1.6
- psycopg2-binary: 2.9.13
- matplotlib: 3.10.8
- python-dotenv: 1.2.4
- pytest: 8.4.2
